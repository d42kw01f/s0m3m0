import math
from collections import defaultdict
from datetime import datetime, timezone
from math import log
from dateutil import parser  # Importing dateutil for robust date parsing


class Post:
    reaction_weights = {
        'like': 0.10, 'love': 0.10, 'haha': -0.05,
        'wow': 0.005, 'angry': -0.10, 'sad': -0.005
    }
    engagement_weights = {
        'shares': 0.25, 'comments': 0.25,
        'comment_reactions': 0.6, 'comment_replies': 0.4
    }
    half_life_days = 7
    lambda_decay = log(2) / half_life_days
    current_time = datetime.now(timezone.utc)
    gamma = 0.5  # Scaling factor for negative sentiments

    def __init__(self, data):
        self.data = data
        self.published_at = self.parse_datetime(data.get('publishedAt'))
        self.decay_factor = self.calculate_decay_factor(self.published_at)
        self.candidate_scores = data.get('pt_the_candi', {})
        self.sentiment_score = data.get('pt_the_senti', {}).get('sentiment_score', 0)
        self.engagement_metrics = self.calculate_engagement_metrics()
        self.top_comments = [Comment(comment, self) for comment in data.get('top_comments', [])]

    def parse_datetime(self, date_str):
        """
        Parses the datetime string into a timezone-aware datetime object.
        Utilizes dateutil.parser for flexibility with various date formats.
        """
        try:
            return parser.parse(date_str).astimezone(timezone.utc)
        except (ValueError, TypeError) as e:
            # Handle parsing errors by logging and setting to current time or another default
            print(f"Error parsing date '{date_str}': {e}")
            return Post.current_time

    def calculate_decay_factor(self, published_at):
        delta_t = (Post.current_time - published_at).total_seconds() / (24 * 3600)
        return math.exp(-Post.lambda_decay * delta_t)

    def calculate_weighted_reaction(self, reactions):
        return sum(
            Post.reaction_weights.get(reaction, 0) * count
            for reaction, count in reactions.items()
        )

    def calculate_engagement_metrics(self):
        engagement = {
            'shares': self.data.get('sharesCount', 0),
            'comments': self.data.get('commentCount', 0),
            'weighted_reactions': abs(
                self.calculate_weighted_reaction(self.data.get('reactions', {}))
            )
        }
        return engagement


class Comment:
    def __init__(self, data, parent_post):
        self.data = data
        self.parent_post = parent_post
        self.published_at = self.parse_datetime(data.get('publishedAt', parent_post.data.get('publishedAt')))
        self.decay_factor = self.calculate_decay_factor(self.published_at)
        self.candidate_scores = data.get('pt_the_candi', {})
        self.sentiment_score = data.get('pt_the_senti', {}).get('sentiment_score', 0)
        self.reply_count = data.get('reply_count', 0)
        self.engagement_metrics = self.calculate_engagement_metrics()

    def parse_datetime(self, date_str):
        try:
            return parser.parse(date_str).astimezone(timezone.utc)
        except (ValueError, TypeError) as e:
            print(f"Error parsing date '{date_str}': {e}")
            return Post.current_time

    def calculate_decay_factor(self, published_at):
        delta_t = (Post.current_time - published_at).total_seconds() / (24 * 3600)
        return math.exp(-Post.lambda_decay * delta_t)

    def calculate_weighted_reaction(self, reactions):
        return sum(
            Post.reaction_weights.get(reaction, 0) * count
            for reaction, count in reactions.items()
        )

    def calculate_engagement_metrics(self):
        engagement = {
            'reactions': abs(
                self.calculate_weighted_reaction(self.data.get('reactions', {}))
            ),
            'replies': self.reply_count
        }
        return engagement


