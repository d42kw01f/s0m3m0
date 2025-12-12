from textblob import TextBlob


def calculate_sentiment_score(post_text: str) -> float:
    sentiment = TextBlob(post_text).sentiment.polarity + 0.001
    return sentiment
