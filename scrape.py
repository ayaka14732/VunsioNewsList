import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import json
import logging
import re

logging.basicConfig(level=logging.DEBUG)

num_pages = 20

url = 'http://hongqi.wengegroup.com:9001/search/searchUserSprint'

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'X-Requested-With': 'com.zkwg.wenchangnews',
    'app_info_id': '32',
    'Cookie': 'SESSION=ff7c6bee-1747-4316-be92-4ae6be1bb29c',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 9; INE-AL00 Build/HUAWEIINE-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.69 Mobile Safari/537.36 Html5Plus/1.0 (Immersed/35.294117)',
}

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

async def request_search(session: aiohttp.ClientSession, page: int) -> dict:
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
    r = await session.post(url, data=json.dumps(payload))
    r.raise_for_status()
    obj = await r.json()
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

async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for page in range(num_pages):
            task = request_search(session, page)
            tasks.append(task)
        res = await asyncio.gather(*tasks)
    d = {**{k: v for d in res for k, v in d.items()}, **read_list()}
    l = sorted((title, post_url, video_url) for title, (post_url, video_url) in d.items())
    write_list(l)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
