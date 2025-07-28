import requests

import json


import os

import time
import random
import atexit
import cloudscraper


BASE_URL = "https://coppermind.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://coppermind.net"
}

STATE_FILE = "crawl_state.json"

def load_state():
    global pages, visited, skipped
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            pages = set(data.get("pages", []))
            visited = set(data.get("visited", []))
            skipped = set(data.get("skipped", []))
    else:
        pages.add(BASE_URL + "/wiki/Kaladin")

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump({
            "pages": list(pages),
            "visited": list(visited),
            "skipped": list(skipped),
        }, f, indent=2)

atexit.register(save_state)

# create a session so headers/cookies persist
session = requests.Session()
session.headers.update(HEADERS)
scraper = cloudscraper.create_scraper()
def parse_article(url):
    try: 
                response = scraper.get(url)
                print(f"Cloudscraper GET -> {response.status_code}")
                if response.status_code == 200:
                    print('will be saved back...')
                    return 1
                elif response.status_code == 403 or response.status_code == 503 or response.status_code == 429:
                    # Handle 403 Forbidden, 503 Service Unavailable, or 429 Too Many Requests
                    time.sleep(random.randint(30))
                    print(f'{response.status_code}  error, sleeping for 30 seconds')
                    return 1
                else:
                    print('will be removed')
                    return None

    except Exception as e:
        print(f"Request failed for {url}: {e}")
        return None

def crawl_pages():
    # process all pages set
    for page in list(pages):
        pages.remove(page)
        if page in visited or page in skipped:
            print(f"Already visited or skipped {page}.")
            continue
        result = parse_article(page)
        if result is None:
            skipped.add(page)
            print(f"Skipping {page}.")
        else:
            pages.add(page)
            visited.add(page)
            print(f"Retained {page} for retry.")
    save_state()
    print(f"crawl_pages done. Visited: {len(visited)}, Skipped: {len(skipped)}, Remaining pages: {len(pages)}")


def retry_skipped():
    # retry all skipped links
    print("Retrying skipped pages...")
    for page in list(skipped):
        if page in pages:
            continue
        result = parse_article(page)
        if result is not None:
            skipped.remove(page)
            pages.add(page)
            print(f"Page {page} reachable. Added back to pages.")
        else:
            print(f"Page {page} still failing.")
    save_state()
    print(f"retry_skipped done. Visited: {len(visited)}, Skipped: {len(skipped)}, Remaining pages: {len(pages)}")

if __name__ == "__main__":
    load_state()
    
    retry_skipped()
    

