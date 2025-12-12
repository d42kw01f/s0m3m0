export interface IPostAdd {
  scrapeAt: string | null;
  full_post_text: string | null;
  full_comment: (string | null)[] | null;
  reaction_url?: string | null;
  reactions?: (string | null)[] | null;
}
