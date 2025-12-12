import math
from collections import defaultdict
from datetime import datetime, timezone
from math import log
from dateutil import parser
import numpy as np
from multiprocessing import Pool, cpu_count
import json

# Define global constants and functions

REACTION_WEIGHTS = {
    'like': 0.50, 'love': 0.60, 'haha': -0.4,
    'wow': 0.005, 'angry': -0.50, 'sad': -0.005
}

ENGAGEMENT_WEIGHTS = {
    'shares': 0.25, 'comments': 0.25,
    'comment_reactions': 0.6, 'comment_replies': 0.4
}

HALF_LIFE_DAYS = 7
LAMBDA_DECAY = log(2) / HALF_LIFE_DAYS
CURRENT_TIME = datetime.now(timezone.utc)

CANDIDATES = ['anura', 'sajith', 'ranil', 'other', 'no_one']


def parse_datetime(date_str):
    try:
        return parser.parse(date_str).astimezone(timezone.utc)
    except (ValueError, TypeError) as e:
        print(f"Error parsing date '{date_str}': {e}")
        return CURRENT_TIME


def calculate_decay_factor(published_at):
    delta_t = (CURRENT_TIME - published_at).total_seconds() / (24 * 3600)
    delta_t = max(delta_t, 0)
    return math.exp(-LAMBDA_DECAY * delta_t)


def calculate_weighted_reaction(reactions):
    reaction_contributions = {}
    total_weighted_reactions = 0
    for reaction, count in reactions.items():
        r_weight = REACTION_WEIGHTS.get(reaction, 0)
        contribution = r_weight * count
        reaction_contributions[reaction] = contribution
        total_weighted_reactions += contribution
    return total_weighted_reactions, reaction_contributions


def default_dict_float():
    return defaultdict(float)


def process_post(data):
    # Parse post data
    published_at = parse_datetime(data.get('publishedAt'))
    decay_factor = calculate_decay_factor(published_at)
    candidate_scores = data.get('pt_the_candi', {})
    sentiment_score = data.get('pt_the_senti', {}).get('sentiment_score', 0)

    # Calculate engagement metrics
    shares = data.get('sharesCount', 0)
    comments = data.get('commentCount', 0)
    weighted_reactions, reaction_contributions = calculate_weighted_reaction(data.get('reactions', {}))

    # Logarithmic scaling for normalization
    norm_shares = np.log1p(shares)
    norm_comments = np.log1p(comments)
    norm_weighted_reactions = np.log1p(abs(weighted_reactions))

    # Engagement score for the post
    E_p_shares = ENGAGEMENT_WEIGHTS['shares'] * norm_shares
    E_p_comments = ENGAGEMENT_WEIGHTS['comments'] * norm_comments
    E_p_reactions = norm_weighted_reactions  # Reactions are directly added
    E_p = E_p_shares + E_p_comments + E_p_reactions

    # Initialize candidate weights and contributions
    candidate_weights = defaultdict(float)
    field_contributions = defaultdict(default_dict_float)

    for candidate in CANDIDATES:
        C_p_c = candidate_scores.get(candidate, 0)
        weight = E_p * C_p_c * sentiment_score * decay_factor
        candidate_weights[candidate] += weight

        # Calculate contributions from each field
        field_contributions[candidate]['post_shares'] += E_p_shares * C_p_c * sentiment_score * decay_factor
        field_contributions[candidate]['post_comments'] += E_p_comments * C_p_c * sentiment_score * decay_factor
        field_contributions[candidate]['post_reactions'] += E_p_reactions * C_p_c * sentiment_score * decay_factor

        # Breakdown of reactions
        for reaction, contribution in reaction_contributions.items():
            norm_reaction = np.log1p(abs(contribution))
            reaction_weight = norm_reaction * C_p_c * sentiment_score * decay_factor
            field_contributions[candidate][f'post_reaction_{reaction}'] += reaction_weight

    # Process comments
    top_comments = data.get('top_comments', [])
    for comment_data in top_comments:
        # Parse comment data
        comment_published_at = parse_datetime(comment_data.get('publishedAt'))
        comment_decay_factor = calculate_decay_factor(comment_published_at)
        comment_candidate_scores = comment_data.get('pt_the_candi', {})
        comment_sentiment_score = comment_data.get('pt_the_senti', {}).get('sentiment_score', 0)
        comment_replies = comment_data.get('commentReplyCount', 0)
        comment_weighted_reactions, comment_reaction_contributions = calculate_weighted_reaction(
            comment_data.get('commentReaction', {}))

        # Logarithmic scaling for normalization
        norm_comment_reactions = np.log1p(abs(comment_weighted_reactions))
        norm_comment_replies = np.log1p(comment_replies)

        # Engagement score for the comment
        E_c_reactions = ENGAGEMENT_WEIGHTS['comment_reactions'] * norm_comment_reactions
        E_c_replies = ENGAGEMENT_WEIGHTS['comment_replies'] * norm_comment_replies
        E_c = E_c_reactions + E_c_replies

        for candidate in CANDIDATES:
            C_c_c = comment_candidate_scores.get(candidate, 0)
            weight = E_c * C_c_c * comment_sentiment_score * comment_decay_factor
            candidate_weights[candidate] += weight

            # Calculate contributions from each field
            field_contributions[candidate][
                'comment_reactions'] += E_c_reactions * C_c_c * comment_sentiment_score * comment_decay_factor
            field_contributions[candidate][
                'comment_replies'] += E_c_replies * C_c_c * comment_sentiment_score * comment_decay_factor

            # Breakdown of comment reactions
            for reaction, contribution in comment_reaction_contributions.items():
                norm_reaction = np.log1p(abs(contribution))
                reaction_weight = norm_reaction * ENGAGEMENT_WEIGHTS['comment_reactions']
                reaction_weight *= C_c_c * comment_sentiment_score * comment_decay_factor
                field_contributions[candidate][f'comment_reaction_{reaction}'] += reaction_weight

    return candidate_weights, field_contributions


