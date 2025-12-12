export interface INormalPost {
  postId: string;
  scraperAt: string;
  datetime: string | null;
  post_text: string | null;
  username: string | null;
  post_url: string | null;
  img_content: (string | null)[] | null;
  num_reaction: number | null;
  num_shares: number | null;
  num_comments: number | null;
  two_comments: (string | null)[] | null;
  additionalContent?: any;
}