class EngagementAnalyzer:
    gamma = 0.5  # Scaling factor for negative sentiments

    def __init__(self, post_data):
        # Initialize with a list of posts
        self.posts = [Post(post_data)]
        self.total_engagements = defaultdict(list)
        self.total_candidate_weights = defaultdict(float)
        self.candidates = ['anura', 'sajith', 'ranil', 'other', 'no_one']

    def collect_engagement_data(self):
        for post in self.posts:
            self.total_engagements['shares'].append(post.engagement_metrics['shares'])
            self.total_engagements['comments'].append(post.engagement_metrics['comments'])
            self.total_engagements['weighted_reactions'].append(post.engagement_metrics['weighted_reactions'])
            for comment in post.top_comments:
                self.total_engagements['comment_reactions'].append(comment.engagement_metrics['reactions'])
                self.total_engagements['comment_replies'].append(comment.engagement_metrics['replies'])

    def normalize_engagement(self, engagement_list):
        max_value = max(engagement_list) if engagement_list else 1
        return [v / max_value if max_value else 0 for v in engagement_list]

    def calculate_post_weights(self):
        # Normalize engagements
        normalized_engagements = {
            key: self.normalize_engagement(self.total_engagements[key])
            for key in self.total_engagements
        }

        # Keep track of the indices for comments
        comment_index = 0

        for i, post in enumerate(self.posts):
            normalized_shares = normalized_engagements['shares'][i]
            normalized_comments = normalized_engagements['comments'][i]
            normalized_weighted_reactions = normalized_engagements['weighted_reactions'][i]
            E_p = (
                Post.engagement_weights['shares'] * normalized_shares +
                Post.engagement_weights['comments'] * normalized_comments +
                normalized_weighted_reactions
            )

            # Compute sentiment factor for post
            S_p = post.sentiment_score
            if S_p >= 0:
                sentiment_factor = 1 + S_p
            else:
                sentiment_factor = 1 + self.gamma * S_p

            # For each candidate
            for e_candidate in self.candidates:
                C_p_c = post.candidate_scores.get(e_candidate, 0)
                weight = E_p * C_p_c * post.decay_factor * sentiment_factor
                self.total_candidate_weights[e_candidate] += weight

            # Process comments
            for comment in post.top_comments:
                normalized_comment_reactions = normalized_engagements['comment_reactions'][comment_index]
                normalized_comment_replies = normalized_engagements['comment_replies'][comment_index]
                E_c = (
                    Post.engagement_weights['comment_reactions'] * normalized_comment_reactions +
                    Post.engagement_weights['comment_replies'] * normalized_comment_replies
                )

                # Compute sentiment factor for comment
                S_c = comment.sentiment_score
                if S_c >= 0:
                    sentiment_factor = 1 + S_c
                else:
                    sentiment_factor = 1 + self.gamma * S_c

                # For each candidate
                for e_candidate in self.candidates:
                    C_c_c = comment.candidate_scores.get(e_candidate, 0)
                    weight = E_c * C_c_c * comment.decay_factor * sentiment_factor
                    self.total_candidate_weights[e_candidate] += weight

                comment_index += 1  # Increment the comment index

    def get_normalized_candidate_weights(self):
        sum_of_abs_weights = sum(abs(main_weight) for main_weight in self.total_candidate_weights.values())
        normalized_weights = {
            m_candidate: (m_weight / sum_of_abs_weights) * 100 if sum_of_abs_weights else 0
            for m_candidate, m_weight in self.total_candidate_weights.items()
        }
        return normalized_weights

    def analyze(self):
        self.collect_engagement_data()
        self.calculate_post_weights()
        normalized_weights = self.get_normalized_candidate_weights()
        return self.total_candidate_weights, normalized_weights


if __name__ == '__main__':
    # Example usage with a list of post data
    post_data_list = [
        {
            'post_id': 1,
            'platform': 'Facebook',
            'reactions': {
                'like': 100, 'love': 50, 'haha': 20, 'wow': 10, 'sad': 5, 'angry': 5
            },
            'commentCount': 80,
            'share_count': 40,
            'publishedAt': 'Fri, 20 Sep 2023 12:58:32 GMT+0000',
            'scrapedAt': '2023-10-02T12:00:00Z',
            'post_text': 'Anura is making great strides in the election!',
            'post_title': 'Anura Leads the Polls',
            'top_comments': [
                {
                    'comment_text': 'I fully support Anura!',
                    'reactions': {'like': 50, 'love': 20},
                    'reply_count': 10,
                    'publishedAt': '2023-10-01T13:00:00Z',
                    'candidate_scores': {'anura': 0.9},
                    'pt_the_senti': {'sentiment_score': 0.8}
                },
                {
                    'comment_text': 'Not sure about Anura\'s policies.',
                    'reactions': {'like': 30},
                    'reply_count': 5,
                    'publishedAt': '2023-10-01T14:00:00Z',
                    'candidate_scores': {'sajith': 0.7},
                    'pt_the_senti': {'sentiment_score': -0.4}
                },
            ],
            'pt_the_candi': {'anura': 0.5, 'sajith': 0.1, 'ranil': 0.021312},
            'pt_the_senti': {'sentiment_score': 0.6}
        },
        {
            'post_id': 2,
            'platform': 'Twitter',
            'reactions': {
                'like': 150, 'love': 30, 'haha': 10, 'wow': 5, 'sad': 2, 'angry': 3
            },
            'commentCount ': 60,
            'share_count': 20,
            'publishedAt': 'Sat, 21 Sep 2023 15:20:00 GMT+0000',
            'scrapedAt': '2023-10-03T16:00:00Z',
            'post_text': 'Sajith has shown great leadership in recent times.',
            'post_title': '',
            'top_comments': [
                {
                    'comment_text': 'Sajith is the best choice!',
                    'reactions': {'like': 40, 'love': 10},
                    'reply_count': 8,
                    'publishedAt': '2023-10-02T10:00:00Z',
                    'pt_the_candi': {'sajith': 0.85},
                    'pt_the_senti': {'sentiment_score': 0.0}
                },
                {
                    'comment_text': 'Not impressed with Sajith\'s strategies.',
                    'reactions': {'like': 20, 'angry': 5},
                    'reply_count': 3,
                    'publishedAt': '2023-10-02T11:30:00Z',
                    'pt_the_candi': {'sajith': 0.6},
                    'pt_the_senti': {'sentiment_score': -0.5}
                },
            ],
            'pt_the_candi': {'anura': 0.1, 'sajith': 0.7, 'ranil': 0.05},
            'pt_the_senti': {'sentiment_score': 0.7}
        },
        # Add more posts as needed
    ]

    analyzer = EngagementAnalyzer(post_data_list)
    total_candidate_weights, normalized_candidate_weights = analyzer.analyze()

    print("Total Candidate Weights:")
    for candidate, weight in total_candidate_weights.items():
        print(f"{candidate.capitalize()}: {weight}")

    print("\nCandidate Popularity Percentages:")
    for candidate, percentage in normalized_candidate_weights.items():
        sign = '+' if percentage >= 0 else '-'
        print(f"{candidate.capitalize()}: {sign}{abs(percentage):.2f}%")
