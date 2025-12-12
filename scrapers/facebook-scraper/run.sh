#!/bin/bash

npx tsc  # Compile TypeScript code (assuming you have npx and TypeScript installed)

if [ "$1" == "hashtag" ]; then
  node ./dist/facebook_HashtagScraper.js "https://m.facebook.com/hashtag/space" "4"
elif [ "$1" == "page" ]; then
  node ./dist/facebook_PageScraper.js "https://m.facebook.com/anurakumara" "Mon Jul 15 2024 22:00:00 GMT+0530 (India Standard Time)"
elif [ "$1" == "post" ]; then
  echo "post"
fi


echo "Test"
