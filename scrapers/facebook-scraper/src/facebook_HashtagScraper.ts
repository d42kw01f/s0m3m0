import { BrowserAutomation } from './services/browserAutomation';
import { FbScraper } from './services/fbScraper';
import { INormalPost } from './interfaces/INormalPost';
import { ImgContent, IImgContentUrl } from './interfaces/ISinglePost';
import getRandomInt from './utils/randomNumberGenerator';
import fb_NormalPostModel from './models/MNormalPost';
import connectDB from './db';
import mongoose from 'mongoose';
import * as dotenv from 'dotenv';

dotenv.config();

const [, , url, maxLimitStr] = process.argv;
const maxLimit = maxLimitStr ? parseInt(maxLimitStr, 10) : 5;

if (!url || isNaN(maxLimit)) {
  console.error('[ERROR] Invalid or missing url and maxPosts parameters');
  process.exit(1);
}

// Function to process imgContent as an array of IImgContentUrl objects
const processImgContent = (imgContentData: any): ImgContent[] => {
  return imgContentData
    .filter((content: any) => content !== null)
    .map((content: any) => {
      if (typeof content === 'object' && typeof content.url === 'string') {
        return { url: content.url, downloaded: content.downloaded || false }; // Default downloaded to false
      } else {
        throw new Error('[ERROR] Invalid imgContent format');
      }
    });
};

function isValidPost(post: INormalPost): boolean {
  if (post.postId.startsWith("fb_null")) {
    return false;
  }

  const fieldsToCheck = [
    post.datetime,
    post.post_url,
    post.username
  ];

  return fieldsToCheck.some(field => field !== null);
}

(async () => {
  await connectDB();

  const browserAutomation: BrowserAutomation = new BrowserAutomation();
  await browserAutomation.initialize(false);
  const cookiePath: string | undefined = process.env.COOKIE_PATH;
  if (!cookiePath) {
    throw new Error('[ERROR] COOKIE_PATH is not defined in environment variables.');
  }
  await browserAutomation.loadCookies(cookiePath);
  await browserAutomation.navigateTo(url);

  try {
    let postDetailsJson: INormalPost[] = [];
    let goAgain: boolean = true;

    do {
      await browserAutomation.waitForTimeout(getRandomInt(3000, 5000));

      const fbScraper: FbScraper = new FbScraper(browserAutomation.getPage()!);
      postDetailsJson = await fbScraper.fetchPageProfilePosts(1);

      console.log(postDetailsJson.length);
      if (postDetailsJson.length >= maxLimit) {
        goAgain = false;
      }

      await browserAutomation.scrollDown(getRandomInt(10000, 12000));
    } while (goAgain);

    console.log(`[INFO] Final length ${postDetailsJson.length}`);
    if (postDetailsJson.length > 0) {
      const validPosts: INormalPost[] = postDetailsJson.filter(isValidPost);
      if (validPosts.length > 0) {
        for (const post of validPosts) {
          // const processedImgContent = processImgContent(post.img_content);

          await fb_NormalPostModel.updateOne(
            { postId: post.postId },
            { $set: { ...post } },
            { upsert: true }
          );
        }
      } else {
        console.log('[WARNING] No valid posts to save.');
      }
    } else {
      console.log('[WARNING] No new posts found.');
    }
  } catch (error) {
    console.error('[ERROR] Unknown error occurred during the HashTags Scraping')
  } finally {
    await browserAutomation.close();
    await mongoose.disconnect();
  }
})();
