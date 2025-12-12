import {HTTPResponse, Page} from 'puppeteer';
import { INormalPost } from "../interfaces/INormalPost";
import { IPostAdd } from "../interfaces/IPostAdd";
import { getFacebookUsernameString } from "../utils/usernameFinder";
import { parseDate } from "../utils/parseDate";
import fs from 'fs';

export class FbScraper {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async fetchPageProfilePosts(fbMethod: number): Promise<INormalPost[]> {
    try {
      fbMethod === 1
        ? await this.page.waitForSelector('#BrowseResultsContainer', { timeout: 10000 })
        : await this.page.waitForSelector('#tlFeed', { timeout: 10000 });

      const parseDateString : string = parseDate.toString();

     return await this.page.evaluate(async (parseDateFunc: string, fbMethod: number, getFacebookUsernameFunc: string) => {
      const parseDate = eval(`(${parseDateFunc})`);
      const getFacebookUsername = eval(getFacebookUsernameFunc);

      let articles = fbMethod === 1
        ? Array.from(document.querySelectorAll('div._a5o._9_7._2rgt._1j-f'))
        : Array.from(document.querySelectorAll('article._56be._4hkg._5rgr._5tx9.async_like'));

      const posts = await Promise.all(articles.map(async (article) => {
        try {
          const generateUniqueId = (): number => {
            return Math.floor(Math.random() * 1000000);
          };

          const PostText = article.querySelector('div._5rgt._5nk5._3ynu._5msi')?.textContent || null;
          const PostReaction = article.querySelector('div._1g06')?.textContent || null;
          const PostComShareElement = article.querySelector('div._1fnt');
          const PostDateElement = article.querySelector('header._7om2._1o88._77kd._4gxq._5qc1 abbr');
          const contentElement = article.querySelector('div._3ynr._5rgu._7dc9._27x0');
          const URLElement = article.querySelector('a._5msj');
          const usernameElement = article.querySelector('h3._52jd._52jb._52jh._5qc3._4vc-._3rc4._4vc-')?.querySelector('a');

          const commentsSection = article.querySelector('div._333v._45kb');
          const PostCommentsList = commentsSection
              ? Array.from(commentsSection.querySelectorAll('div[data-sigil="comment-body"]')).map(comment => comment.textContent || '')
              : null;

          const postCommentsCount: string | null = PostComShareElement?.querySelector('span[data-sigil="comments-token"]')?.textContent?.split(' ')[0] || null;
          const postSharesCount: string | null = PostComShareElement?.querySelector('span:not([data-sigil="comments-token"])')?.textContent?.split(' ')[0] || null;
          const postReactionCount: string | null = PostReaction;
          const PostDate: Date | null = PostDateElement ? parseDate(PostDateElement.textContent || '') : null;

          const PostContent = contentElement
              ? Array.from(contentElement.querySelectorAll('a')).map((link) => link.getAttribute('href'))
              : null;

          const PostUrl: string | null = URLElement?.getAttribute('href') || null;
          const UsernameUrl: string | null = usernameElement?.getAttribute('href') || null;

          const uuid: string = PostUrl?.split('&id=')[0].replace('/story.php?story_fbid=', '') || generateUniqueId().toString();
          const scraperAt: string = new Date().toISOString();
          const username: string | null = getFacebookUsername(UsernameUrl || '');
          const postId: string = `fb_${username}_${Date.now()}_${uuid}`;

          return {
            postId: postId,
            scraperAt: scraperAt,
            datetime: PostDate ? PostDate.toString() : null,
            post_text: PostText,
            username: username,
            post_url: PostUrl,
            img_content: PostContent,
            num_reaction: postReactionCount,
            num_shares: postSharesCount,
            num_comments: postCommentsCount,
            two_comments: PostCommentsList,
          };
        } catch (error) {
          console.error('[ERROR] parsing article:', error);
          return null;
        }
      }));
      return posts.filter(post => post !== null) as INormalPost[];
    },parseDateString, fbMethod, getFacebookUsernameString);

    } catch (error) {
      console.error('[ERROR] fetching IPosts data:', error);
      return [];
    }
  }

  async fetchSinglePost(): Promise<IPostAdd | null> {
    try {
      await this.page.waitForSelector('div#rootcontainer');

      const addPostData: IPostAdd = await this.page.evaluate(() => {
        const fullPostText : string | null = document.querySelector('div._5rgt._5nk5._3ynu')?.textContent || null;
        const reactionUrlElement = document.querySelector('a._45m8');
        const commentElement = document.querySelector('div._333v._45kb');
        const reactionUrl : string | null = reactionUrlElement?.getAttribute('href') || null;

        const postTextElement = fullPostText ? null : document.querySelector('div.msg.mfsl');
        const innerDivText : string = postTextElement?.querySelector('div')?.textContent || '';

        const fullComments = commentElement
          ? Array.from(commentElement.querySelectorAll('div[data-sigil="comment-body"]')).map(comment => comment.textContent || '')
          : null;

        const scraperAt : string = new Date().toISOString();

        return {
          scrapeAt: scraperAt,
          full_post_text: fullPostText || innerDivText,
          full_comment: fullComments,
          reaction_url: reactionUrl
        };
      });

      if (addPostData.reaction_url) {
        let fullReactionUrl : string = addPostData.reaction_url;
        if (!fullReactionUrl.startsWith('http')) {
          fullReactionUrl = `https://facebook.com${fullReactionUrl}`;
        }

        await this.page.goto(fullReactionUrl, { waitUntil: 'networkidle2' });
        await this.page.waitForSelector('div.scrollAreaColumn');

        addPostData.reactions = await this.page.evaluate(() => {
          return Array.from(document.querySelectorAll('div.scrollAreaColumn span._10tn span[aria-label]'))
            .map(span => span.getAttribute('aria-label'));
        });
      }
      return addPostData;
    } catch (error) {
      console.error('Error fetching post data:', error);
      return {
        scrapeAt: null,
        full_post_text: null,
        full_comment: null,
        reaction_url: null,
        reactions: null,
      };
    }
  }

  async downloadImage(url: string, filePath: string): Promise<boolean> {
    try {
      await this.page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
      await this.page.waitForSelector('img[src^="https://scontent"]', { timeout: 5000 });

      const imageUrl: string | null = await this.page.evaluate(() => {
        const imgElement: HTMLImageElement = document.querySelector('img[src^="https://scontent"]') as HTMLImageElement;
        return imgElement ? imgElement.src : null;
      });

      if (imageUrl) {
        const viewSource: HTTPResponse | null = await this.page.goto(imageUrl);

        if (viewSource) {
          const buffer: Buffer = await viewSource.buffer();
          fs.writeFileSync(filePath, buffer);
          console.log('Image saved successfully:', filePath);
          return true;
        } else {
          console.log('Failed to load the image URL.');
        }
      } else {
        console.log('Image not found.');
      }
    } catch (error) {
      console.error('Error downloading image:', error);
    }
    return false;
  }

  async waitForTimeout(timeout: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, timeout));
  }
}