def aggregate_results(results):
    total_candidate_weights = defaultdict(float)
    total_field_contributions = defaultdict(default_dict_float)

    for candidate_weights, field_contributions in results:
        for candidate, weight in candidate_weights.items():
            total_candidate_weights[candidate] += weight
        for candidate, fields in field_contributions.items():
            for field, value in fields.items():
                total_field_contributions[candidate][field] += value
    return total_candidate_weights, total_field_contributions


def normalize_candidate_weights(total_candidate_weights):
    sum_of_weights = sum(total_candidate_weights.values())
    if sum_of_weights != 0:
        normalized_weights = {
            candidate: (weight / sum_of_weights) * 100
            for candidate, weight in total_candidate_weights.items()
        }
    else:
        normalized_weights = {candidate: 0 for candidate in CANDIDATES}
    return normalized_weights


def analyze_posts(posts_data):
    # Use multiprocessing to process posts in parallel
    with Pool(processes=cpu_count()) as pool:
        results = pool.map(process_post, posts_data)

    # Aggregate candidate weights and field contributions
    _total_candidate_weights, _total_field_contributions = aggregate_results(results)

    # Normalize candidate weights
    normalized_weights = normalize_candidate_weights(_total_candidate_weights)

    return _total_candidate_weights, normalized_weights, _total_field_contributions


if __name__ == '__main__':
    posts_data = [
        {
            'newsId': 1,
            'platform': 'Facebook',
            'reactions': {
                'like': 1200, 'love': 50, 'haha': 20, 'wow': 10, 'sad': 5, 'angry': 5
            },
            'sharesCount': 0,
            'commentCount': 80,
            'publishedAt': 'Fri, 20 Sep 2024 12:58:32 GMT+0000',
            'scrapedAt': '2023-10-02T12:00:00Z',
            'newsTitleEn': 'Anura is making great strides in the election!',
            'newsContentLl': 'Anura Leads the Polls',
            'top_comments': [
                {
                    'commentText': 'I fully support Anura!',
                    'commentReaction': {'like': 50, 'love': 20},
                    'commentReplyCount': 10,
                    'publishedAt': 'Tue, 24 Sep 2024 15:04:36 GMT+0000',
                    'pt_the_candi': {'anura': 0.2, 'sajith': 0.4, 'ranil': 0.5},
                    'pt_the_senti': {'sentiment_score': 0.8}
                },
                {
                    'commentText': "Not sure about Anura's policies.",
                    'commentReaction': {'haha': 30, 'like': 3},
                    'commentReplyCount': 5,
                    'publishedAt': 'Tue, 24 Sep 2024 15:04:36 GMT+0000',
                    'pt_the_candi': {'anura': 0.8, 'sajith': 0.1, 'ranil': 0.12},
                    'pt_the_senti': {'sentiment_score': -0.4}
                },
            ],
            'pt_the_candi': {'anura': 0.5, 'sajith': 0.1, 'ranil': 0.021312},
            'pt_the_senti': {'sentiment_score': 0.6}
        },
        # Add more post data dictionaries as needed
    ]

    total_candidate_weights, normalized_candidate_weights, total_field_contributions = analyze_posts(posts_data)

    print("Total Candidate Weights:")
    for candidate, weight in total_candidate_weights.items():
        print(f"{candidate.capitalize()}: {weight}")

    print("\nCandidate Popularity Percentages:")
    for candidate, percentage in normalized_candidate_weights.items():
        print(f"{candidate.capitalize()}: {percentage}%")

    print("\nField Contributions:")
    for candidate, fields in total_field_contributions.items():
        print(f"\nCandidate: {candidate.capitalize()}")
        for field, value in fields.items():
            print(f"  {field}: {value}")
