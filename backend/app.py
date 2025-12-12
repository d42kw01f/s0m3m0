from flask import Flask, request, jsonify, Response
import subprocess
import json

app = Flask(__name__)


@app.route('/api/fb_page', methods=['POST'])
def scrape_page() -> tuple[Response, int]:
    """
    Endpoint to scrape a Facebook page.

    Expects 'url' and 'untilDate' in the POST request body.
    """
    data = request.json
    url: str = data.get('url')
    until_date: str = data.get('untilDate')

    if not url or not until_date:
        return jsonify({"error": "Missing 'url' or 'untilDate' parameter"}), 400

    # Call the scraper script with the provided parameters
    result = subprocess.run(
        ['node', '../scrapers/dist/facebook_PageScraper.js', url, until_date],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    if result.returncode != 0:
        return jsonify({"error": "Scraping failed", "details": result.stderr}), 500

    return jsonify({"message": "Scraping started successfully", "details": result.stdout}), 200


@app.route('/api/fb_hashtag', methods=['POST'])
def scrape_hashtag() -> tuple[Response, int]:
    """
    Endpoint to scrape Facebook posts based on a hashtag.

    Expects 'url' and 'maxPosts' in the POST request body.
    """
    app.logger.debug("scrape_hashtag endpoint hit")
    data = request.json
    url: str = data.get('url')
    max_posts: str = data.get('maxPosts')

    if not url or not max_posts:
        return jsonify({"error": "Missing 'url' or 'maxPosts' parameter"}), 400

    # Call the scraper script with the provided parameters
    result = subprocess.run(
        ['node', '../scrapers/dist/facebook_HashtagScraper.js', url, max_posts],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    if result.returncode != 0:
        return jsonify({"error": "Scraping failed", "details": result.stderr}), 500

    return jsonify({"message": "Scraping started successfully", "details": result.stdout}), 200


@app.route('/api/fb_post', methods=['POST'])
def scrape_post() -> tuple[Response, int]:
    """
    Endpoint to scrape a single Facebook post.

    Expects a JSON object containing post details in the POST request body.
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Serialize the JSON object to a string
    political_post_json: str = json.dumps(data)

    # Call the scraper script with the JSON string as a parameter
    result = subprocess.run(
        ['node', '../scrapers/dist/facebook_SinglePostScraper.js', political_post_json],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    if result.returncode != 0:
        return jsonify({"error": "Scraping failed", "details": result.stderr}), 500

    return jsonify({"message": "Scraping started successfully", "details": result.stdout}), 200


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
