from datetime import datetime, timezone
import subprocess
import json
import time
import random
from typing import Any, List, Dict, Optional


class FacebookScraperProcessor:
    def __init__(self, db_client: Any, sentiment_predictor: Any, text_translator: Any) -> None:
        """
        Initializes the FacebookScraperProcessor with a database client, sentiment predictor, and text translator.

        :param db_client: Database client used to fetch and update documents.
        :param sentiment_predictor: Sentiment predictor for determining whether text is political or non-political.
        :param text_translator: Text translator for translating the post and comment texts.
        """
        self.db_client = db_client
        self.sentiment_predictor = sentiment_predictor
        self.text_translator = text_translator

    def process(self) -> None:
        """
        Processes unpredicted documents by translating text, predicting sentiment, and updating the documents.
        """
        unpredicted_docs = self.db_client.find_unpredicted_texts_docs()
        i = 0

        for doc in unpredicted_docs:
            post_text: str = doc.get("post_text", "")
            translated_text: Optional[str] = self.text_translator.translate_text(post_text) if post_text else None

            i += 1

            # Initialize final_the_poli as non-political by default
            final_the_poli: str = 'non-political'

            # Predict sentiment based on the translated post text
            if translated_text:
                sentiment: str = self.sentiment_predictor.predict(translated_text)
                if sentiment == 'political':
                    final_the_poli = 'political'
            else:
                sentiment = "non-political"

            # Process comments
            comment_data: List[Dict[str, Optional[str]]] = []
            comments: List[str] = doc.get("two_comments", [])
            if comments:
                for comment in comments:
                    translated_comment_text: Optional[str] = self.text_translator.translate_text(comment)
                    comment_sentiment: str = (
                        self.sentiment_predictor.predict(translated_comment_text)
                        if translated_comment_text else "non-political"
                    )
                    if comment_sentiment == 'political':
                        final_the_poli = 'political'

                    # Store comment data
                    comment_data.append({
                        "original_comment": comment,
                        "translated_comment": translated_comment_text,
                        "comment_sentiment": comment_sentiment
                    })

            # Prepare the fields to be updated in the document
            update_fields: Dict[str, Any] = {
                "post_text_prediction_data": {
                    "prediction": sentiment,
                    "predictedAt": datetime.now(timezone.utc).isoformat(),
                    "tr_post_text": translated_text,
                },
                "comment_prediction_data": comment_data,
                "final_the_poli": final_the_poli
            }

            # If the post is political, run the external Node.js script
            if final_the_poli == 'political':
                try:
                    print(f'\t\t> political - {doc["post_text"]}')
                    doc_json: str = json.dumps(doc, default=str)
                    print(doc_json)

                    # Sleep for a random duration between 1 and 180 seconds
                    time.sleep(random.uniform(1, 180))

                    # Run the external Node.js scraper script
                    result = subprocess.run(
                        ['node', '../scrapers/dist/facebook_SinglePostScraper.js', doc_json],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        check=True  # Raises CalledProcessError if the script fails
                    )
                except subprocess.CalledProcessError as e:
                    print(f"An error occurred while running the script: {e.stderr}")

            # Update the document in the database
            self.db_client.update_doc(doc["_id"], update_fields)
            print(f"{i}. Processed document {doc['_id']}")

        print("Translation, sentiment prediction, and update completed for unpredicted documents.")
