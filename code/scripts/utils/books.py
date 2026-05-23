#!/usr/bin/env python3
import json
import re
import urllib.request

SHELVES = ["currently-reading", "read", "curated"]


def get_books(shelf):
    url = f"https://www.goodreads.com/review/list_rss/105903487?shelf={shelf}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml = resp.read().decode("utf-8")
        return parse_books(xml)
    except Exception as e:
        print(f"Error fetching books for shelf {shelf}: {e}")
        return []


def parse_books(xml):
    books = []
    for item_match in re.finditer(r"<item>([\s\S]*?)</item>", xml):
        content = item_match.group(1)

        title_m = re.search(r"<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</title>", content)
        link_m = re.search(r"<link>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</link>", content)
        image_m = re.search(
            r"<book_large_image_url>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</book_large_image_url>",
            content,
        ) or re.search(
            r"<book_image_url>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</book_image_url>",
            content,
        )
        author_m = re.search(
            r"<author_name>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</author_name>",
            content,
        )
        rating_m = re.search(
            r"<user_rating>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</user_rating>",
            content,
        )
        desc_m = re.search(
            r"<book_description>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</book_description>",
            content,
        )
        pub_date_m = re.search(
            r"<pubDate>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</pubDate>",
            content,
        )

        if title_m and link_m and image_m and author_m:
            book = {
                "title": title_m.group(1).strip(),
                "link": link_m.group(1).strip(),
                "imageUrl": image_m.group(1).strip(),
                "author": author_m.group(1).strip(),
            }
            if rating_m:
                book["rating"] = rating_m.group(1).strip()
            if desc_m:
                book["description"] = re.sub(r"<[^>]*>", "", desc_m.group(1)).strip()
            if pub_date_m:
                book["pubDate"] = pub_date_m.group(1).strip()
            books.append(book)

    return books


def fetch_books():
    books_data = {}
    for shelf in SHELVES:
        print(f"Fetching books for shelf: {shelf}")
        books_data[shelf] = get_books(shelf)

    with open("./data/non-public/books.json", "w") as f:
        json.dump(books_data, f, indent=2)
    print("Books data saved to ./data/non-public/books.json")


if __name__ == "__main__":
    fetch_books()
