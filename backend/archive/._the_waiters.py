import datetime
import pytz
from pymongo import MongoClient
from typing import Optional, Dict

client = MongoClient('mongodb://192.168.8.167:27017/')
db = client['Helakuru']
collection = db['esana_news']


def calculate_post_age(post_datetime: str, scraper_at: str) -> int:
    # Clean post datetime to remove the timezone name
    post_datetime_cleaned = post_datetime.split(" (")[0]
    # Parse the cleaned datetime string
    post_date = datetime.datetime.strptime(post_datetime_cleaned, "%a %b %d %Y %H:%M:%S GMT%z")
    # Parse the scraper_at string and convert to a timezone-aware datetime
    scraper_at_date = datetime.datetime.strptime(scraper_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
    # Calculate the age of the post in days
    age = (scraper_at_date - post_date).days

    return age


def time_decay_factor(age_in_days: int, half_life: int = 30) -> float:
    # Exponential decay function based on the post age
    decay = 0.5 ** (age_in_days / half_life)
    return decay


def calculate_post_score(comments: Optional[int], shares: Optional[int], likes: Optional[int], hearts: Optional[int],
                         haha: Optional[int], top_comments: Optional[int], post_datetime: str, scraper_at: str) -> (
        Dict)[str, float]:
    age_in_days = calculate_post_age(post_datetime, scraper_at)
    decay = time_decay_factor(age_in_days)

    # Weights for post metrics
    weight_comments = 0.25
    weight_shares = 0.25
    weight_likes = 0.10
    weight_hearts = 0.10
    weight_haha = -0.05
    weight_wow = 0.005
    weight_angry = -0.10
    weight_sad = -0.005
    weight_top_comments = 0.25

    # Calculate weighted scores with fallback for None
    comments_weight = (comments or 0) * weight_comments
    shares_weight = (shares or 0) * weight_shares
    likes_weight = (likes or 0) * weight_likes
    hearts_weight = (hearts or 0) * weight_hearts
    haha_weight = (haha or 0) * weight_haha
    top_comments_weight = (top_comments or 0) * weight_top_comments

    # Calculate the final total score
    total_score = (
            comments_weight +
            shares_weight +
            likes_weight +
            hearts_weight +
            haha_weight +
            top_comments_weight
    )

    # Apply the decay factor
    adjusted_score = total_score * decay

    return {
        "comments_weight": comments_weight,
        "shares_weight": shares_weight,
        "likes_weight": likes_weight,
        "hearts_weight": hearts_weight,
        "haha_weight": haha_weight,
        "top_comments_weight": top_comments_weight,
        "final_post_weight": adjusted_score
    }


def cal_the_waiters() -> None:
    # Find posts that do not have the 'final_post_weight' field
    posts = collection.find({
        "post_weights.final_post_weight": {"$exists": False}
    })

    for post in posts:
        # Extract relevant data from each post
        comments_count = post.get('numComments', 0)
        shares_count = post.get('numShares', 0)
        likes_count = post['reactions'].get('like', 0)
        hearts_count = post['reactions'].get('love', 0)
        haha_count = post['reactions'].get('haha', 0)
        top_comments_count = len(post.get('comments', []))

        # Extract post datetime and scraper timestamp
        post_datetime = post['datetime']
        scraper_at = post['scraperAt']

        # Calculate the weights for the post
        weights = calculate_post_score(
            comments_count,
            shares_count,
            likes_count,
            hearts_count,
            haha_count,
            top_comments_count,
            post_datetime,
            scraper_at
        )

        # Update the post with the calculated weights
        collection.update_one(
            {"_id": post["_id"]},
            {"$set": {
                "post_weights": {
                    "comments_weight": weights["comments_weight"],
                    "shares_weight": weights["shares_weight"],
                    "likes_weight": weights["likes_weight"],
                    "hearts_weight": weights["hearts_weight"],
                    "haha_weight": weights["haha_weight"],
                    "top_comments_weight": weights["top_comments_weight"],
                },
                "final_weights": weights["final_post_weight"]
            }}
        )

    print("Post weights updated successfully.")


if '__main__' == __name__:
    cal_the_waiters()
