# 文昌新闻视频列表

<https://www.youtube.com/@vunsio-news>

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
8 23 * * * /path/to/dir/update.sh
```
