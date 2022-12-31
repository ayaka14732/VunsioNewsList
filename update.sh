#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

. .env
. venv/bin/activate

python scrape.py

GIT_CHANGED=$(git status --porcelain)
if [[ $GIT_CHANGED ]]; then
    RESULT=$(git diff -U0 list.csv | grep '^[+-]' | grep -Ev '^(--- a/|\+\+\+ b/)' | sed 's/^[+]//g' | perl -pe 's/^(\d+)-(\d+)-(\d+),(.+),(.+)$/aria2c -x16 -s16 -c -o \1\2\3.mp4 \5/g')

    curl "https://api.telegram.org/$BOT_TOKEN/sendMessage" -d "chat_id=$CHAT_ID" -d "text=\`\`\`
$RESULT
\`\`\`" -d 'parse_mode=MarkdownV2'

    git add .
    git commit -m 'Update list' --author "github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"
    git push -u origin main
fi
