import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import time
import html

BASE_URL = "https://coppermind.net/wiki/Kaladin"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://coppermind.net"
}

# create a session so headers/cookies persist
session = requests.Session()
session.headers.update(HEADERS)

pages = set()

def clean_text(text):
    # Remove citation brackets [1] and edit markers [edit]
    clean_text = html.unescape(text)
    clean_text = re.sub(r"\[\d*\]|\[\s*.*?\s*\]", "", html.unescape(clean_text)).strip()
    return clean_text.strip()

def parse_article(url):
    try:
        response = session.get(url, timeout=10)
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

    print(f"GET {url} -> {response.status_code}")
    if response.status_code != 200:
        # optional: fallback with cloudscraper if Cloudflare is blocking you
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            print(f"Cloudscraper GET -> {response.status_code}")
        except ImportError:
            pass

    if response.status_code != 200:
        print(f"Failed to retrieve {url} after retry, status_code={response.status_code}")
        return None

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
        if child.name in ['h2','h3']:
            hl = child.find('span', class_='mw-headline')
            current_section = hl.get_text().strip() if hl else clean_text(child.get_text())
            section[current_section] = ""
        elif child.name == "p":
            section[current_section] += clean_text(child.get_text()) + "\n"
        elif child.name in ["ul", "ol"]:
            items = [f"- {clean_text(li.get_text())}" for li in child.find_all("li")]
            section[current_section] += "\n".join(items) + "\n"

    return {
        "title": title,
        "url": url,
        "sections": section
    }

def save_json_to_file(data):
    """
    Saves a JSON object to a file.

    Args:
        data: The JSON object (dict or list) to save.
        filename: The name of the file to save to.
    """
    filename = f"{data['title'].replace(' ', '_')}.json"
    with open(filename, 'w') as file:

        json.dump(data, file, indent=4)

if __name__ == "__main__":
    save_json_to_file(parse_article(BASE_URL))

    