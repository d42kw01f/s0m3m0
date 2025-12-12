import math
from collections import defaultdict
from datetime import datetime, timezone
from math import log


class Post:
    reaction_weights = {'like': 0.10, 'love': 0.10, 'haha': -0.05, 'wow': 0.005, 'angry': -0.10, 'sad': -0.005}
    engagement_weights = {'shares': 0.25, 'comments': 0.25, 'comment_reactions': 0.6, 'comment_replies': 0.4}
    half_life_days = 7
    lambda_decay = log(2) / half_life_days
    current_time = datetime.now(timezone.utc)

    def __init__(self, data):
        self.data = data
        self.published_at = self.parse_datetime(data.get('published_at'))
        self.decay_factor = self.calculate_decay_factor(self.published_at)
        self.candidate_scores = data.get('candidate_scores', {})
        self.sentiment_score = data.get('sentiment_score', 0)
        self.engagement_metrics = self.calculate_engagement_metrics()
        self.top_comments = [Comment(comment) for comment in data.get('top_comments', [])]

    def parse_datetime(self, date_str):
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

    def calculate_decay_factor(self, published_at):
        delta_t = (Post.current_time - published_at).total_seconds() / (24 * 3600)
        return math.exp(-Post.lambda_decay * delta_t)

    def calculate_weighted_reaction(self, reactions):
        return sum(Post.reaction_weights.get(reaction, 0) * count for reaction, count in reactions.items())

    def calculate_engagement_metrics(self):
        engagement = {
            'shares': self.data.get('share_count', 0),
            'comments': self.data.get('comment_count', 0),
            'weighted_reactions': abs(self.calculate_weighted_reaction(self.data.get('reactions_count', {})))
        }
        return engagement


class Comment(Post):
    def __init__(self, data):
        super().__init__(data)
        self.reply_count = data.get('reply_count', 0)
        self.comment_sentiment_score = data.get('sentiment_score', 0)
        self.comment_candidate_scores = data.get('candidate_scores', {})


class EngagementAnalyzer:
    def __init__(self, posts):
        self.posts = [Post(data) for data in posts]
        self.total_engagements = defaultdict(list)
        self.total_candidate_weights = defaultdict(float)
        self.candidates = ['anura', 'sajith', 'ranil']

    def collect_engagement_data(self):
        for post in self.posts:
            self.total_engagements['shares'].append(post.engagement_metrics['shares'])
            self.total_engagements['comments'].append(post.engagement_metrics['comments'])
            self.total_engagements['weighted_reactions'].append(post.engagement_metrics['weighted_reactions'])
            for comment in post.top_comments:
                self.total_engagements['comment_reactions'].append(
                    abs(comment.calculate_weighted_reaction(comment.data.get('reactions_count', {}))))
                self.total_engagements['comment_replies'].append(comment.reply_count)

    @staticmethod
    def normalize_engagement(engagement_list):
        max_value = max(engagement_list) if engagement_list else 1
        return [v / max_value if max_value else 0 for v in engagement_list]

    def calculate_post_weights(self):
        normalized_engagements = {
            key: self.normalize_engagement(self.total_engagements[key])
            for key in self.total_engagements
        }

        for i, post in enumerate(self.posts):
            normalized_shares = normalized_engagements['shares'][i]
            normalized_comments = normalized_engagements['comments'][i]
            normalized_weighted_reactions = normalized_engagements['weighted_reactions'][i]
            E_p = (
                    Post.engagement_weights['shares'] * normalized_shares +
                    Post.engagement_weights['comments'] * normalized_comments +
                    normalized_weighted_reactions
            )
            for candi in self.candidates:
                C_p_c = post.candidate_scores.get(candi, 0)
                self.total_candidate_weights[candi] += E_p * C_p_c * post.sentiment_score * post.decay_factor

            for j, comment in enumerate(post.top_comments):
                normalized_comment_reactions = normalized_engagements['comment_reactions'][j]
                normalized_comment_replies = normalized_engagements['comment_replies'][j]
                E_c = (
                        Post.engagement_weights['comment_reactions'] * normalized_comment_reactions +
                        Post.engagement_weights['comment_replies'] * normalized_comment_replies
                )
                for candi in self.candidates:
                    C_c_c = comment.comment_candidate_scores.get(candi, 0)
                    self.total_candidate_weights[
                        candi] += E_c * C_c_c * comment.comment_sentiment_score * comment.decay_factor

    def get_normalized_candidate_weights(self):
        sum_of_abs_weights = sum(abs(weight) for weight in self.total_candidate_weights.values())
        normalized_weights = {
            m_candi: (m_weight / sum_of_abs_weights) * 100 if sum_of_abs_weights else 0
            for m_candi, m_weight in self.total_candidate_weights.items()
        }
        return normalized_weights

    def analyze(self):
        self.collect_engagement_data()
        self.calculate_post_weights()
        normalized_weights = self.get_normalized_candidate_weights()
        return self.total_candidate_weights, normalized_weights


if __name__ == "__main__":
    posts_data = [
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

    analyzer = EngagementAnalyzer(posts_data)
    total_candidate_weights, normalized_candidate_weights = analyzer.analyze()

    print("Total Candidate Weights:")
    for candidate, weight in total_candidate_weights.items():
        print(f"{candidate.capitalize()}: {weight}")

    print("\nCandidate Popularity Percentages:")
    for candidate, percentage in normalized_candidate_weights.items():
        sign = '+' if percentage >= 0 else '-'
        print(f"{candidate.capitalize()}: {sign}{abs(percentage):.2f}%")
