export default function getLastPostDate(postDetailsJson: any[]): Date | null {
  if (postDetailsJson.length === 0) {
    return null;
  }

  const lastPost = postDetailsJson[postDetailsJson.length - 1];
  const lastPostDate : Date = new Date(lastPost.datetime);

  return isNaN(lastPostDate.getTime()) ? null : lastPostDate;
}
