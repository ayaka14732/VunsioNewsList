import base64
from datetime import datetime
import json
import logging
import re
import time

from bs4 import BeautifulSoup
import requests

logging.basicConfig(level=logging.DEBUG)

num_pages = 1

url = 'http://hongqi.wengegroup.com/activities/search/searchUserSprint'

def custom_base64(s):
    # UTF-8 encode then standard base64
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')

def make_sign(url, method, timestamp=None):
    if timestamp is None:
        timestamp = int(time.time() * 1000)

    payload = json.dumps({"url": url, "timestamp": timestamp, "method": method}, separators=(',', ':'))

    # Step 1: base64
    t = list(custom_base64(payload))
    n = len(t) // 2

    # Step 2: swap with steps [6, 2, 8, 3]
    for step in [6, 2, 8, 3]:
        for i in range(0, n, step):
            t[i], t[n + i] = t[n + i], t[i]

    return ''.join(t)

def generate_headers():
    sign = make_sign("search/searchUserSprint", "post")
    headers = {
        'Host': 'hongqi.wengegroup.com',
        'Proxy-Connection': 'keep-alive',
        'sign': sign,
        'app_info_id': '32',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 16; sdk_gphone64_x86_64 Build/BE4B.251210.005; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.135 Mobile Safari/537.36 Html5Plus/1.0 (Immersed/24.0)',
        'X-Requested-With': 'com.zkwg.wenchangnews',
        'Accept-Language': 'en-US,en;q=0.5',
        'Cookie': 'SESSION=6129f918-7aed-452e-bea0-f527422ebbce',
    }
    return headers

def remove_html_tags(html_text: str) -> str:
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text()

def read_list(filename: str='list.csv') -> dict:
    d = {}
    with open(filename, encoding='utf-8') as f:
        for line in f:
            title, post_url, video_url = line.rstrip('\n').split(',')
            d[title] = post_url, video_url
    return d

def write_list(l: list) -> None:
    with open('list.csv', 'w', encoding='utf-8') as f:
        for title, post_url, video_url in l:
            print(title, post_url, video_url, sep=',', file=f)

def get_video_url_from_content(content: str) -> str | None:
    if not content:
        return
    soup = BeautifulSoup(content, 'html.parser')
    video_tag = soup.find('video')
    if not video_tag:
        return
    video_src = video_tag.get('src')
    if not video_src:
        return
    return video_src

def determine_title(item) -> str:
    title = remove_html_tags(item['title'])

    if '《文昌新闻》' in title and '海南话' in title:
        match = re.search(r'(\d+)年(\d+)月(\d+)', title)
        if match:
            year, month, day = match.groups()
            return f'{year}-{month:0>2}-{day:0>2}'

        match = re.search(r'(\d+)月(\d+)', title)
        if match:
            match = re.search(r'(\d+)月(\d+)', title)
            month, day = match.groups()
            year = datetime.strptime(item['pubDate'], "%Y-%m-%d %H:%M:%S").year
            return f'{year}-{month:0>2}-{day:0>2}'

    return title

def request_search(page: int, headers) -> dict:
    d = {}

    payload = {
        'appInfoId': '32',
        'loginUserId': '',
        'pageNum': page,
        'pageSize': 10,
        'title': '《文昌新闻》海南话',
        'content': '',
        'columnId': '',
        'startTime': '2023-06-01T00:00:00',
    }

    logging.debug(f'Requesting page {page}...')
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    r.raise_for_status()
    obj = r.json()
    assert obj['success']
    logging.debug(f'Requesting page {page} done')

    for item in obj['data'][0]['sprintList']:
            title = determine_title(item)

            post_url = item['url']
            post_url = post_url.replace('mixmedia/', '')

            content = item['content']

            video_url = get_video_url_from_content(content) or item['properties'].get('accessUrl')
            if not video_url:
                continue

            d[title] = post_url, video_url

    return d

def main():
    d = {}

    for page in range(num_pages):
        headers = generate_headers()
        res = request_search(page, headers)
        d.update(res)

        time.sleep(4)  # Pace requests to avoid scraping too quickly.

    d = {**d, **read_list()}
    l = sorted((title, post_url, video_url) for title, (post_url, video_url) in d.items())
    write_list(l)

if __name__ == "__main__":
    main()
