#!/usr/bin/env python3
import json
import math
import os
import re
import urllib.request
from pathlib import Path

USER_ID = "105903487"
QUOTES_URL = f"https://www.goodreads.com/quotes/list/{USER_ID}"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

PER_PAGE = 30


def fetch_page(page):
    url = f"{QUOTES_URL}?page={page}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return None


def find_matching_div_end(text, start):
    """Find the matching </div> for a <div> starting at position `start`.
    Returns the position right after the closing </div>, or -1."""
    i = start
    depth = 0
    # Find positions of all <div and </div
    pattern = re.compile(r"</?div\b[^>]*>", re.IGNORECASE)
    for m in pattern.finditer(text, i):
        tag = m.group()
        if tag.startswith("</"):
            depth -= 1
            if depth == 0:
                return m.end()
        else:
            depth += 1
    return -1


def parse_quotes(html):
    quotes = []
    # Each quote is in an <li class="gr-d-flex elementList ">
    li_pattern = re.compile(
        r'<li[^>]*class="gr-d-flex elementList[^"]*"[^>]*>(.*?)</li>', re.DOTALL
    )
    for li_match in li_pattern.finditer(html):
        li_content = li_match.group(1)

        # Extract quote number
        num_match = re.search(
            r'<div class="leftAlignedImage">\s*#(\d+)\s*</div>', li_content, re.DOTALL
        )
        number = int(num_match.group(1)) if num_match else 0

        # Extract quoteText
        qtext_match = re.search(r'<div class="quoteText">(.*?)</div>', li_content, re.DOTALL)
        if not qtext_match:
            continue
        text_html = qtext_match.group(1)

        quote_text = extract_quote_text(text_html)
        author, book = extract_author_book(text_html)

        # Extract quoteFooter (handle nested divs)
        footer_start = li_content.find('<div class="quoteFooter">')
        if footer_start >= 0:
            footer_end = find_matching_div_end(li_content, footer_start)
            if footer_end > 0:
                footer_html = li_content[footer_start:footer_end]
            else:
                footer_html = ""
        else:
            footer_html = ""

        tags = extract_tags(footer_html)
        likes, quote_url = extract_likes(footer_html)

        quotes.append(
            {
                "quote": quote_text,
                "author": author,
                "book": book,
                "tags": tags,
                "likes": likes,
                "url": quote_url,
            }
        )
    return quotes


def extract_quote_text(text_html):
    m = re.search(r"&ldquo;(.*?)&rdquo;", text_html, re.DOTALL)
    if m:
        text = m.group(1).strip()
        text = re.sub(r"<br\s*/?>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text
    return ""


def extract_author_book(text_html):
    author = ""
    book = ""

    author_spans = re.findall(
        r'<span class="authorOrTitle">\s*(.*?)\s*</span>', text_html, re.DOTALL
    )
    for span_text in author_spans:
        text = re.sub(r"<[^>]*>", "", span_text).strip()
        if text:
            if text.endswith(","):
                text = text[:-1].strip()
            if text:
                author = text
                break

    book_match = re.search(
        r'<span[^>]*id=quote_book_link_\d+[^>]*>.*?<a[^>]*class="authorOrTitle"[^>]*>(.*?)</a>',
        text_html,
        re.DOTALL,
    )
    if book_match:
        book = re.sub(r"<[^>]*>", "", book_match.group(1)).strip()

    return author, book


def extract_tags(footer_html):
    return re.findall(
        r'<a href="/quotes/tag/[^"]*">\s*(.*?)\s*</a>', footer_html, re.DOTALL
    )


def extract_likes(footer_html):
    m = re.search(
        r'<a\s+class="smallText"[^>]*href="/quotes/([^"]*)"[^>]*>\s*(\d+)\s+likes?\s*</a>',
        footer_html,
        re.DOTALL,
    )
    if m:
        return int(m.group(2)), f"https://www.goodreads.com/quotes/{m.group(1)}"
    return 0, ""


def get_total_quotes(html):
    m = re.search(r"Showing \d+[–-]\d+ of (\d+)", html)
    if m:
        return int(m.group(1))
    return 0


def fetch_quotes():
    print("Fetching first page to determine total...")
    html = fetch_page(1)
    if not html:
        print("Failed to fetch first page")
        return

    total = get_total_quotes(html)
    pages = max(1, math.ceil(total / PER_PAGE))
    print(f"Found {total} quotes across {pages} pages")

    all_quotes = []
    for page in range(1, pages + 1):
        if page == 1:
            page_html = html
        else:
            print(f"  Fetching page {page}/{pages}...")
            page_html = fetch_page(page)
            if not page_html:
                print(f"  Failed to fetch page {page}, stopping")
                break

        quotes = parse_quotes(page_html)
        print(f"  Page {page}: parsed {len(quotes)} quotes")
        all_quotes.extend(quotes)

    seen = set()
    unique = []
    for q in all_quotes:
        key = q["quote"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(q)

    print(f"Total unique quotes: {len(unique)}")

    out = Path("./data/non-public/quotes.json")
    out.write_text(json.dumps(unique, indent=2) + "\n")
    print(f"Quotes saved to {out}")


if __name__ == "__main__":
    fetch_quotes()
