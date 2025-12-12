// TODO: Need to make this better.
export const parseDate = (dateString: string): Date => {
  const now : Date = new Date();
  if (dateString.includes('hrs')) {
    const hoursAgo : number = parseInt(dateString.split(' ')[0], 10);
    return new Date(now.getTime() - hoursAgo * 60 * 60 * 1000);
  } else if (dateString.includes('Yesterday')) {
    const timeParts : string[] = dateString.split('at')[1].trim().split(':');
    const yesterday : Date = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    yesterday.setHours(parseInt(timeParts[0], 10));
    yesterday.setMinutes(parseInt(timeParts[1], 10));
    return yesterday;
  } else if (dateString.match(/\d+ \w+ at \d+:\d+/)) {
    const parts : string[]  = dateString.split(' at ');
    const dateParts : string[]  = parts[0].split(' ');
    const timeParts : string[]  = parts[1].split(':');
    const day: number = parseInt(dateParts[0], 10);
    const month : number = new Date(`${dateParts[1]} 1, 2000`).getMonth();
    const date : Date = new Date(now.getFullYear(), month, day);
    date.setHours(parseInt(timeParts[0], 10));
    date.setMinutes(parseInt(timeParts[1], 10));
    if (date > now) {
      date.setFullYear(date.getFullYear() - 1);
    }
    return date;
  } else if (dateString.match(/\d+ \w+ \d{4} at \d+:\d+/)) {
    return new Date(dateString.replace(' at ', ' '));
  }
  return now;
};
