// Define the interface for a URL object in image content
export interface IImgContentUrl {
  url: string;
  downloaded: boolean;
}

// Define the type that imgContent can be, either a URL object or a string
export type ImgContent = IImgContentUrl;

// Define the interface for a single post, using the ImgContent type
export interface ISinglePost {
  postId: string;
  scraperAt: string;
  datetime: string | null;
  postFullText: string | null;
  imgContent: ImgContent[] | null;
  numShares: number | null;
  numComments: number | null;
  reactions: {
    like: number | null;
    love: number | null;
    haha: number | null;
    wow: number | null;
    care: number | null;
    sad: number | null;
    angry: number | null;
  };
  comments: (string | null)[] | null;
  additionalContent?: any;
}
