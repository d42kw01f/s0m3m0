import math
from collections import defaultdict
from datetime import datetime, timezone

# Sample data structure for posts
posts = [
    {
        'post_id': 1,
        'platform': 'Facebook',
        'reactions_count': {'like': 100, 'love': 50, 'haha': 20, 'wow': 10, 'sad': 5, 'angry': 5},
        'comment_count': 80,
        'share_count': 40,
        'published_at': '2023-10-01T12:00:00Z',
        'scraped_at': '2023-10-02T12:00:00Z',
        'post_text': 'Anura is making great strides in the election!',
        'post_title': 'Anura Leads the Polls',
        'top_comments': [
            {
                'comment_text': 'I fully support Anura!',
                'reactions_count': {'like': 50, 'love': 20},
                'reply_count': 10,
                'published_at': '2023-10-01T13:00:00Z',
                'candidate_scores': {'anura': 0.9},
                'sentiment_score': 0.8
            },
            {
                'comment_text': 'Not sure about Anura\'s policies.',
                'reactions_count': {'like': 30},
                'reply_count': 5,
                'published_at': '2023-10-01T14:00:00Z',
                'candidate_scores': {'sajith': 0.7},
                'sentiment_score': -0.4
            },
        ],
        'candidate_scores': {'anura': 0.5, 'sajith': 0.1, 'ranil': 0.021312},
        'sentiment_score': 0.6
    },
]

candidates = ['anura', 'sajith', 'ranil']

total_candidate_weights = defaultdict(float)
total_engagements = {
    'shares': [],
    'comments': [],
    'weighted_reactions': [],
    'comment_reactions': [],
    'comment_replies': []
}

reaction_weights = {
    'like': 0.10,
    'love': 0.10,
    'haha': -0.05,
    'wow': 0.005,
    'angry': -0.10,
    'sad': -0.005
}

weights = {
    'shares': 0.25,
    'comments': 0.25,
    'comment_reactions': 0.6,  # Using previous weight
    'comment_replies': 0.4  # Using previous weight
}

# Decay constant (lambda)
from math import log

half_life_days = 7
lambda_decay = log(2) / half_life_days  # Decay constant per day

# Current time (assuming UTC)
current_time = datetime.now(timezone.utc)

# Process each post
for post in posts:
    # Convert published_at to datetime
    published_at_str = post.get('published_at')
    if published_at_str:
        published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    else:
        # If published_at is missing, skip the post
        continue

    # Calculate time difference in days
    delta_t = (current_time - published_at).total_seconds() / (24 * 3600)  # Convert seconds to days

    # Compute decay factor
    D_p = math.exp(-lambda_decay * delta_t)

    # Normalize engagement metrics
    normalized_shares = post.get('share_count', 0)
    total_engagements['shares'].append(normalized_shares)

    normalized_comments = post.get('comment_count', 0)
    total_engagements['comments'].append(normalized_comments)

    # Calculate weighted reactions
    reactions = post.get('reactions_count', {})
    weighted_reaction_score = sum(
        reaction_weights.get(reaction, 0) * count for reaction, count in reactions.items()
    )
    total_engagements['weighted_reactions'].append(abs(weighted_reaction_score))  # Use absolute value for normalization

    # Candidate relevance scores (C_p[c])
    candidate_scores = post.get('candidate_scores', {})

    # Use raw Sentiment Score (S_p)
    S_p = post.get('sentiment_score', 0)

    # Will normalize after collecting max values

    # Process top comments
    for comment in post.get('top_comments', []):
        # Calculate weighted reactions for comment
        comment_reactions = comment.get('reactions_count', {})
        weighted_comment_reaction_score = sum(
            reaction_weights.get(reaction, 0) * count for reaction, count in comment_reactions.items()
        )
        total_engagements['comment_reactions'].append(abs(weighted_comment_reaction_score))  # Use absolute value

        total_engagements['comment_replies'].append(comment.get('reply_count', 0))

# Get max values for normalization
max_shares = max(total_engagements['shares']) if total_engagements['shares'] else 1
max_comments = max(total_engagements['comments']) if total_engagements['comments'] else 1
max_weighted_reactions = max(total_engagements['weighted_reactions']) if total_engagements['weighted_reactions'] else 1
max_comment_reactions = max(total_engagements['comment_reactions']) if total_engagements['comment_reactions'] else 1
max_comment_replies = max(total_engagements['comment_replies']) if total_engagements['comment_replies'] else 1

