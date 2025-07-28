import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urldefrag
import os
import html
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
scraper = cloudscraper.create_scraper()
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


pages = set()
visited = set()
skipped = set()

def clean_text(text):
    
    clean_text = re.sub(r"\[\d*\]|\[\s*.*?\s*\]", "", html.unescape(text)).strip()
    return clean_text.strip()

def normalize_url(url):
    # Removes fragment (#...) from URL
    return urldefrag(url)[0]


def get_final_url(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        return response.url  # This is the final URL after all redirects
    except requests.RequestException as e:
        print(f"Error resolving URL {url}: {e}")
        return url  # Fallback to original if something fails

def parse_article(url):

    try:     
        response = scraper.get(url,timeout=10)
        print(f"Cloudscraper GET -> {response.status_code} for {url}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

    if response.status_code != 200:
        print(f"Failed to retrieve {url} after retry, status_code={response.status_code}")
        return None
    if response.status_code == 403 or response.status_code == 503 or response.status_code == 429:
        # Handle 403 Forbidden, 503 Service Unavailable, or 429 Too Many Requests
        print(f'{response.status_code} error, sleeping for 30 seconds')
        return 1


    soup = BeautifulSoup(response.content, "html.parser")
    content_div = soup.find("div", class_="mw-parser-output")
    if not content_div:
        print(f"No content found for {url}")
        return None

    title = soup.find("h1").text.strip()
    section = {"Introduction": ""}
    current_section = "Introduction"

    for child in content_div.children:
        if child.name == "div" and (
            "thumb" in child.get("class", []) or
            "navbox" in child.get("class", []) or
            "notice" in child.get("class", [])
        ):
            continue
        if child.name not in ['p','h2','h3','h4','h5','h6','ul','ol','li']:
            continue
        if child.name in ['h2','h3','h4','h5','h6','ul','ol']:
            hl = child.find('span', class_='mw-headline')
            current_section = hl.get_text().strip() if hl else clean_text(child.get_text())
            section[current_section] = ""
        elif child.name == "p":
            section[current_section] += clean_text(child.get_text()) + "\n"
        elif child.name in ["ul", "ol"]:
            items = [f"- {clean_text(li.get_text())}" for li in child.find_all("li")]
            section[current_section] += "\n".join(items) + "\n"
        
  # Remove irrelevant containers before link discovery
    for tag in content_div.select(".navbox, .catlinks, .reflist, .hatnote, .metadata, .mw-references-wrap"):
        tag.decompose()  # Remove them entirely from DOM

    # Now gather relevant internal links
    for child in content_div.find_all('a', href=True):
        link = child.get('href')
        if not link.startswith("/wiki/"):
            continue

        unwanted_prefixes = (
            '/wiki/File:',
            '/wiki/Category:',
            '/wiki/Help:',
            '/wiki/User:',
            '/wiki/User_talk:',
            '/wiki/Special:',
            '/wiki/Summary:',
            '/wiki/Template:',
            '/wiki/Template_talk:',
            '/wiki/Coppermind:',
            '/wiki/Illustrator:',
            '/wiki/Map:',
            '/wiki/Cite:',
            '/wiki/Help_talk:',
            '/wiki/Wikipedia:',
        )

        if link.startswith(unwanted_prefixes):
            continue

        if re.search(r'/Gallery$', link):
            continue

        full_url = normalize_url(urljoin(BASE_URL, link))
        if full_url not in pages and full_url not in visited and full_url not in skipped:
            pages.add(full_url)
            
    return {
        "title": title,
        "url": url,
        "sections": section
    }

def save_json_to_file(data):
    title_cleaned = re.sub(r'[\\/*?:"<>|]', "_", data['title'])
    base_filename = f"{title_cleaned.replace(' ', '_')}.json"
    
    folder = "data"
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = os.path.join(folder, base_filename)

    # Check for file existence in the correct folder
    if os.path.exists(filename):
        timestamp = int(time.time())
        filename = os.path.join(folder, f"{title_cleaned.replace(' ', '_')}_{timestamp}.json")

    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"File saved: {filename}")
        return True
    except Exception as e:
        print(f"Error saving {data['title']}: {e}")
        return False

if __name__ == "__main__":
    load_state()
    try:
        while pages:
            page = pages.pop()
            page = get_final_url(page)
            if '/wiki/Wikipedia:' in page:
                print('Skipping Wikipedia page')
                continue
            if page in visited or page in skipped:
                print(f"Already visited or skipped {page}.")
                continue
            data = parse_article(page)
            if data is None:
                skipped.add(page)
                print(f"Skipping {page} due to parsing error or no content.")
                continue
            if data == 1:
                pages.add(page) # Retry later
                print('Got rate limited or something. Retry later after sleeping for 30 seconds')
                time.sleep(random.randint(25,30))

            # Check if 'Introduction' section is empty
            if "Introduction" not in data["sections"] or not data["sections"]["Introduction"].strip():
                print(f"[!] Skipping {page} because 'Introduction' section was empty. Will retry later.")
                pages.add(page)  # Re-add to retry later
                time.sleep(random.uniform(3, 5))
                continue

            if save_json_to_file(data):
                visited.add(page)
            else:
                pages.add(page)
                print(f"Failed to save {data['title']}. Re-adding {page} to pages.")
            print(f"Currently visited: {len(visited)}, skipped: {len(skipped)}, remaining: {len(pages)}")
            time.sleep(random.uniform(0.5, 1))
            
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        save_state()
        print("Crawl state saved.")

