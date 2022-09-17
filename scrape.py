import json
import re
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

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

proxies = {
    'http': 'socks5://127.0.0.1:1081/',
    'https': 'socks5://127.0.0.1:1081/',
}

def read_existing_list(filename: str='list.csv') -> dict:
    d = {}
    with open(filename, encoding='utf-8') as f:
        for line in f:
            title, post_url, video_url = line.rstrip('\n').split(',')
            d[title] = post_url, video_url
    return d

def get_video_url_from_content(content: str) -> str:
    if content:
        match = re.search(r'<video src="([^"]+)"[^<>]+>', content)
        if match:
            return match.group(1)
    return ''

def request_search(page: int) -> dict:
    d = {}

    payload = {
        'appInfoId': '32',
        'keyword': '《文昌新闻》海南话',
        'loginUserId': '',
        'pageNum': page,
        'pageSize': 10,
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers, proxies=proxies)
    r.raise_for_status()
    obj = r.json()
    assert obj['success']

    for item in obj['data'][0]['sprintList']:
        title = item['title']

        if '文昌新闻' in title and '海南话' in title:
            title = title.replace("<font color='red'>《文昌新闻》海南话</font>", '')

            match = re.search(r'(\d+)年(\d+)月(\d+)', title)
            if match:
                year, month, day = match.groups()
                title = f'{year}-{month:0>2}-{day:0>2}'

            post_url = item['url']
            post_url = post_url.replace('mixmedia/', '')

            content = item['content']

            video_url = get_video_url_from_content(content) or item['properties']['accessUrl']

            d[title] = post_url, video_url

    return d

def main():
    final_data = {**{k: v for page in range(20) for k, v in request_search(page).items()}, **read_existing_list()}
    final_data = sorted((title, post_url, video_url) for title, (post_url, video_url) in final_data.items())

    with open('list2.csv', 'w', encoding='utf-8') as f:
        for title, post_url, video_url in final_data:
            print(title, post_url, video_url, sep=',', file=f)

if __name__ == '__main__':
    main()
