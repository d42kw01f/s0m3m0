export const parseReactions = (reactions: (string | null)[]): { [key in keyof typeof reactionTypes]: number | null } => {
  const reactionTypes = {
    like: 'Like',
    love: 'Love',
    haha: 'Haha',
    wow: 'Wow',
    care: 'Care',
    sad: 'Sad',
    angry: 'Angry'
  };

  const parsedReactions: { [key in keyof typeof reactionTypes]: number | null } = {
    like: null,
    love: null,
    haha: null,
    wow: null,
    care: null,
    sad: null,
    angry: null
  };

  const parseAbbreviatedNumber = (str: string): number => {
    const num : number = parseFloat(str.replace(/[^\d.]/g, ''));
    const multiplier : string = str.slice(-1).toLowerCase();
    switch (multiplier) {
      case 'K': return num * 1000;
      case 'M': return num * 1000000;
      case 'B': return num * 1000000000;
      default: return num;
    }
  };

  reactions.forEach(reaction => {
    if (reaction) {
      (Object.keys(reactionTypes) as (keyof typeof reactionTypes)[]).forEach(type => {
        if (reaction.includes(reactionTypes[type])) {
          const countMatch = reaction.match(/[\d.,]+[kmb]?\s/i);
          if (countMatch) {
            parsedReactions[type] = parseAbbreviatedNumber(countMatch[0].trim());
          }
        }
      });
    }
  });

  return parsedReactions;
};