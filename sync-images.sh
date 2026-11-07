#!/usr/bin/env zsh
set -euo pipefail

cd "${0:A:h}"

echo "1/3 Updating filenames.js from images/..."
python3 filenames.py

echo "2/3 Syncing images/ and filenames.js to s3://cksau-website..."
aws s3 sync images/ s3://cksau-website/images/ --delete \
  --exclude ".DS_Store" \
  --exclude "*/.DS_Store"
aws s3 cp filenames.js s3://cksau-website/filenames.js

echo "3/3 Invalidating CloudFront cache for images and filenames.js..."
aws cloudfront create-invalidation \
  --distribution-id E28V6ZSCH5HVUA \
  --paths "/images/*" "/filenames.js" > /dev/null

echo "Done! Remember to commit and push filenames.js if images were added or removed."
