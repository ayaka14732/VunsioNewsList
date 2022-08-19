from bs4 import BeautifulSoup
import re
import requests
from typing import Optional

def page_html2video_url(page_html: str) -> Optional[str]:
    match = re.search(r'function \(\) {createPlayer\("video:\/\/vid:([0-9a-f]+)","[^"]+","(\d{4}-\d{2}-\d{2})","[^"]+","[^"]+"\)}', page_html)
    if match:
        video_id, date_str = match.groups()
        date_str = date_str.replace('-', '/')
        video_url = f'http://v8.gdmztv.com:8082/mzt/vod/{date_str}/{video_id}/h264_1200k_mp4.mp4'
        return video_url

    match = re.search(r'<param name="flashvars" value="file=([^&"]+)&amp;coverImg=[^&"]+&amp;autoStart=1" \/>', page_html)
    if match:
        video_url = match.group(1)
        return video_url

def scrape_list_page(list_url: str) -> None:
    response = requests.get(list_url)
    response.raise_for_status()
    response.encoding = 'utf-8'
    html_str = response.text

    for li in BeautifulSoup(html_str, features='html.parser').select('.videolist ul li'):
        a = li.select_one('a')

        title = a['title']

        if '完整版' in title:
            post_url = a['href']

            response = requests.get(post_url)
            response.raise_for_status()
            page_html = response.text

            video_url = page_html2video_url(page_html)

            print(title, post_url, video_url, sep='\t')

if __name__ == '__main__':
    for i in range(1, 86 + 1):
        list_url = f'http://news.gdmztv.com/service900/{i}.shtml'
        scrape_list_page(list_url)
