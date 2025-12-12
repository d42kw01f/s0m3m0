import { BrowserAutomation } from './services/browserAutomation';
import { FbScraper } from './services/fbScraper';
import { INormalPost } from "./interfaces/INormalPost";
import getRandomInt from './utils/randomNumberGenerator';
import fb_NormalPostModel from './models/MNormalPost';
import getLastPostDate from './utils/getLastPostDate';
import mongoose from 'mongoose';
import * as dotenv from 'dotenv';
import connectDB from './db';

dotenv.config();

const [,, url, untilDateStr] = process.argv;
const untilDate: Date = new Date(untilDateStr);

if (!url || isNaN(untilDate.getTime())) {
  console.error('[ERROR] Invalid or missing URL and untilDate parameters');
  process.exit(1);
}

(async () => {
  await connectDB();

  const browserAutomation : BrowserAutomation = new BrowserAutomation();
  await browserAutomation.initialize(true);

  const cookiePath: string | undefined = process.env.COOKIE_PATH;
  if (!cookiePath) {
    throw new Error('[ERROR] COOKIE_PATH is not defined in environment variables.');
  }

  await browserAutomation.loadCookies(cookiePath);
  await browserAutomation.navigateTo(url);

  let goAgain: boolean = true;
  let lastPostDate: Date | null = null;
  let postDetailsJson: INormalPost[] = [];

  try {
    do {
      await browserAutomation.scrollDown(getRandomInt(10000, 12000));
      await browserAutomation.waitForTimeout(getRandomInt(3000, 5000));

      const facebookPageDataInit: FbScraper = new FbScraper(browserAutomation.getPage()!);
      postDetailsJson = await facebookPageDataInit.fetchPageProfilePosts(0);

      lastPostDate = getLastPostDate(postDetailsJson);
      if (!lastPostDate) {
        lastPostDate = new Date(+0);
        console.log('[WARNING] No valid post dates found.');
      }

      if (lastPostDate && lastPostDate <= untilDate) {
        goAgain = false;
      }
    } while (goAgain);

    // Saving data to MongoDB
    if (postDetailsJson.length > 0) {
      await fb_NormalPostModel.insertMany(postDetailsJson);
    } else {
      console.log('[WARNING] No new posts found.');
    }

  } catch (error) {
    console.error('[ERROR] Unknown error occurred during the Page/Profile Scraping')
  } finally {
    await browserAutomation.close();
    await mongoose.disconnect();
  }
})();
