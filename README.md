# List of daily news videos in Wenchang Hainanese

文昌海南话新闻视频列表

This repository contains the following contents:

1. A list of daily news videos in Wenchang Hainanese
1. A script to automatically fetch new videos from the offical website
1. A Telegram bot to automatically push updates to a designated Telegram channel

The videos are manually published on [YouTube](https://www.youtube.com/@vunsio-news).

Setup:

```sh
python -m venv venv
. venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Copy `.env.template` to `.env`, and edit.

Add to cron:

```
35 6 * * * /path/to/dir/update.sh
```
