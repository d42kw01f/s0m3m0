import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

def load_data():
    client = MongoClient("mongodb://localhost:27017/")
    db = client['esana_scraper']
    collection = db['news_articles']
    return list(collection.find())


# Load data from MongoDB
data = load_data()


# Helper functions
def get_candidate_scores(data):
    candidate_scores = {'anura': 0, 'sajith': 0, 'ranil': 0, 'other': 0, 'no_one': 0}
    candidate_top_counts = {'anura': 0, 'sajith': 0, 'ranil': 0, 'other': 0, 'no_one': 0}

    for doc in data:
        weights = doc.get('pt_the_waiter', {}).get('total_candidate_weights', {})
        for candidate in ['anura', 'sajith', 'ranil', 'other', 'no_one']:
            candidate_scores[candidate] += weights.get(candidate, 0)
        if weights:
            top_candidate = max(weights, key=weights.get)
            if top_candidate in candidate_top_counts:
                candidate_top_counts[top_candidate] += 1

    return candidate_scores, candidate_top_counts



def get_sentiment_stats(data):
    sentiment_scores = [
        doc.get('pt_the_senti', {}).get('sentiment_score', 0) for doc in data
    ]
    return sentiment_scores


def get_reaction_stats(data):
    reactions = {'like': 0, 'love': 0, 'haha': 0, 'wow': 0, 'sad': 0, 'angry': 0}
    for doc in data:
        for rtype, count in doc.get('reactions', {}).items():
            reactions[rtype] += count
    return reactions


def get_top_documents(data, key, n=5):
    return sorted(data, key=lambda x: sum(x.get(key, {}).values()), reverse=True)[:n]


# Streamlit App Layout
st.title("Candidate Scoring Analysis Dashboard")

# Section 1: Candidate Scoring
st.header("1. Candidate Scoring Overview")
candidate_scores, candidate_top_counts = get_candidate_scores(data)
st.subheader("Total Candidate Scores")
st.bar_chart(candidate_scores)

st.subheader("Top Candidate Distribution")
st.write(pd.DataFrame(candidate_top_counts.items(), columns=['Candidate', 'Top Counts']))

# Section 2: Sentiment Analysis
st.header("2. Sentiment Analysis")
sentiment_scores = get_sentiment_stats(data)
st.subheader("Sentiment Score Distribution")
if sentiment_scores:
    fig = px.histogram(x=sentiment_scores, nbins=10, title="Sentiment Distribution")
    st.plotly_chart(fig)
    st.write(f"Average Sentiment Score: {sum(sentiment_scores) / len(sentiment_scores):.2f}")
else:
    st.write("No sentiment data available.")

# Section 3: Reactions Overview
st.header("3. Reactions Overview")
reactions = get_reaction_stats(data)
st.subheader("Reaction Counts")
st.bar_chart(reactions)

# Section 4: Top Reacted Documents
st.header("4. Top Reacted Documents")
top_docs = get_top_documents(data, 'reactions', n=5)
for idx, doc in enumerate(top_docs, start=1):
    st.write(f"**#{idx} - {doc.get('newsTitleEn', 'No Title')}**")
    st.write(f"Total Reactions: {sum(doc.get('reactions', {}).values())}")
    st.write("---")

# Section 5: Comments Overview
st.header("5. Comments Overview")
st.subheader("Top Comments by Sentiment")
for doc in data[:3]:  # Show 3 examples
    comments = doc.get('top_comments', [])
    if comments:
        top_comment = max(comments, key=lambda c: c.get('pt_the_senti', {}).get('sentiment_score', 0))
        st.write(f"**Title:** {doc.get('newsTitleEn', 'No Title')}")
        st.write(f"**Top Comment:** {top_comment.get('commentText', 'No Comment')}")
        st.write(f"**Sentiment Score:** {top_comment.get('pt_the_senti', {}).get('sentiment_score', 'N/A')}")
        st.write("---")

# Section 6: Time-Based Trends (if applicable)
if any(doc.get('publishedAt') for doc in data):
    st.header("6. Time-Based Trends")
    st.subheader("Publication Timeline")
    time_data = pd.DataFrame(
        [doc.get('publishedAt') for doc in data if 'publishedAt' in doc],
        columns=['Published Date']
    )
    time_data['Published Date'] = pd.to_datetime(time_data['Published Date'])
    time_data['Count'] = 1
    time_data = time_data.groupby('Published Date').count().reset_index()
    fig = px.line(time_data, x='Published Date', y='Count', title="Publication Trend")
    st.plotly_chart(fig)

st.write("Dashboard created with ❤️ using Streamlit")
