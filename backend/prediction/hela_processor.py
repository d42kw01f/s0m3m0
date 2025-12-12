from datetime import datetime, timezone
from typing import Any, Dict
from prediction.the_waiter import analyze_posts
from prediction.the_candi import CandidatePredictor
from prediction.the_senti import calculate_sentiment_score
from prediction.translator import TextTranslator


class HelakuruScraperProcessor:
    def __init__(
            self,
            db_client: Any,
            political_predictor: Any,
            the_candi_dir: str,
            label_dict: Dict[int, str],
            tr_url: str
    ) -> None:
        self.db_client = db_client
        self.political_predictor = political_predictor
        self.candidate_predictor = CandidatePredictor(
            model_dir=the_candi_dir, label_dict=label_dict
        )
        self.the_trans = TextTranslator(tr_url)

    def process(self) -> None:
        """
        Processes unpredicted and unweighted documents by performing political prediction,
        candidate prediction, sentiment analysis, and engagement analysis.
        """
        self._process_unpredicted_documents()
        self._process_unweighted_documents()
        print("Processing of Helakuru articles completed.")

    def _process_unpredicted_documents(self) -> None:
        unprocessed_docs = self.db_client.find_unpredicted_texts_docs()

        for index, doc in enumerate(unprocessed_docs, start=1):
            article_text = doc.get("newsContentEn", "")
            if article_text == "":
                article_text = doc.get("newsTitleEn", "")
            predicted_time = datetime.now(timezone.utc).isoformat()
            update_fields: Dict[str, Any] = {
                "predictedAt": predicted_time,
                "pt_the_poli": {
                    "prediction": "non-political",
                    "final_the_poli": "non-political",
                },
            }

            if article_text:
                # Perform political prediction
                political_prediction = self.political_predictor.predict(article_text)
                update_fields["pt_the_poli"]["prediction"] = political_prediction

                if political_prediction == "political":
                    update_fields["pt_the_poli"]["final_the_poli"] = "political"

                    # Perform candidate prediction
                    candidate_score = self.candidate_predictor.predict(article_text)
                    if candidate_score is not None:
                        update_fields["pt_the_candi"] = candidate_score

                    # Perform sentiment analysis
                    sentiment_score = calculate_sentiment_score(article_text)
                    if sentiment_score is not None:
                        update_fields["pt_the_senti"] = {
                            "sentiment_score": sentiment_score,
                        }

                    # Process top comments
                    top_comments = doc.get("top_comments", [])
                    for comment in top_comments:  # Process up to 10 comments
                        comment_text = comment.get("commentText", None)
                        if comment_text:
                            tr_comment_text = self.the_trans.translate_text(comment_text)
                            if tr_comment_text is not None:
                                comment["tr_comment_text"] = tr_comment_text
                            cm_sentiment_score = calculate_sentiment_score(tr_comment_text)
                            if cm_sentiment_score is not None:
                                comment["pt_the_senti"] = {
                                    "sentiment_score": cm_sentiment_score,
                                }
                            cm_candidate_score = self.candidate_predictor.predict(tr_comment_text)
                            if cm_candidate_score is not None:
                                comment["pt_the_candi"] = cm_candidate_score

                    # Add updated comments back to the document
                    update_fields["top_comments"] = top_comments

            # Update the document in the database
            self.db_client.update_doc(doc["_id"], update_fields)
            print(f"{index}. Processed article {doc['_id']}")

    def _process_unweighted_documents(self) -> None:
        """
        Processes documents that have not yet been weighted for engagement.
        Performs engagement analysis and updates the corresponding fields in the database.
        """
        unweighted_docs = self.db_client.find_unweighted_text_docs()

        for index, doc in enumerate(unweighted_docs, start=1):
            total_candidate_weights, normalized_candidate_weights, total_field_contributions = analyze_posts([doc])

            if total_candidate_weights and normalized_candidate_weights:
                update_fields: Dict[str, Any] = {
                    "pt_the_waiter": {
                        "total_candidate_weights": total_candidate_weights,
                        "normalized_candidate_weights": normalized_candidate_weights,
                    }
                }
                self.db_client.update_doc(doc["_id"], update_fields)
                print(f"{index}. Updated weights for article {doc['_id']}")
