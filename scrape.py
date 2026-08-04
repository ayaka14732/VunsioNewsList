import argparse
import base64
import csv
from datetime import date, datetime
import json
import logging
import re
import time
from typing import Any

from bs4 import BeautifulSoup
import requests

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DEFAULT_NUM_PAGES = 1
PAGE_SIZE = 10
REQUEST_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 30
LIST_FILENAME = 'list.csv'
SEARCH_URL = 'http://hongqi.wengegroup.com/activities/search/searchUserSprint'
SEARCH_TITLE = '文昌新闻 海南话'
START_TIME = '2023-06-01T00:00:00'
FULL_DATE_PATTERN = re.compile(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?')
MISTYPED_DATE_PATTERN = re.compile(r'(\d{4})\s*年\s*(\d{1,2})\s*日\s*(\d{1,2})\s*日')
SHORT_DATE_PATTERN = re.compile(r'(\d{1,2})\s*月\s*(\d{1,2})\s*日?')
ISO_DATE_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}')

def custom_base64(value: str) -> str:
    return base64.b64encode(value.encode('utf-8')).decode('ascii')

def make_sign(url: str, method: str, timestamp: int | None = None) -> str:
    if timestamp is None:
        timestamp = int(time.time() * 1000)

    payload = json.dumps({'url': url, 'timestamp': timestamp, 'method': method}, separators=(',', ':'))
    encoded = list(custom_base64(payload))
    midpoint = len(encoded) // 2

    for step in (6, 2, 8, 3):
        for index in range(0, midpoint, step):
            encoded[index], encoded[midpoint + index] = encoded[midpoint + index], encoded[index]

    return ''.join(encoded)

def generate_headers() -> dict[str, str]:
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
    return soup.get_text(separator='', strip=True)

def read_list(filename: str = LIST_FILENAME) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    with open(filename, encoding='utf-8') as file:
        for line_number, row in enumerate(csv.reader(file), start=1):
            if len(row) != 3:
                raise ValueError(f'{filename}:{line_number}: expected 3 columns, got {len(row)}')
            title, post_url, video_url = row
            if not ISO_DATE_PATTERN.fullmatch(title) and '文昌新闻' in title and '海南话' in title:
                normalized_title = normalize_news_title(title)
                if normalized_title:
                    title = normalized_title
            entries[title] = post_url, video_url
    return entries

def write_list(entries: list[tuple[str, str, str]], filename: str = LIST_FILENAME) -> None:
    with open(filename, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerows(entries)

def get_video_url_from_content(content: str) -> str | None:
    if not content:
        return None

    soup = BeautifulSoup(content, 'html.parser')
    video_tag = soup.find('video')
    if not video_tag:
        return None

    video_url = video_tag.get('src')
    if isinstance(video_url, str):
        return video_url

    source_tag = video_tag.find('source')
    if source_tag:
        source_url = source_tag.get('src')
        if isinstance(source_url, str):
            return source_url
    return None

def normalize_news_title(title: str, published_at: str | None = None) -> str | None:
    compact_title = re.sub(r'\s+', '', title)
    if '文昌新闻' not in compact_title or '海南话' not in compact_title or '普通话' in compact_title:
        return None

    explicit_date_match = FULL_DATE_PATTERN.search(title) or MISTYPED_DATE_PATTERN.search(title)
    if explicit_date_match:
        year, month, day = (int(part) for part in explicit_date_match.groups())
    else:
        match = SHORT_DATE_PATTERN.search(title)
        if not match:
            return None
        if published_at is None:
            return None
        month, day = (int(part) for part in match.groups())

    try:
        if explicit_date_match:
            return date(year, month, day).isoformat()
        assert published_at is not None
        published_date = datetime.fromisoformat(published_at).date()
        year = published_date.year
        normalized_date = date(year, month, day)
        if (normalized_date - published_date).days > 180:
            normalized_date = date(year - 1, month, day)
        elif (published_date - normalized_date).days > 180:
            normalized_date = date(year + 1, month, day)
        return normalized_date.isoformat()
    except (TypeError, ValueError):
        return None

def determine_title(item: dict[str, Any]) -> str | None:
    title = remove_html_tags(item.get('title', ''))
    return normalize_news_title(title, item.get('pubDate'))

def request_search(page: int, session: requests.Session) -> tuple[dict[str, tuple[str, str]], int]:
    payload: dict[str, Any] = {
        'appInfoId': '32',
        'loginUserId': '',
        'pageNum': page,
        'pageSize': PAGE_SIZE,
        'title': SEARCH_TITLE,
        'content': '',
        'columnId': '',
        'startTime': START_TIME,
    }

    logging.info('Requesting page %d', page + 1)
    response = session.post(SEARCH_URL, headers=generate_headers(), json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    result = response.json()
    if not result.get('success'):
        raise RuntimeError(f'Search request failed: {result.get("message", result)}')

    data = result.get('data')
    if not data or not isinstance(data[0], dict):
        raise RuntimeError('Search response did not contain the expected data')
    items = data[0].get('sprintList') or []
    entries: dict[str, tuple[str, str]] = {}

    for item in items:
        title = determine_title(item)
        if title is None:
            continue

        post_url = item.get('url')
        if not post_url:
            continue
        post_url = post_url.replace('mixmedia/', '')

        properties = item.get('properties') or {}
        video_url = get_video_url_from_content(item.get('content', '')) or properties.get('accessUrl')
        if not video_url:
            continue
        entries.setdefault(title, (post_url, video_url))

    return entries, len(items)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Update the Wenchang Hainanese news video list.')
    parser.add_argument('--num-pages', type=int, default=DEFAULT_NUM_PAGES, help=f'Number of newest search pages to fetch (default: {DEFAULT_NUM_PAGES}, {PAGE_SIZE} items per page).')
    args = parser.parse_args()
    if args.num_pages < 1:
        parser.error('--num-pages must be at least 1')
    return args

def main() -> None:
    args = parse_args()
    existing_entries = read_list()
    scraped_entries: dict[str, tuple[str, str]] = {}

    with requests.Session() as session:
        for page in range(args.num_pages):
            if page:
                time.sleep(REQUEST_DELAY_SECONDS)
            page_entries, item_count = request_search(page, session)
            for title, urls in page_entries.items():
                scraped_entries.setdefault(title, urls)
            if item_count < PAGE_SIZE:
                break

    new_titles = scraped_entries.keys() - existing_entries.keys()
    combined_entries = {**scraped_entries, **existing_entries}
    rows = sorted((title, post_url, video_url) for title, (post_url, video_url) in combined_entries.items())
    write_list(rows)

if __name__ == '__main__':
    main()
