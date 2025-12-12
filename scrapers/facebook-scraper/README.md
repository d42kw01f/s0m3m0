# S0M3M0
This project is a TypeScript-based web scraping tool that uses Puppeteer to scrape data from a Facebook page, processes the data, and saves it to JSON files. The project also includes capabilities to take screenshots of the page.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The Facebook Page Data Scraper automates the process of browsing a Facebook page, scrolling through posts, and extracting useful data such as post text, reactions, comments, shares, and dates. It then saves this data into a JSON file and takes a screenshot of the page.

## Features

- **Automated Browser Control**: Uses Puppeteer to control a headless browser.
- **Data Extraction**: Scrapes post data from a specified Facebook page.
- **Data Saving**: Saves the extracted data to JSON files.
- **Screenshot Capture**: Takes screenshots of the Facebook page.
- **Error Handling**: Includes robust error handling and logging.

## Requirements

- Node.js (version 14 or later)
- npm (version 6 or later)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/facebook-page-data-scraper.git
   cd facebook-page-data-scraper
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   COOKIE_PATH=./secrets/cookies.json
   ```

## Usage

1. **Prepare Cookies**:
   - Log in to Facebook using a browser and save the cookies to a file (e.g., `cookies.json` in the `secrets` directory).

2. **Run the Scraper**:
   ```bash
   npm run build
   npm start
   ```

3. **Check Output**:
   - JSON files and screenshots will be saved in the `output` directory.

## Project Structure

```
facebook-page-data-scraper/
├── README.md
├── dist/
│   ├── browserAutomation.js
│   ├── facebookDataScraper.js
│   ├── index.js
│   ├── old_fb_scraper.js
│   └── postLastDate.js
├── output/
│   └── screenshots/
├── package-lock.json
├── package.json
├── secrets/
│   └── cookies.json
├── src/
│   ├── services/
│   │   ├── browserAutomation.ts
│   │   ├── fbPageScraper.ts
│   ├── utils/
│   │   ├── getLastPostDate.ts
│   ├── index.ts
│   └── old_fb_scraper.ts
├── tsconfig.json
└── .gitignore
```

- **src/**: Source code.
  - **services/**: Business logic and scraping operations.
    - `browserAutomation.ts`: Handles browser automation using Puppeteer.
    - `fbPageScraper.ts`: Extracts data from Facebook posts.
  - **utils/**: Utility functions.
    - `getLastPostDate.ts`: Determines the date of the last post.
  - `index.ts`: Main entry point of the application.
- **dist/**: Compiled JavaScript files.
- **output/**: Directory for saving JSON files and screenshots.
- **secrets/**: Directory for storing cookies.
- **tsconfig.json**: TypeScript configuration.
- **.gitignore**: Git ignore file.

## Configuration

- **Cookies**: Ensure your cookies are stored in the path specified in the `.env` file (`COOKIE_PATH`).

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.