# Re-process each post with normalization
for post in posts:
    # Convert published_at to datetime
    published_at_str = post.get('published_at')
    if published_at_str:
        published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    else:
        continue

    # Calculate time difference in days
    delta_t = (current_time - published_at).total_seconds() / (24 * 3600)

    # Compute decay factor
    D_p = math.exp(-lambda_decay * delta_t)

    # Normalize engagement metrics
    shares = post.get('share_count', 0)
    normalized_shares = shares / max_shares if max_shares else 0

    comments = post.get('comment_count', 0)
    normalized_comments = comments / max_comments if max_comments else 0

    reactions = post.get('reactions_count', {})
    weighted_reaction_score = sum(
        reaction_weights.get(reaction, 0) * count for reaction, count in reactions.items()
    )
    normalized_weighted_reactions = weighted_reaction_score / max_weighted_reactions if max_weighted_reactions else 0

    # Calculate Engagement Metric (E_p)
    E_p = (weights['shares'] * normalized_shares) + \
          (weights['comments'] * normalized_comments) + \
          normalized_weighted_reactions

    # Candidate relevance scores (C_p[c])
    candidate_scores = post.get('candidate_scores', {})

    # Use raw Sentiment Score (S_p)
    S_p = post.get('sentiment_score', 0)

    # Compute Candidate Weights per Post (w_p[c])
    w_p = {}
    for candidate in candidates:
        C_p_c = candidate_scores.get(candidate, 0)
        w_p_c = E_p * C_p_c * S_p * D_p  # Apply decay factor
        w_p[candidate] = w_p_c

    # Process top comments
    W_p_comments = defaultdict(float)
    for comment in post.get('top_comments', []):
        # Convert comment published_at to datetime
        comment_published_at_str = comment.get('published_at')
        if comment_published_at_str:
            comment_published_at = datetime.strptime(comment_published_at_str, '%Y-%m-%dT%H:%M:%SZ').replace(
                tzinfo=timezone.utc)
            delta_t_comment = (current_time - comment_published_at).total_seconds() / (24 * 3600)
        else:
            delta_t_comment = delta_t  # If missing, assume same as post

        # Compute decay factor for comment
        D_c = math.exp(-lambda_decay * delta_t_comment)

        # Normalize comment engagement metrics
        comment_reactions = comment.get('reactions_count', {})
        weighted_comment_reaction_score = sum(
            reaction_weights.get(reaction, 0) * count for reaction, count in comment_reactions.items()
        )
        normalized_comment_reactions = weighted_comment_reaction_score / max_comment_reactions if max_comment_reactions else 0

        replies = comment.get('reply_count', 0)
        normalized_comment_replies = replies / max_comment_replies if max_comment_replies else 0

        # Calculate Comment Engagement Metric (E_c)
        E_c = (weights['comment_reactions'] * normalized_comment_reactions) + \
              (weights['comment_replies'] * normalized_comment_replies)

        # Use raw Sentiment Score (S_c)
        S_c = comment.get('sentiment_score', 0)

        # Candidate relevance scores (C_c[c])
        candidate_scores_comment = comment.get('candidate_scores', {})

        # Compute Candidate Weights per Comment (w_c[c])
        for candidate in candidates:
            C_c_c = candidate_scores_comment.get(candidate, 0)
            w_c_c = E_c * C_c_c * S_c * D_c  # Apply decay factor
            W_p_comments[candidate] += w_c_c

    # Combine Post and Comment Weights
    for candidate in candidates:
        total_candidate_weights[candidate] += w_p.get(candidate, 0) + W_p_comments.get(candidate, 0)

# Sum of absolute weights for normalization
sum_of_abs_weights = sum(abs(weight) for weight in total_candidate_weights.values())

normalized_candidate_weights = {}
if sum_of_abs_weights > 0:
    for candidate, weight in total_candidate_weights.items():
        normalized_candidate_weights[candidate] = (weight / sum_of_abs_weights) * 100  # Percentage
else:
    for candidate in candidates:
        normalized_candidate_weights[candidate] = 0

# Output the results
print(total_candidate_weights)
print(normalized_candidate_weights)
# Output results
print("Candidate Popularity Percentages:")
for candidate, percentage in normalized_candidate_weights.items():
    sign = '+' if percentage >= 0 else '-'
    print(f"{candidate.capitalize()}: {sign}{abs(percentage):.2f}%")
