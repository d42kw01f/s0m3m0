export const getFacebookUsername = (url: string): string | null => {
  try {
    const profileUrlPattern: RegExp = /profile\.php\?id=([^&]+)/;
    const pathPattern: RegExp = /\/([^/?]+)\?/;
    const basePathPattern: RegExp = /\/([^/?]+)/;

    const profileMatch: RegExpMatchArray | null = url.match(profileUrlPattern);
    if (profileMatch) {
      return profileMatch[1];
    }

    const pathMatch: RegExpMatchArray | null = url.match(pathPattern);
    if (pathMatch) {
      return pathMatch[1];
    }

    const basePathMatch: RegExpMatchArray | null = url.match(basePathPattern);
    if (basePathMatch) {
      return basePathMatch[1];
    }

    console.error('ERROR: Unable to find a valid username!');
    return null;
  } catch (e) {
    console.error('ERROR: An exception occurred while extracting the username!', e);
    return null;
  }
};

export const getFacebookUsernameString = `
  (${getFacebookUsername.toString()})
`;
