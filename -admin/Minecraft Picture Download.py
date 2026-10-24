# -*- coding: utf-8 -*-
"""
Download block and item icons from the Minecraft Wiki, naming each file after
its display name (extension preserved).

Pages:
    - Blocks: https://minecraft.wiki/w/Block  (images are in the #List_of_blocks section)
    - Items:  https://minecraft.wiki/w/Item   (images are in the #Lists_of_items section)

Output:
    All images are saved flat into {target folder}; duplicate names get a _2/_3 suffix.

Usage:
    python "Minecraft Picture Download.py" [target folder]

Dependencies:
    pip install curl_cffi beautifulsoup4

Notes:
    The wiki is protected by Cloudflare, so plain requests/urllib gets blocked.
    curl_cffi is used to impersonate a real Chrome TLS fingerprint.
"""

import os
import re
import sys
import time

PAGES = [
    {"name": "Blocks",
     "url": "https://minecraft.wiki/w/Block",
     "section": "List_of_blocks"},
    {"name": "Items",
     "url": "https://minecraft.wiki/w/Item",
     "section": "Lists_of_items"},
]

BASE_URL = "https://minecraft.wiki"
# Declare PNG in the Accept header so Cloudflare Polish does not convert originals to WebP
IMAGE_HEADERS = {
    "Accept": "image/png,image/jpeg,image/*;q=0.8,*/*;q=0.5",
    "Referer": PAGES[0]["url"],
}
MAX_RETRY = 3            # retries per failed request
DOWNLOAD_INTERVAL = 0.05  # delay between downloads to avoid hammering the server


def ensure_dependencies():
    """Check for and report missing dependencies."""
    missing = []
    try:
        import curl_cffi  # noqa: F401
    except ImportError:
        missing.append("curl_cffi")
    try:
        import bs4  # noqa: F401
    except ImportError:
        missing.append("beautifulsoup4")
    if missing:
        print("Missing dependencies: " + ", ".join(missing))
        print("Please run: pip install " + " ".join(missing))
        sys.exit(1)


def sanitize_filename(name: str) -> str:
    """Strip characters that are illegal in Windows file names."""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "", name).strip().strip(". ")
    return name[:150] or "untitled"


def detect_ext(data: bytes) -> str:
    """Detect the real format from the file signature (guards against mismatched extensions)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"GIF8":
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:5] == b"<?xml" or b"<svg" in data[:200]:
        return ".svg"
    return ""  # unknown format


def fetch_page(session, url):
    """Fetch the page HTML with a few retries."""
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = session.get(url, impersonate="chrome", timeout=60)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"    Page fetch failed (attempt {attempt}/{MAX_RETRY}): {e}")
            if attempt < MAX_RETRY:
                time.sleep(3)
    return None


def parse_items(html, section_id):
    """
    Parse the gallery lists (one or more div-col blocks) inside #section_id and
    return [(display name, original image filename), ...].
    The name is taken from span.sprite-text first, falling back to the link title.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    section = soup.find(id=section_id)
    if section is None:
        print(f"    Section #{section_id} not found; the page layout may have changed.")
        return []

    # The first h2 with an id after this section marks the end of the collection range
    end = None
    for h in section.find_all_next("h2"):
        if h.get("id"):
            end = h
            break

    items = []
    for el in section.find_all_next():
        if end is not None and el is end:
            break
        if el.name == "div" and "div-col" in (el.get("class") or []):
            ul = el.find("ul")
            if ul is None:
                continue
            for li in ul.find_all("li"):
                name = None
                sprite = li.find("span", class_="sprite-text")
                if sprite:
                    name = sprite.get_text(strip=True)
                else:
                    for a in li.find_all("a", title=True):
                        if not a.get("href", "").startswith("/w/File:"):
                            name = a.get("title", "").strip()
                            break
                img = li.find("img")
                if not name or img is None:
                    continue

                # Extract the original filename from the thumbnail/sprite src
                src = img.get("src", "")
                m = re.search(r"/thumb/([^/?]+)/", src)
                if not m:
                    m = re.search(r"/images/([^/?]+)", src)
                if not m:
                    continue

                items.append((name, m.group(1)))

    return items


def download_one(session, name, image_file, folder, used):
    """Download one original image and save it as "name.ext". Returns the path or None."""
    ext_src = os.path.splitext(image_file)[1].lower() or ".png"
    url = f"{BASE_URL}/images/{image_file}"

    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = session.get(url, impersonate="chrome", headers=IMAGE_HEADERS, timeout=60)
            resp.raise_for_status()
            data = resp.content
            if len(data) < 100:  # too small to be a real image
                raise ValueError(f"Response too small ({len(data)} bytes)")
            break
        except Exception as e:
            if attempt < MAX_RETRY:
                time.sleep(1)
            else:
                print(f"    Download failed {image_file}: {e}")
                return None

    real_ext = detect_ext(data)
    if real_ext:
        ext = real_ext
    elif resp.headers.get("Content-Type", "").startswith("image/"):
        ext = "." + resp.headers["Content-Type"].split("/")[1].split(";")[0]
    else:
        ext = ext_src

    filename = sanitize_filename(name) + ext
    # Duplicate names within one run (e.g. several variants of the same item) get a _2/_3 suffix
    if filename in used:
        base, e = os.path.splitext(filename)
        n = 2
        while f"{base}_{n}{e}" in used:
            n += 1
        filename = f"{base}_{n}{e}"
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(data)
    used.add(filename)
    return path


def download_page(session, page, base_folder, used):
    """Download every image of a single page into base_folder."""
    print(f"\n=== {page['name']} ===")
    print(f"    Target folder: {base_folder}")

    html = fetch_page(session, page["url"])
    if html is None:
        print("    Failed to fetch the page; skipping it.")
        return

    items = parse_items(html, page["section"])
    if not items:
        print("    No entries were parsed.")
        return

    print(f"    Parsed {len(items)} entries, downloading ...")
    ok = 0
    failed = []
    total = len(items)
    for i, (name, image_file) in enumerate(items, 1):
        path = download_one(session, name, image_file, base_folder, used)
        if path:
            ok += 1
            print(f"    [{i}/{total}] {os.path.basename(path)}")
        else:
            failed.append((name, image_file))
            print(f"    [{i}/{total}] FAILED: {name} ({image_file})")
        time.sleep(DOWNLOAD_INTERVAL)

    print(f"    Done: {ok}/{total} succeeded", end="")
    if failed:
        print(f", {len(failed)} failed:")
        for name, f in failed:
            print(f"        {name} -> {f}")
    else:
        print()


def main():
    ensure_dependencies()
    from curl_cffi import requests as cffi_requests

    base_folder = sys.argv[1] if len(sys.argv) > 1 else r"C:\Shinlinst\Software\-data\Minecraft Picture Download"
    os.makedirs(base_folder, exist_ok=True)
    print(f"Storage root: {base_folder}")

    session = cffi_requests.Session()
    used = set()  # filenames used across all pages, so duplicates get suffixes instead of overwriting
    for page in PAGES:
        download_page(session, page, base_folder, used)

    print("\nAll done.")


if __name__ == "__main__":
    main()
