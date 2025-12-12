import { parseReactions } from './utils/getReactionData';
import { ISinglePost, ImgContent, IImgContentUrl } from './interfaces/ISinglePost';
import { FbScraper } from './services/fbScraper';
import { INormalPost } from './interfaces/INormalPost';
import { IPostAdd } from './interfaces/IPostAdd';
import { BrowserAutomation } from './services/browserAutomation';
import fb_PoliticalPostModel from './models/MSinglePost';
import getRandomInt from './utils/randomNumberGenerator';
import * as dotenv from 'dotenv';
import mongoose from 'mongoose';
import connectDB from './db';
import fs from 'fs';
dotenv.config();

const [, , politicalPostJson] = process.argv;

if (!politicalPostJson) {
  console.error('Invalid or missing politicalPostJson parameters');
  process.exit(1);
}

// Function to process imgContent as an array of IImgContentUrl objects
const processImgContent = (imgContentData: any): IImgContentUrl[] => {
  console.log("Raw imgContentData:", imgContentData); // Log raw data

  if (!Array.isArray(imgContentData)) {
    console.error('imgContentData should be an array');
    return [];
  }

  const processedContent = imgContentData
    .filter((content: any): boolean => content) // Check if content is an object with a 'url'
    .map((content: any) => ({
      url: content,
      downloaded: false // Default downloaded to false for new entries
    }));

  console.log("Processed imgContent:", processedContent); // Log processed content

  return processedContent;
};

(async (): Promise<void> => {
  await connectDB();

  const browserAutomation: BrowserAutomation = new BrowserAutomation();
  let politicalPost: INormalPost;

  try {
    politicalPost = JSON.parse(politicalPostJson);
  } catch (error) {
    console.error('[ERROR] Invalid JSON string provided for politicalPost:', error);
    process.exit(1);
  }

  try {
    await browserAutomation.initialize(true);

    const cookiePath: string | undefined = process.env.COOKIE_PATH;
    if (!cookiePath) {
      throw new Error('[ERROR] COOKIE_PATH is not defined in environment variables.');
    }

    if (!politicalPost.post_url) {
      console.error('[ERROR] No URL found in the given political post data.');
      process.exit(1);
    }

    // Setting up the browser with cookies
    await browserAutomation.loadCookies(cookiePath);
    const postUrl: string = `https://facebook.com${politicalPost.post_url}`;
    await browserAutomation.navigateTo(postUrl);

    await browserAutomation.waitForTimeout(getRandomInt(1000, 3000));

    const postScraper: FbScraper = new FbScraper(browserAutomation.getPage()!);
    const postDetails: IPostAdd | null = await postScraper.fetchSinglePost();

    const parsedReactions = postDetails?.reactions ? parseReactions(postDetails.reactions) : {
      like: null,
      love: null,
      haha: null,
      wow: null,
      care: null,
      sad: null,
      angry: null
    };

    // Process imgContent using the helper function
    const processedImgContent: IImgContentUrl[] = processImgContent(politicalPost.img_content || []);

    const politicalPostData: ISinglePost = {
      postId: politicalPost.postId,
      scraperAt: new Date().toISOString(),
      datetime: politicalPost.datetime || null,
      postFullText: postDetails?.full_post_text || null,
      imgContent: processedImgContent,
      numShares: politicalPost.num_shares || null,
      numComments: politicalPost.num_comments || null,
      reactions: parsedReactions,
      comments: postDetails?.full_comment || [],
      additionalContent: postDetails?.reaction_url || null
    };

    const newPoliticalPost = new fb_PoliticalPostModel(politicalPostData);
    await newPoliticalPost.save();

  } catch (error) {
    console.error('[ERROR] An error occurred during scraping:', error);
  } finally {
    await browserAutomation.close();
    await mongoose.disconnect();
  }
})();
