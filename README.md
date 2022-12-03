# 文昌新闻视频列表

<https://www.youtube.com/@vunsio-news>

Update:

```sh
git diff -U0 list.csv | grep '^[+-]' | grep -Ev '^(--- a/|\+\+\+ b/)' | sed 's/^[+]//g' | perl -pe 's/^(\d+)-(\d+)-(\d+),(.+),(.+)$/aria2c -x16 -s16 -c -o \1\2\3.mp4 \5/g'
```
