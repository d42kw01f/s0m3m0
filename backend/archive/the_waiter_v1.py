from typing import Optional, Dict
import pytz
from dateutil import parser


def calculate_post_age(post_datetime: str, scraper_at: str) -> int:
    # Parse both dates using dateutil's parser for better flexibility with time zones
    post_date = parser.parse(post_datetime)
    scraper_at_date = parser.parse(scraper_at)

    # Ensure scraper_at_date is timezone-aware, defaulting to UTC if missing
    if scraper_at_date.tzinfo is None:
        scraper_at_date = scraper_at_date.replace(tzinfo=pytz.utc)

    # Calculate the age of the post in days
    age = (scraper_at_date - post_date).days

    return age


def time_decay_factor(age_in_days: int, half_life: int = 30) -> float:
    # Exponential decay function based on the post age
    decay = 0.5 ** (age_in_days / half_life)
    return decay


def calculate_post_engagement_score(reactions: Dict[str, int], comments: Optional[int], shares: Optional[int],
                                    post_datetime: str, scraper_at: str) -> float:
    age_in_days = calculate_post_age(post_datetime, scraper_at)
    decay = time_decay_factor(age_in_days)

    # Total engagement is the sum of all reactions, comments, and shares
    total_engagement = sum(reactions.values()) + (comments or 0) + (shares or 0)

    # Apply the decay factor
    total_score = total_engagement * decay

    return total_score


def calculate_candidate_scores(total_score: float, candidate_probabilities: Dict[str, float],
                               sentiment_score: float) -> Dict[str, float]:
    candidate_scores = {}
    for candidate, probability in candidate_probabilities.items():
        candidate_score = total_score * probability * sentiment_score
        candidate_scores[candidate] = candidate_score
    return candidate_scores


if __name__ == '__main__':
    def cal_the_weights() -> None:
        # Sample data
        comments_count = 12
        shares_count = 0
        reactions = {
            'like': 21,
            'love': 32,
            'haha': 2333,
            'angry': 22
        }
        publishedAt = 'Fri Nov 01 2024 12:34:56 GMT+0000'
        scraper_at = '2024-11-02T08:45:30.123456Z'
        post_text = "Anura Kumara Dissanayake is one of the bad leaders ever"

        # Assume these are the outputs from your AI models
        candidate_probabilities = {
            'anura': 0.8,
            'sajith': 0.1,
            'ranil': 0.05,
            'other': 0.05
        }
        sentiment_score = -0.8  # Output from your sentiment analyzer

        # Calculate the total engagement score for the post
        total_score = calculate_post_engagement_score(
            reactions,
            comments_count,
            shares_count,
            publishedAt,
            scraper_at
        )

        # Calculate the candidate scores
        candidate_scores = calculate_candidate_scores(
            total_score,
            candidate_probabilities,
            sentiment_score
        )

        print(f"Total Engagement Score: {total_score}")
        print(f"Candidate Scores: {candidate_scores}")
        print("Post weights updated successfully.")


    cal_the_weights()
