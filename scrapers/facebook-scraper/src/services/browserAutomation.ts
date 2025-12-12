import * as puppeteer from 'puppeteer';
import fs from 'fs/promises';

export class BrowserAutomation {
  private browser: puppeteer.Browser | null = null;
  private page: puppeteer.Page | null = null;

  async initialize(headless: boolean = true): Promise<void> {
    try {
      this.browser = await puppeteer.launch({ headless });
      this.page = await this.browser.newPage();
      await this.page.setUserAgent(
        'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
      );
    } catch (error) {
      console.error('Error initializing browser:', error);
    }
  }

  async loadCookies(filePath: string): Promise<void> {
    try {
      const cookiesString = await fs.readFile(filePath, 'utf-8');
      const cookies = JSON.parse(cookiesString);
      await this.page!.setCookie(...cookies);
    } catch (error) {
      console.error('Error loading cookies:', error);
    }
  }

  async navigateTo(url: string): Promise<void> {
    try {
      await this.page!.goto(url, { waitUntil: 'networkidle2' });
    } catch (error) {
      console.error('Error navigating to URL:', error);
    }
  }

  async takeScreenshot(filePath: string): Promise<void> {
    try {
      await this.page!.screenshot({ path: filePath });
    } catch (error) {
      console.error('Error taking screenshot:', error);
    }
  }

  async scrollDown(pixels: number): Promise<void> {
    try {
      await this.page!.evaluate((scrollPixels) => {
        window.scrollBy(0, scrollPixels);
      }, pixels);
    } catch (error) {
      console.error('Error scrolling down:', error);
    }
  }

  async waitForTimeout(timeout: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, timeout));
  }

  async close(): Promise<void> {
    try {
      await this.browser!.close();
    } catch (error) {
      console.error('Error closing browser:', error);
    }
  }

  getPage(): puppeteer.Page | null {
    return this.page;
  }
}
