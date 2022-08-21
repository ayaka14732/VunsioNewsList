import json
import re
import requests

def determine_video_url(content):
    if content:
        match = re.search(r'<video src="([^"]+)"[^<>]+>', content)
        if match:
            return match.group(1)
    return ''

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

for page_num in range(6):  # range(124, 300)
    payload = {
        'appInfoId': '32',
        'keyword': '《文昌新闻》海南话',
        'loginUserId': '',
        'pageNum': page_num,
        'pageSize': 10,
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers)
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

            video_url = determine_video_url(content) or item['properties']['accessUrl']

            print(title, post_url, video_url, sep=',')
