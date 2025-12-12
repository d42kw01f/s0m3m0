import fs from 'fs';
import mongoose from 'mongoose';
import dotenv from 'dotenv';
import { BrowserAutomation } from './services/browserAutomation';
import { FbScraper } from './services/fbScraper';
import { ISinglePost, IImgContentUrl } from './interfaces/ISinglePost';
import { IImgPoli } from "./interfaces/IImgPoli";
import fb_imgPoliModel from "./models/MImgPoli";
import connectDB from './db';

dotenv.config();

const [,, politicalImgJson] = process.argv;

if (!politicalImgJson) {
    console.error('Invalid or missing politicalImgJson parameters');
    process.exit(1);
}

async function processImagePost(politicalImgPost: ISinglePost): Promise<void> {
    if (!politicalImgPost.imgContent || !Array.isArray(politicalImgPost.imgContent)) {
        console.log('No imgContent found or imgContent is not an array for document:', politicalImgPost.postId);
        return;
    }

    const cookiePath: string | undefined = process.env.COOKIE_PATH;
    if (!cookiePath) {
      throw new Error('[ERROR] COOKIE_PATH is not defined in environment variables.');
    }

    const browserAutomation = new BrowserAutomation();
    try {
        await browserAutomation.initialize(false);
        // await browserAutomation.loadCookies(cookiePath)
        const page = browserAutomation.getPage();
        if (!page) {
            console.error('Failed to create a new page');
            return;
        }

        const scraper = new FbScraper(page);

        for (const [index, img] of politicalImgPost.imgContent.entries()) {
            const imageUrl = getImageUrl(img);
            const filePath = getFilePath(politicalImgPost.postId, index);

            try {
                await ensureDirectoryExists('./downloads');
                const downloadSuccessful = await scraper.downloadImage(imageUrl, filePath);
                if (downloadSuccessful) {
                    await saveImageRecord(politicalImgPost.postId, filePath);
                } else {
                    console.log(`Failed to download image ${index + 1} for document ${politicalImgPost.postId}`);
                }
            } catch (error) {
                console.error(`Error processing image ${index + 1} for document ${politicalImgPost.postId}:`, error);
            }
        }
    } finally {
        await browserAutomation.close();
    }
}

function getImageUrl(img: IImgContentUrl | string): string {
    return typeof img === 'string' ? `https://www.facebook.com${img}` : `https://www.facebook.com${img.url}`;
}

function getFilePath(postId: string, index: number): string {
    return `./downloads/${postId}-${index}.jpg`;
}

async function ensureDirectoryExists(dir: string): Promise<void> {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
    }
}

async function saveImageRecord(postId: string, filePath: string): Promise<void> {
    const newDocument: IImgPoli = {
        postId,
        imageFilePath: filePath,
        downloadedAt: new Date(),
    };
    const newPoliticalPost = new fb_imgPoliModel(newDocument);
    await newPoliticalPost.save();
    console.log(`Saved image record for postId ${postId}`);
}

(async () => {
    try {
        await connectDB();

        let politicalImgPost: ISinglePost;
        try {
            politicalImgPost = JSON.parse(politicalImgJson);
        } catch (error) {
            console.error('[ERROR] Invalid JSON string provided for politicalImgPost:', error);
            process.exit(1);
        }

        await processImagePost(politicalImgPost);
    } catch (error) {
        console.error('An unexpected error occurred:', error);
    } finally {
        await mongoose.disconnect();
    }
})();
