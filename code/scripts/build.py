#!/usr/bin/env python3
"""Static site generator for prakashsellathurai.com."""

import json
import logging
import os
import pathlib
import re
import shutil
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from nbconvert import HTMLExporter
from nbformat import v4 as nbf, reads, NO_CONVERT

from lib.datatypes import (
    Book,
    Essay,
    ExperimentTopic,
    FileData,
    NoteTopic,
    Project,
    Quote,
    SiteMetadata,
)
from lib.frontmatter import parse_frontmatter
from lib.markdown import MarkdownRenderer, escape_html
from lib.slug import slug
from lib.xmlgen import generate_rss_feed, generate_sitemap

_logger = logging.getLogger(__name__)

BASE_PATH = os.environ.get("BASE_PATH", "")
OUT_DIR = pathlib.Path("out")
NOTES_DIR = pathlib.Path("data/non-public/submodules/Grimoire/notes")
EXPERIMENTS_DIR = pathlib.Path("data/non-public/submodules/Grimoire/experiments")
_ALLOWED_EXTS = {".txt", ".py", ".c", ".md", ".ipynb"}

_DOCS_EXTRA_CSS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">\n'
    '  <link rel="stylesheet" href="/static/css/docs.css">'
)
_DOCS_GITBOOK_EXTRA_CSS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">\n'
    '  <link rel="stylesheet" href="/static/css/docs.css">\n'
    '  <link rel="stylesheet" href="/static/css/gitbook-markdown.css">'
)
_PAGE_NAMES = {
    "/essays/": "Essays",
    "/about.html": "About",
    "/projects.html": "Projects",
    "/bookshelf.html": "Bookshelf",
    "/notes/": "Notes",
    "/tags/": "Tags",
    "/experiments/": "Experiments",
}


def _parse_date(date_str: str) -> datetime:
    """Parse an ISO date string (with optional trailing 'Z') to datetime."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def _format_date_iso(date_str: str) -> str:
    """Format a date string as ISO 8601 for structured data."""
    return _parse_date(date_str).isoformat()


def _format_date(date_str: str) -> str:
    """Format a date string for human display (e.g. 'Aug 07, 2026')."""
    return _parse_date(date_str).strftime("%b %d, %Y")


def _build_author_schema(metadata: SiteMetadata) -> dict:
    details = metadata.get("authorDetails", {})
    author = {"@type": "Person", "name": metadata["author"]}
    for key in ("url", "sameAs", "email", "jobTitle", "image"):
        if key in details:
            author[key] = details[key]
    return author


def _website_schema(site_url: str, site_title: str) -> dict:
    """Build the WebSite structured-data entry for a page's JSON-LD graph."""
    return {
        "@type": "WebSite",
        "url": site_url + "/",
        "name": site_title,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": site_url + "/?q={search_term_string}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def _person_schema(metadata: SiteMetadata, site_url: str) -> dict:
    """Build the Person structured-data entry for a page's JSON-LD graph."""
    details = metadata.get("authorDetails", {})
    person = {
        "@type": "Person",
        "name": metadata.get("author", ""),
        "url": site_url,
        "sameAs": details.get("sameAs", []),
        "jobTitle": details.get("jobTitle", "Software Engineer"),
        "description": metadata.get("description", ""),
    }
    author_img = details.get("image") or metadata.get("siteLogo", "")
    if author_img:
        person["image"] = site_url + author_img
    email = metadata.get("email")
    if email:
        person["email"] = email
    knows_about = details.get("knowsAbout")
    if knows_about:
        person["knowsAbout"] = knows_about
    return person


def _blog_posting_schema(metadata: SiteMetadata, essay: Essay, site_url: str, essay_url: str) -> dict:
    """Build the BlogPosting structured-data entry for an essay page."""
    return {
        "@type": "BlogPosting",
        "headline": essay["title"],
        "description": essay.get("summary", ""),
        "datePublished": _format_date_iso(essay["date"]),
        "dateModified": _format_date_iso(essay["date"]),
        "author": _build_author_schema(metadata),
        "url": site_url + essay_url,
        "image": site_url
        + (metadata.get("socialBanner") or metadata.get("siteLogo", "")),
        "mainEntityOfPage": {"@type": "WebPage", "@id": site_url + essay_url},
    }


def _main_entity_schema(metadata: SiteMetadata, site_url: str) -> dict:
    """Build the Person entity used as mainEntity in the About page schema."""
    author_details = metadata.get("authorDetails", {})
    main_entity = {
        "@type": "Person",
        "name": metadata["author"],
        "url": site_url,
        "description": author_details.get("description")
        or metadata.get("description", ""),
        "sameAs": author_details.get("sameAs", []),
        "jobTitle": author_details.get("jobTitle", "Software Engineer"),
    }
    img = author_details.get("image") or metadata.get("siteLogo", "")
    if img:
        main_entity["image"] = site_url + img.replace("__BASE_PATH__", "")
    email = metadata.get("email")
    if email:
        main_entity["email"] = email
    knows_about = author_details.get("knowsAbout")
    if knows_about:
        main_entity["knowsAbout"] = knows_about
    return main_entity


def _collection_schema(item_list: list[dict], name=None, description=None, url=None) -> dict:
    """Build a CollectionPage schema with the given ItemList.

    Args:
        item_list: list of ListItem schema entries.
        name: Optional collection name.
        description: Optional collection description.
        url: Optional collection URL.
    """
    schema = {"@type": "CollectionPage"}
    if name is not None:
        schema["name"] = name
    if description is not None:
        schema["description"] = description
    if url is not None:
        schema["url"] = url
    schema["mainEntity"] = {"@type": "ItemList", "itemListElement": item_list}
    return schema


def _software_application_item(metadata: SiteMetadata, project: Project, position: int, best_rating: int) -> dict:
    """Build a ListItem schema wrapping a SoftwareApplication for a project."""
    app_url = project.get("website") or project["href"]
    app = {
        "@type": "SoftwareApplication",
        "name": project["title"],
        "description": project.get("description", ""),
        "url": app_url,
        "codeRepository": project["href"],
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "author": _build_author_schema(metadata),
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": project.get("stars", 0),
            "bestRating": best_rating,
            "worstRating": 0,
            "ratingCount": 1,
        },
    }
    return {"@type": "ListItem", "position": position, "item": app}


def _book_item(book: Book, position: int, resolve_image) -> dict:
    """Build a ListItem schema wrapping a Book for the bookshelf."""
    b_schema = {"@type": "Book", "name": book["title"]}
    b_schema["author"] = book.get("author", "")
    b_schema["url"] = book.get("link", "")
    img = resolve_image(book)
    if img:
        b_schema["image"] = img
    try:
        rating = int(book.get("rating", 0))
    except (ValueError, TypeError):
        rating = 0
    if rating > 0:
        b_schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating,
            "ratingCount": 1,
            "bestRating": 5,
            "worstRating": 1,
        }
    return {"@type": "ListItem", "position": position, "item": b_schema}


def _read_site_metadata(filepath) -> dict:
    content = pathlib.Path(filepath).read_text()
    content = content.replace("__BASE_PATH__", BASE_PATH)
    return json.loads(content)


def _breadcrumbs_for_url(url: str, site_url: str) -> dict | None:
    if not url or url == "/":
        return None

    items = []

    if url in _PAGE_NAMES:
        items.append(
            {
                "@type": "ListItem",
                "position": 1,
                "item": {"@id": site_url + "/", "name": "Home"},
            }
        )
        items.append(
            {
                "@type": "ListItem",
                "position": 2,
                "item": {
                    "@id": site_url + url,
                    "name": _PAGE_NAMES[url],
                },
            }
        )
    else:
        parts = url.strip("/").split("/")
        if len(parts) >= 2:
            parent_path = "/" + parts[0] + "/"
            parent_name = _PAGE_NAMES.get(
                parent_path,
                parts[0].replace(".html", "").replace("-", " ").title(),
            )
            items.append(
                {
                    "@type": "ListItem",
                    "position": 1,
                    "item": {"@id": site_url + "/", "name": "Home"},
                }
            )
            items.append(
                {
                    "@type": "ListItem",
                    "position": 2,
                    "item": {
                        "@id": site_url + parent_path,
                        "name": parent_name,
                    },
                }
            )
            child_name = parts[-1].replace(".html", "").replace("-", " ").title()
            items.append(
                {
                    "@type": "ListItem",
                    "position": 3,
                    "item": {"@id": site_url + url, "name": child_name},
                }
            )

    if not items:
        return None

    return {"@type": "BreadcrumbList", "itemListElement": items}


def _apply_template(template_str: str, data: dict) -> str:
    result = template_str
    for key, value in data.items():
        if value is not None:
            result = result.replace("{{" + key + "}}", str(value))
    return result


def _write_page(out_dir: pathlib.Path, rel_path: str, html: str) -> None:
    """Write rendered HTML to out_dir/rel_path, creating parents as needed."""
    target = out_dir / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


def _render_keywords_meta(metadata: SiteMetadata) -> str:
    keywords = ", ".join(metadata.get("keywords", []))
    if not keywords:
        return ""
    return f'<meta name="keywords" content="{escape_html(keywords)}">'


def _render_open_graph(page_info: dict, site_url: str, full_url: str, og_image: str, site_title: str) -> str:
    return f"""
  <meta property="og:title" content="{escape_html(page_info["title"])}">
  <meta property="og:description" content="{escape_html(page_info["description"])}">
  <meta property="og:url" content="{full_url}">
  <meta property="og:image" content="{site_url}{og_image}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{escape_html(site_title)}">"""


def _render_twitter_card(page_info: dict, site_url: str, og_image: str) -> str:
    return f"""
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape_html(page_info["title"])}">
  <meta name="twitter:description" content="{escape_html(page_info["description"])}">
  <meta name="twitter:image" content="{site_url}{og_image}">"""


def _render_json_ld(schemas: list[dict]) -> str:
    if len(schemas) == 1:
        schemas[0]["@context"] = "https://schema.org"
        json_ld_obj = schemas[0]
    else:
        json_ld_obj = {"@context": "https://schema.org", "@graph": schemas}
    json_ld_str = json.dumps(json_ld_obj, indent=2)
    return f"""
  <script type="application/ld+json">
  {json_ld_str}
  </script>"""


_FAVICON_LINKS = """
  <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
  <link rel="manifest" href="/static/favicons/site.webmanifest">
  <link rel="mask-icon" href="/static/favicons/safari-pinned-tab.svg" color="#8b7355">"""


def _render_css_link(extra_css):
    css_link = '<link rel="stylesheet" href="/static/css/style.css">'
    if extra_css:
        css_link += f"\n  {extra_css}"
    return css_link


def render_head(metadata: SiteMetadata, page_info: dict, extra_schemas=None, extra_css=None) -> str:
    """Render the <head> HTML for a page.

    Args:
        metadata: Site-wide metadata.
        page_info: Dict with title, description, url, and optional image.
        extra_schemas: Optional list of JSON-LD schema dicts to include.
        extra_css: Optional extra CSS link tags.

    Returns:
        The complete <head> element HTML.
    """
    site_url = metadata["siteUrl"].rstrip("/")
    full_url = f"{site_url}{page_info['url']}" if page_info["url"] else site_url
    og_image = (
        page_info.get("image")
        or metadata.get("socialBanner")
        or metadata.get("siteLogo", "")
    )

    canonical = f'<link rel="canonical" href="{full_url}">'

    schemas = [
        _website_schema(site_url, metadata["title"]),
        _person_schema(metadata, site_url),
    ]
    breadcrumbs = _breadcrumbs_for_url(page_info.get("url", ""), site_url)
    if breadcrumbs:
        schemas.append(breadcrumbs)
    if extra_schemas:
        schemas.extend(extra_schemas)

    rss_link = f'<link rel="alternate" type="application/rss+xml" title="{escape_html(metadata["title"])}" href="{site_url}/feed.xml">'

    return f"""
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_html(page_info["title"])}</title>
  <meta name="description" content="{escape_html(page_info["description"])}">
  {_render_keywords_meta(metadata)}
  {canonical}
  {_render_open_graph(page_info, site_url, full_url, og_image, metadata["title"])}
  {_render_twitter_card(page_info, site_url, og_image)}
  {_render_json_ld(schemas)}
  {rss_link}
  {_FAVICON_LINKS}
  {_render_css_link(extra_css)}
</head>
"""


def render_header(metadata: SiteMetadata) -> str:
    return """<header>
  <a href="/">Home</a>
  <a href="/static/resume/prakash_s_resume.pdf">Resume</a>
  <a href="/essays/">Essays</a>
    <a href="/projects.html">Projects</a>
    <a href="/bookshelf.html">Bookshelf</a>
    <a href="/notes/">Notes</a>
    <a href="/experiments/">Experiments</a>
    <a href="/quotes.html">Quotes</a>
    <a href="/about.html">About</a>
  <a href="/feed.xml" class="rss-link" aria-label="RSS Feed">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 11a9 9 0 0 1 9 9"/>
      <path d="M4 4a16 16 0 0 1 16 16"/>
      <circle cx="5" cy="19" r="1"/>
    </svg>
  </a>
</header>
"""


def render_footer(metadata: SiteMetadata) -> str:
    year = datetime.now().year
    return f"""<footer>
  <p>&copy; {year} {escape_html(metadata["author"])}. &middot; <a href="/sitelinks.html">Site Links</a></p>
</footer>
"""


_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def _note_description(file_data: FileData, limit: int = 160) -> str:
    text = _LINK_RE.sub(r"\1", file_data["content"])
    for token in ("#", "`", "*", "_", ">", "[", "]"):
        text = text.replace(token, " ")
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "\u2026"
    return text


def _gb_search_html() -> str:
    return f"""<div class="gb-search">
  <svg class="gb-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
  <input type="search" placeholder="Search&hellip;" aria-label="Search" data-gb-search>
  <kbd class="gb-search-kbd">Ctrl K</kbd>
</div>"""


def _notes_sidebar_html(notes: list[NoteTopic], current: dict | None = None) -> str:
    current = current or {}

    parts_html = []
    for n in notes:
        topic_slug = n["topic_slug"]
        root = {"dirs": {}, "files": list(n["files"])}
        for st in n["subtopics"]:
            node = root
            for part in st["subtopic_path"].split("/"):
                if part not in node["dirs"]:
                    node["dirs"][part] = {"dirs": {}, "files": []}
                node = node["dirs"][part]
            node["files"] = list(st["files"])

        def files_html(node, path_parts):
            cur_sub = "/".join(path_parts) if path_parts else None
            out = []
            for f in node["files"]:
                href = _note_file_url(topic_slug, cur_sub, f["slug"])
                active = (
                    current.get("topic_slug") == topic_slug
                    and current.get("subtopic_path") == cur_sub
                    and current.get("file_slug") == f["slug"]
                )
                cls = ' class="gb-tree-file active"' if active else ' class="gb-tree-file"'
                out.append(f'<a{cls} href="{href}">{escape_html(f["title"])}</a>')
            return "\n".join(out)

        def dirs_html(dirs, path_parts):
            out = []
            for name, sub in sorted(dirs.items()):
                child_path = "/".join(path_parts + [name])
                current_path = current.get("subtopic_path") or ""
                expanded = current.get("topic_slug") == topic_slug and (
                    current_path == child_path
                    or current_path.startswith(child_path + "/")
                )
                inner = files_html(sub, path_parts + [name]) + dirs_html(
                    sub["dirs"], path_parts + [name]
                )
                open_attr = " open" if expanded else ""
                out.append(
                    f'<details class="gb-tree-sub"{open_attr}><summary>{escape_html(name)}</summary>'
                    f'<div class="gb-tree-inner">{inner}</div></details>'
                )
            return "\n".join(out)

        topic_active = current.get("topic_slug") == topic_slug
        summary_cls = ' class="topic-active"' if topic_active else ""
        inner = files_html(root, []) + dirs_html(root["dirs"], [])
        open_attr = " open" if topic_active else ""
        parts_html.append(
            f'<details class="gb-tree-dir"{open_attr}><summary{summary_cls}>{escape_html(n["topic_title"])}</summary>'
            f'<div class="gb-tree-inner">{inner}</div></details>'
        )

    tree = "\n".join(parts_html)
    return f"""<input type="checkbox" id="gb-nav-toggle" class="gb-nav-toggle">
<label for="gb-nav-toggle" class="gb-burger" aria-label="Toggle notes navigation"><span class="gb-burger-icon"><span></span><span></span><span></span></span></label>
<aside class="gb-sidebar">
  <a class="gb-brand" href="/notes/">Notes</a>
  {_gb_search_html()}
  <nav class="gb-tree">
    {tree}
  </nav>
  <a class="gb-back" href="/">&larr; Home</a>
</aside>"""


def _pager_html(items: list[dict], current: str, get_id, get_href, aria_label: str) -> str:
    idx = next((i for i, it in enumerate(items) if get_id(it) == current), None)
    if idx is None:
        return ""
    prev_item = items[idx - 1] if idx > 0 else None
    next_item = items[idx + 1] if idx < len(items) - 1 else None

    def cell(direction: str, item: dict | None) -> str:
        label = "Previous" if direction == "prev" else "Next"
        arrow = "&larr;" if direction == "prev" else "&rarr;"
        if item is None:
            return (
                f'<a class="gb-pager-{direction} disabled" href="#" tabindex="-1">'
                f'<span class="gb-pager-label">{arrow} {label}</span>'
                f'<span class="gb-pager-title"></span></a>'
            )
        return (
            f'<a class="gb-pager-{direction}" href="{get_href(item)}">'
            f'<span class="gb-pager-label">{arrow} {label}</span>'
            f'<span class="gb-pager-title">{escape_html(item["title"])}</span></a>'
        )

    return f"""<nav class="gb-pager" aria-label="{aria_label}">
  {cell("prev", prev_item)}
  {cell("next", next_item)}
</nav>"""


def _notes_pager_html(notes: list[NoteTopic], current_url: str) -> str:
    return _docs_pager(_flatten_note_pages(notes), current_url)


def _flatten_note_pages(notes: list[NoteTopic]) -> list[dict]:
    pages = []
    for n in notes:
        base = _note_topic_url(n["topic_slug"])
        for st in n["subtopics"]:
            st_base = f'{base}{st["subtopic_path"]}/'
            for f in st["files"]:
                pages.append(
                    {
                        "url": f'{st_base}{f["slug"]}.html',
                        "title": f'{f["title"]} \u00b7 {n["topic_title"]}',
                    }
                )
        for f in n["files"]:
            pages.append({"url": f'{base}{f["slug"]}.html', "title": f["title"]})
    return pages


def _docs_pager(items: list[dict], current_url: str) -> str:
    return _pager_html(
        items, current_url, lambda i: i["url"], lambda i: i["url"],
        "Documents navigation",
    )


def _extract_body(full_html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", full_html, re.S)
    return match.group(1).strip() if match else full_html


def _flatten_experiment_pages(experiments: list[ExperimentTopic]) -> list[dict]:
    pages = []
    for exp in experiments:
        base = _topic_url(exp["topic_slug"])
        for st in exp["subtopics"]:
            st_base = f'{base}{st["subtopic_path"]}/'
            for f in st["files"]:
                pages.append(
                    {
                        "url": f'{st_base}{f["slug"]}.html',
                        "title": f'{f["title"]} \u00b7 {exp["topic_title"]}',
                    }
                )
        for f in exp["files"]:
            pages.append({"url": f'{base}{f["slug"]}.html', "title": f["title"]})
    return pages


def _essay_url(slug: str) -> str:
    """Return the URL path for an essay slug."""
    return f"/essays/{slug}.html"


def _note_topic_url(topic_slug: str) -> str:
    """Return the URL path for a note topic index."""
    return f"/notes/{topic_slug}/"


def _note_file_url(topic_slug: str, subtopic_path: str | None, file_slug: str) -> str:
    base = f"/notes/{topic_slug}"
    if subtopic_path:
        base += "/" + subtopic_path
    return f"{base}/{file_slug}.html"


def _tag_url(tag: str) -> str:
    """Return the URL path for a tag page."""
    return f"/tags/{tag}.html"


def _topic_url(topic_slug: str) -> str:
    """Return the URL path for an experiment topic index."""
    return f"/experiments/{topic_slug}/"


def _exp_file_url(topic_slug: str, subtopic_path: str | None, file_slug: str) -> str:
    base = f"/experiments/{topic_slug}"
    if subtopic_path:
        base += "/" + subtopic_path
    return f"{base}/{file_slug}.html"


def _experiments_sidebar_html(experiments: list[ExperimentTopic], current: dict | None = None) -> str:
    current = current or {}

    parts_html = []
    for exp in experiments:
        topic_slug = exp["topic_slug"]
        root = {"dirs": {}, "files": list(exp["files"])}
        for st in exp["subtopics"]:
            node = root
            for part in st["subtopic_path"].split("/"):
                if part not in node["dirs"]:
                    node["dirs"][part] = {"dirs": {}, "files": []}
                node = node["dirs"][part]
            node["files"] = list(st["files"])

        def files_html(node, path_parts):
            cur_sub = "/".join(path_parts) if path_parts else None
            out = []
            for f in node["files"]:
                href = _exp_file_url(topic_slug, cur_sub, f["slug"])
                active = (
                    current.get("topic_slug") == topic_slug
                    and current.get("subtopic_path") == cur_sub
                    and current.get("file_slug") == f["slug"]
                )
                cls = ' class="gb-tree-file active"' if active else ' class="gb-tree-file"'
                out.append(f'<a{cls} href="{href}">{escape_html(f["title"])}</a>')
            return "\n".join(out)

        def dirs_html(dirs, path_parts):
            out = []
            for name, sub in sorted(dirs.items()):
                child_path = "/".join(path_parts + [name])
                current_path = current.get("subtopic_path") or ""
                expanded = current.get("topic_slug") == topic_slug and (
                    current_path == child_path
                    or current_path.startswith(child_path + "/")
                )
                inner = files_html(sub, path_parts + [name]) + dirs_html(
                    sub["dirs"], path_parts + [name]
                )
                open_attr = " open" if expanded else ""
                out.append(
                    f'<details class="gb-tree-sub"{open_attr}><summary>{escape_html(name)}</summary>'
                    f'<div class="gb-tree-inner">{inner}</div></details>'
                )
            return "\n".join(out)

        topic_active = current.get("topic_slug") == topic_slug
        summary_cls = ' class="topic-active"' if topic_active else ""
        inner = files_html(root, []) + dirs_html(root["dirs"], [])
        open_attr = " open" if topic_active else ""
        parts_html.append(
            f'<details class="gb-tree-dir"{open_attr}><summary{summary_cls}>{escape_html(exp["topic_title"])}</summary>'
            f'<div class="gb-tree-inner">{inner}</div></details>'
        )

    tree = "\n".join(parts_html)
    return f"""<input type="checkbox" id="gb-nav-toggle" class="gb-nav-toggle">
<label for="gb-nav-toggle" class="gb-burger" aria-label="Toggle experiments navigation"><span class="gb-burger-icon"><span></span><span></span><span></span></span></label>
<aside class="gb-sidebar">
  <a class="gb-brand" href="/experiments/">Experiments</a>
  {_gb_search_html()}
  <nav class="gb-tree">
    {tree}
  </nav>
  <a class="gb-back" href="/">&larr; Home</a>
</aside>"""


def _essay_article_html(e: Essay, indent: int = 0, tags: bool = True) -> str:
    p = " " * indent
    i = p + "  "
    t = ""
    if tags:
        t = "".join(
            f'<a href="{_tag_url(tag)}">#{escape_html(tag)}</a>'
            for tag in e["tags"][:3]
        )
        t = f'{i}<div class="tags">\n{i}  {t}\n{i}</div>\n'
    return (
        f'{p}<article>\n'
        f'{i}<h2><a href="{_essay_url(e["slug"])}">{escape_html(e["title"])}</a></h2>\n'
        f'{i}<p class="meta"><time>{_format_date(e["date"])}</time></p>\n'
        f'{i}<p class="summary">{escape_html(e["summary"])}</p>\n'
        f'{t}{p}</article>'
    )


def _render_stars(rating) -> str:
    """Render a numeric rating as star characters, or empty string."""
    try:
        n = int(rating)
    except (ValueError, TypeError):
        return ""
    if not n:
        return ""
    return "★" * n + "☆" * (5 - n)


def _resolve_book_image(book: Book) -> str:
    """Resolve a book's cover image URL, preferring local assets."""
    url = book.get("imageUrl", "")
    if not url or "nophoto" in url:
        return ""
    if url.startswith("/"):
        local = pathlib.Path.cwd() / "data" / "public" / url.lstrip("/")
        if not local.exists():
            url = book.get("imageUrlRemote", "")
    return url if url and "nophoto" not in url else ""


def _build_book_card(book: Book, category: dict, resolve_image) -> str:
    """Build the HTML for a single book in the bookshelf."""
    escaped_title = escape_html(book.get("title", ""))
    escaped_author = escape_html(book.get("author", ""))
    stars = _render_stars(book.get("rating"))
    href = escape_html(book.get("link", "#"))
    img_url = resolve_image(book)

    has_image = bool(img_url)
    is_current = category["dataKey"] == "currently-reading"

    style = f' style="background-image:url({escape_html(img_url)})"' if has_image else ""
    placeholder = (
        f'<div class="book-placeholder">{escaped_title}</div>' if not has_image else ""
    )
    stars_html = f'<span class="book-rating">{stars}</span>' if stars else ""
    current_class = " current" if is_current else ""

    return f'''
    <a href="{href}" class="book{current_class}" target="_blank" rel="noopener"{style}>
      {placeholder}
      <div class="book-shine"></div>
      {stars_html}
      <div class="book-tooltip">
        <b>{escaped_title}</b>
        <span>{escaped_author}</span>
      </div>
    </a>'''


def _build_unified_bookcase(groups: list[dict]) -> str:
    """Build the full bookshelf HTML from grouped book lists."""
    shelves_el = []
    for group in groups:
        books_html = "".join(
            _build_book_card(b, group, _resolve_book_image) for b in group["books"]
        )
        shelves_el.append(
            f'''
    <section class="shelf-section">
      <div class="shelf-label {group["tagClass"]}">
        <span class="tag-dot"></span>{group["label"]}<span class="n">{len(group["books"])} book{"s" if len(group["books"]) != 1 else ""}</span>
      </div>
      <div class="compartment">
        <div class="shelf-boards">{books_html}</div>
      </div>
    </section>'''
        )
    return f'''
    <div class="bookcase">
      {"".join(shelves_el)}
    </div>'''


def _render_quote_item(q: Quote) -> str:
    """Build the HTML for a single quote item."""
    escaped_quote = escape_html(q.get("quote", ""))
    escaped_author = escape_html(q.get("author", ""))
    escaped_book = escape_html(q.get("book", "")) if q.get("book") else ""
    url = q.get("url", "")

    author_html = (
        f'<span class="quote-author">{escaped_author}</span>' if escaped_author else ""
    )
    book_html = (
        f', <span class="quote-book">{escaped_book}</span>' if escaped_book else ""
    )

    quote_url = (
        f'<a href="{escape_html(url)}" class="quote-body-link" target="_blank" rel="noopener">'
    )
    return f'''    <li>
      <div class="quote-content">
        {quote_url}<q>{escaped_quote}</q></a>
        <div class="quote-attribution">
          {author_html}{book_html}
        </div>
      </div>
    </li>'''


def _render_markdown(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    content = file_data["content"]
    try:
        nb = nbf.new_notebook()
        nb.metadata.kernelspec = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        }
        nb.metadata.language_info = {"name": "python", "version": "3.14.0"}
        nb.cells = [nbf.new_markdown_cell(content)]
        exporter = HTMLExporter(template_name="classic")
        full_html, _resources = exporter.from_notebook_node(nb)
        return _extract_body(full_html)
    except Exception as exc:
        _logger.warning("nbconvert failed for markdown, falling back to renderer: %s", exc)
    return markdown_renderer.render(content)


_HLJS_LANG_MAP = {
    "ipython3": "python",
    "ipython": "python",
    "python": "python",
    "py": "python",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "c": "c",
    "cpp": "cpp",
    "r": "r",
    "julia": "julia",
    "javascript": "javascript",
    "js": "javascript",
}


def _hljs_language(highlight_cls: str) -> str | None:
    """Map an nbconvert 'hl-*' pygments class to a highlight.js language."""
    for token in highlight_cls.split():
        if token.startswith("hl-"):
            return _HLJS_LANG_MAP.get(token[3:].lower())
    return None


def _make_code_cells_collapsible(body_html: str) -> str:
    """Wrap each notebook code cell input in a collapsible <details> block.

    Code cells are collapsed by default; the prompt and outputs stay visible.
    The nbconvert pygments markup is replaced with a highlight.js-friendly
    <pre><code class="language-..."> so hljs.highlightAll() can colorize it.
    """
    soup = BeautifulSoup(body_html, "html.parser")
    for cell in soup.select("div.code_cell"):
        inp = cell.find("div", class_="input", recursive=False)
        if inp is None:
            continue
        inner = inp.find("div", class_="inner_cell", recursive=False)
        if inner is None:
            continue
        details = soup.new_tag("details", attrs={"class": "gb-code-block"})
        summary = soup.new_tag("summary")
        expand = soup.new_tag("span", attrs={"class": "gb-code-expand"})
        expand.string = "Expand Code"
        collapse = soup.new_tag("span", attrs={"class": "gb-code-collapse"})
        collapse.string = "Collapse Code"
        summary.append(expand)
        summary.append(collapse)
        details.append(summary)
        inner.wrap(details)

        for hl in inner.select("div.highlight"):
            pre = hl.find("pre")
            if pre is None:
                continue
            code = soup.new_tag("code")
            language = _hljs_language(" ".join(hl.get("class") or []))
            if language:
                code["class"] = f"language-{language}"
            code.string = pre.get_text()
            pre.clear()
            pre.append(code)
    main = soup.find("main")
    return str(main) if main is not None else str(soup)


def _render_notebook(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    content = file_data["content"]
    try:
        nb = reads(content, NO_CONVERT)
    except Exception as exc:
        _logger.warning("Invalid notebook, rendering as code: %s", exc)
        return f"<pre><code>{escape_html(content)}</code></pre>"
    try:
        exporter = HTMLExporter(template_name="classic")
        full_html, _resources = exporter.from_notebook_node(nb)
        return _make_code_cells_collapsible(_extract_body(full_html))
    except Exception as exc:
        _logger.warning("Notebook export failed, rendering as code: %s", exc)
    return f"<pre><code>{escape_html(content)}</code></pre>"


def _render_code_as_notebook(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    escaped = escape_html(file_data["content"])
    return f'<pre><code class="language-{file_data["ext"]}">{escaped}</code></pre>'


_RENDER_STRATEGIES = {
    "md": _render_markdown,
    "ipynb": _render_notebook,
    "py": _render_code_as_notebook,
    "c": _render_code_as_notebook,
    "txt": _render_code_as_notebook,
}


def _render_experiment_content(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    strategy = _RENDER_STRATEGIES.get(file_data["ext"], _render_code_as_notebook)
    return strategy(file_data, markdown_renderer)


class DataLoader:
    """Loads raw site data (JSON, markdown, templates, submodule content)."""

    def __init__(self, data_dir):
        self.data_dir = pathlib.Path(data_dir)

    def read_json(self, filepath) -> dict:
        return json.loads((self.data_dir / filepath).read_text())

    def read_md(self, filepath) -> dict:
        return parse_frontmatter(pathlib.Path(filepath).read_text())

    def load_template(self, template_name: str) -> str:
        template_path = self.data_dir / "templates" / f"{template_name}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text()

    def read_author(self) -> dict:
        content = (
            self.data_dir / "authors" / "default.mdx"
        ).read_text()
        parsed = parse_frontmatter(content)
        return {**parsed["data"], "body": parsed["content"]}

    def read_site_metadata(self) -> SiteMetadata:
        return _read_site_metadata(
            self.data_dir / "siteMetadata.json"
        )

    def get_essays(self) -> list[Essay]:
        essays_dir = self.data_dir / "essays"
        files = [f for f in essays_dir.iterdir() if f.suffix == ".md"]
        result = []
        for file in files:
            parsed = self.read_md(file)
            if parsed["data"].get("draft"):
                continue
            data = parsed["data"]
            result.append(
                {
                    "slug": file.stem,
                    "title": data.get("title", ""),
                    "date": data.get("date", ""),
                    "summary": data.get("summary", ""),
                    "tags": data.get("tags", []),
                    "content": parsed["content"],
                }
            )
        result.sort(key=lambda x: x["date"], reverse=True)
        return result

    def get_books(self) -> dict:
        return self.read_json("books.json")

    def get_precept(self) -> dict:
        return self.read_json("precept.json")

    def get_projects(self) -> list[Project]:
        return self.read_json("repos.json")

    def get_leetcode_solutions(self) -> list[dict]:
        return self.read_json("leetcode-solutions.json")

    def get_quotes(self) -> list[Quote]:
        return self.read_json("quotes.json")

    def get_notes(self) -> list[NoteTopic]:
        notes_path = NOTES_DIR
        if not notes_path.is_dir():
            return []
        notes = []
        for topic in sorted(notes_path.iterdir()):
            if not topic.is_dir():
                continue
            topic_data = {
                "topic": topic.name,
                "topic_slug": slug(topic.name),
                "topic_title": topic.name.replace("-", " ")
                .replace("_", " ")
                .title(),
                "files": [],
                "subtopics": {},
            }
            for root, dirs, filenames in os.walk(topic):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d != "__pycache__"
                    and d != ".ipynb_checkpoints"
                ]
                for f in sorted(filenames):
                    if pathlib.Path(f).suffix.lower() != ".md":
                        continue
                    full_path = pathlib.Path(root) / f
                    rel_dir = os.path.relpath(root, topic)
                    if rel_dir == ".":
                        rel_dir = None
                    try:
                        content = full_path.read_text()
                    except OSError as exc:
                        _logger.warning("Skipping unreadable file %s: %s", full_path, exc)
                        continue
                    name = full_path.stem
                    file_data = {
                        "filename": f,
                        "slug": slug(name),
                        "title": name.replace("-", " ").replace("_", " ").title(),
                        "ext": "md",
                        "content": content,
                    }
                    if rel_dir is None:
                        topic_data["files"].append(file_data)
                    else:
                        st_path = rel_dir.replace(os.sep, "/")
                        topic_data["subtopics"].setdefault(st_path, []).append(
                            file_data
                        )
            if topic_data["files"] or topic_data["subtopics"]:
                st_list = []
                for st_path in sorted(topic_data["subtopics"]):
                    st_list.append(
                        {
                            "subtopic_path": st_path,
                            "subtopic_title": st_path.replace("-", " ")
                            .replace("_", " ")
                            .title(),
                            "files": topic_data["subtopics"][st_path],
                        }
                    )
                topic_data["subtopics"] = st_list
                notes.append(topic_data)
        return notes

    def get_experiments(self) -> list[ExperimentTopic]:
        experiments_path = EXPERIMENTS_DIR
        if not experiments_path.is_dir():
            return []
        experiments = []
        for topic in sorted(experiments_path.iterdir()):
            if not topic.is_dir():
                continue
            topic_data = {
                "topic": topic.name,
                "topic_slug": slug(topic.name),
                "topic_title": topic.name.replace("-", " ")
                .replace("_", " ")
                .title(),
                "files": [],
                "subtopics": {},
            }
            for root, dirs, filenames in os.walk(topic):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d != "__pycache__"
                    and d != ".ipynb_checkpoints"
                ]
                for f in sorted(filenames):
                    ext = pathlib.Path(f).suffix.lower()
                    if ext not in _ALLOWED_EXTS:
                        continue
                    full_path = pathlib.Path(root) / f
                    rel_dir = os.path.relpath(root, topic)
                    if rel_dir == ".":
                        rel_dir = None
                    try:
                        content = full_path.read_text()
                    except OSError as exc:
                        _logger.warning("Skipping unreadable file %s: %s", full_path, exc)
                        continue
                    name = full_path.stem
                    file_data = {
                        "filename": f,
                        "slug": slug(name),
                        "title": name,
                        "ext": ext.lstrip("."),
                        "content": content,
                    }
                    if rel_dir is None:
                        topic_data["files"].append(file_data)
                    else:
                        st_path = rel_dir.replace(os.sep, "/")
                        topic_data["subtopics"].setdefault(st_path, []).append(
                            file_data
                        )
            if topic_data["files"] or topic_data["subtopics"]:
                st_list = []
                for st_path in sorted(topic_data["subtopics"]):
                    st_list.append(
                        {
                            "subtopic_path": st_path,
                            "subtopic_title": st_path.replace("-", " ")
                            .replace("_", " ")
                            .title(),
                            "files": topic_data["subtopics"][st_path],
                        }
                    )
                topic_data["subtopics"] = st_list
                experiments.append(topic_data)
        return experiments


class PageBuilder:
    """Renders every page of the site and writes HTML to the output dir."""

    def __init__(self, data_loader: DataLoader, markdown_renderer: MarkdownRenderer, gfm_renderer: MarkdownRenderer):
        self.data_loader = data_loader
        self.markdown_renderer = markdown_renderer
        self.gfm_renderer = gfm_renderer

    def _build_common(
        self,
        template: str,
        metadata: SiteMetadata,
        page_title: str,
        page_description: str,
        url: str = "",
        image: str = "",
        extra_schemas: list[dict] | None = None,
        extra_css: str | None = None,
    ) -> str:
        """Fill a template's head/header/footer with site-wide HTML.

        Returns:
            The fully rendered page HTML with page content still to be filled.
        """
        return _apply_template(
            template,
            {
                "head": render_head(
                    metadata,
                    {
                        "title": page_title,
                        "description": page_description,
                        "url": url,
                        "image": image,
                    },
                    extra_schemas=extra_schemas,
                    extra_css=extra_css,
                ),
                "header": render_header(metadata),
                "footer": render_footer(metadata),
            },
        )

    def build_home(self, metadata: SiteMetadata, essays: list[Essay], books: dict, projects: list[Project], author: dict, avatar: str, precept: dict) -> None:
        """Build the homepage (index.html)."""
        template = self.data_loader.load_template("home")
        html = self._build_common(
            template, metadata, metadata["title"], metadata["description"], "/"
        )

        recent_essays_html = "\n".join(
            _essay_article_html(e, indent=4) for e in essays[:4]
        )
        recent_essays_html += '\n    <p class="section-footer"><a href="/essays/">All essays &rarr;</a></p>'

        featured_projects_html = (
            '<div class="project-grid">'
            + "".join(
                f"""    <div class="project-card">
      <h3>{f'<a href="{escape_html(p["website"])}">{escape_html(p["title"])}</a>' if p.get("website") else escape_html(p["title"])}</h3>
      <p class="summary">{escape_html(p.get("description", ""))}</p>
      {('<div class="tags">' + "".join(f"<span>#{escape_html(t)}</span>" for t in p.get("tags", [])) + "</div>") if p.get("tags") else ""}
    </div>"""
                for p in projects[:6]
            )
            + '\n    </div>\n    <p class="section-footer"><a href="/projects.html">All projects &rarr;</a></p>'
        )

        curated_books = books.get("curated", [])
        reading_list_html = "\n".join(
            f"""    <li>
      <a href="{escape_html(b["link"])}" target="_blank" rel="noopener">{escape_html(b["title"])}</a>
    </li>"""
            for b in curated_books[:5]
        )

        first_para = author["body"].split("\n\n")[0] if author["body"] else ""

        precept_html = "\n".join(
            f"""    <li>
      <a href="{escape_html(p["link"])}" target="_blank" rel="noopener">{escape_html(p["title"])}</a>
    </li>"""
            for p in (precept[:4] or [])
        )

        html = _apply_template(
            html,
            {
                "recentEssays": recent_essays_html,
                "featuredProjects": featured_projects_html,
                "authorPreview": escape_html(first_para),
                "readingList": reading_list_html,
                "preceptList": precept_html,
                "metadata.author": escape_html(metadata["author"]),
                "avatar": avatar,
            },
        )

        _write_page(OUT_DIR, "index.html", html)

    def build_essays_list(self, metadata: SiteMetadata, essays: list[Essay]) -> None:
        """Build the essays index page."""
        template = self.data_loader.load_template("essays-list")
        html = self._build_common(
            template,
            metadata,
            metadata["title"],
            f"Essays by {metadata['author']}",
            "/essays/",
        )

        essays_list_html = "\n".join(_essay_article_html(e) for e in essays)

        html = _apply_template(html, {"essaysList": essays_list_html})

        _write_page(OUT_DIR, "essays/index.html", html)

    def build_essay(self, metadata: SiteMetadata, essay: Essay) -> None:
        """Build a single essay page."""
        template = self.data_loader.load_template("essay")
        site_url = metadata["siteUrl"].rstrip("/")
        essay_url = _essay_url(essay["slug"])

        blog_posting = _blog_posting_schema(metadata, essay, site_url, essay_url)

        html = self._build_common(
            template,
            metadata,
            f"{essay['title']} - {metadata['title']}",
            essay["summary"],
            essay_url,
            extra_schemas=[blog_posting],
        )

        essay_content = self.markdown_renderer.render(essay["content"])

        html = _apply_template(
            html,
            {
                "essay.title": escape_html(essay["title"]),
                "essay.date": _format_date(essay["date"]),
                "essay.tags": " ".join(
                    f'<a href="{_tag_url(t)}">#{escape_html(t)}</a>'
                    for t in essay["tags"]
                ),
                "essay.content": essay_content,
            },
        )

        _write_page(OUT_DIR, f"essays/{essay['slug']}.html", html)

    def build_notes_list(self, metadata: SiteMetadata, notes: list[NoteTopic]) -> None:
        """Build the notes index page."""
        template = self.data_loader.load_template("notes")
        html = self._build_common(
            template,
            metadata,
            f"Notes - {metadata['title']}",
            "Quick references and notes",
            "/notes/",
            extra_css=_DOCS_EXTRA_CSS,
        )

        sections = []
        for note in notes:
            file_links = []
            for st in note["subtopics"]:
                for f in st["files"]:
                    file_links.append(
                        f'    <a class="gb-file-link" href="{_note_file_url(note["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">note</span></a>'
                    )
            for f in note["files"]:
                file_links.append(
                    f'    <a class="gb-file-link" href="{_note_file_url(note["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">note</span></a>'
                )
            sections.append(
                f'<section class="gb-index-section"><h2><a class="gb-topic-title" href="{_note_topic_url(note["topic_slug"])}">{escape_html(note["topic_title"])}</a></h2>'
                f'<div class="gb-file-list">{"".join(file_links)}</div></section>'
            )

        html = _apply_template(
            html,
            {
                "notesSidebar": _notes_sidebar_html(notes),
                "notesTitle": "Notes",
                "notesLead": "Quick references and notes on various topics",
                "notesContent": "\n".join(sections),
            },
        )

        _write_page(OUT_DIR, "notes/index.html", html)

    def build_note_topic_index(self, metadata: SiteMetadata, topic: NoteTopic, notes: list[NoteTopic]) -> None:
        """Build a note topic index page."""
        template = self.data_loader.load_template("notes")
        topic_url = _note_topic_url(topic["topic_slug"])
        html = self._build_common(
            template,
            metadata,
            f'{topic["topic_title"]} - Notes - {metadata["title"]}',
            f'Notes in {topic["topic_title"]}',
            topic_url,
            extra_css=_DOCS_EXTRA_CSS,
        )
        sections = []
        for st in topic["subtopics"]:
            file_links = "\n".join(
                f'    <a class="gb-file-link" href="{_note_file_url(topic["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">note</span></a>'
                for f in st["files"]
            )
            sections.append(
                f'<section class="gb-index-section"><h2>{escape_html(st["subtopic_title"])}</h2>'
                f'<div class="gb-file-list">{file_links}</div></section>'
            )
        if topic["files"]:
            file_links = "\n".join(
                f'    <a class="gb-file-link" href="{_note_file_url(topic["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">note</span></a>'
                for f in topic["files"]
            )
            sections.append(
                f'<section class="gb-index-section"><h2>Notes</h2><div class="gb-file-list">{file_links}</div></section>'
            )
        html = _apply_template(
            html,
            {
                "notesSidebar": _notes_sidebar_html(
                    notes, {"topic_slug": topic["topic_slug"]}
                ),
                "notesTitle": escape_html(topic["topic_title"]),
                "notesLead": f'Notes in {topic["topic_title"]}',
                "notesContent": "\n".join(sections),
            },
        )
        _write_page(OUT_DIR, f'notes/{topic["topic_slug"]}/index.html', html)

    def build_note_subtopic_index(self, metadata: SiteMetadata, topic: NoteTopic, subtopic: dict, notes: list[NoteTopic]) -> None:
        """Build a note subtopic index page."""
        template = self.data_loader.load_template("notes")
        st_url = f'/notes/{topic["topic_slug"]}/{subtopic["subtopic_path"]}/'
        html = self._build_common(
            template,
            metadata,
            f'{subtopic["subtopic_title"]} - {topic["topic_title"]} - Notes - {metadata["title"]}',
            f'Notes in {topic["topic_title"]} / {subtopic["subtopic_title"]}',
            st_url,
            extra_css=_DOCS_EXTRA_CSS,
        )
        file_links = "\n".join(
            f'    <a class="gb-file-link" href="{_note_file_url(topic["topic_slug"], subtopic["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">note</span></a>'
            for f in subtopic["files"]
        )
        html = _apply_template(
            html,
            {
                "notesSidebar": _notes_sidebar_html(
                    notes,
                    {
                        "topic_slug": topic["topic_slug"],
                        "subtopic_path": subtopic["subtopic_path"],
                    },
                ),
                "notesTitle": escape_html(subtopic["subtopic_title"]),
                "notesLead": f'Notes in {topic["topic_title"]} / {subtopic["subtopic_title"]}',
                "notesContent": f'<section class="gb-index-section"><div class="gb-file-list">{file_links}</div></section>',
            },
        )
        _write_page(
            OUT_DIR,
            f'notes/{topic["topic_slug"]}/{subtopic["subtopic_path"]}/index.html',
            html,
        )

    def build_note(self, metadata: SiteMetadata, topic: NoteTopic, file_data: FileData, notes: list[NoteTopic], subtopic_path: str | None = None) -> None:
        """Build a single note page."""
        template = self.data_loader.load_template("note")
        note_url = _note_file_url(topic["topic_slug"], subtopic_path, file_data["slug"])

        note_content = self.gfm_renderer.render(file_data["content"])

        html = self._build_common(
            template,
            metadata,
            f"{file_data['title']} - Notes - {metadata['title']}",
            f"Notes on {file_data['title']}",
            note_url,
            extra_css=_DOCS_GITBOOK_EXTRA_CSS,
        )

        html = _apply_template(
            html,
            {
                "notesSidebar": _notes_sidebar_html(
                    notes,
                    {
                        "topic_slug": topic["topic_slug"],
                        "subtopic_path": subtopic_path,
                        "file_slug": file_data["slug"],
                    },
                ),
                "note.title": escape_html(file_data["title"]),
                "note.content": note_content,
                "notesPager": _notes_pager_html(notes, note_url),
            },
        )

        note_dir = f'notes/{topic["topic_slug"]}'
        if subtopic_path:
            note_dir += f'/{subtopic_path}'
        _write_page(OUT_DIR, f'{note_dir}/{file_data["slug"]}.html', html)

    def build_experiments_list(self, metadata: SiteMetadata, experiments: list[ExperimentTopic]) -> None:
        """Build the experiments index page."""
        template = self.data_loader.load_template("experiments")
        html = self._build_common(
            template,
            metadata,
            f"Experiments - {metadata['title']}",
            "Document explorations and experiments",
            "/experiments/",
            extra_css=_DOCS_EXTRA_CSS,
        )
        sections = []
        for exp in experiments:
            file_links = []
            for st in exp["subtopics"]:
                for f in st["files"]:
                    file_links.append(
                        f'    <a class="gb-file-link" href="{_exp_file_url(exp["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">{escape_html(f["ext"].upper())} file</span></a>'
                    )
            for f in exp["files"]:
                file_links.append(
                    f'    <a class="gb-file-link" href="{_exp_file_url(exp["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">{escape_html(f["ext"].upper())} file</span></a>'
                )
            sections.append(
                f'<section class="gb-index-section"><h2><a class="gb-topic-title" href="{_topic_url(exp["topic_slug"])}">{escape_html(exp["topic_title"])}</a></h2>'
                f'<div class="gb-file-list">{"".join(file_links)}</div></section>'
            )
        html = _apply_template(
            html,
            {
                "experimentsSidebar": _experiments_sidebar_html(experiments),
                "experimentsTitle": "Experiments",
                "experimentsLead": "Code experiments and explorations",
                "experimentsContent": "\n".join(sections),
                "experimentsPager": "",
            },
        )
        _write_page(OUT_DIR, "experiments/index.html", html)

    def build_topic_index(self, metadata: SiteMetadata, topic: ExperimentTopic, experiments: list[ExperimentTopic]) -> None:
        """Build an experiment topic index page."""
        template = self.data_loader.load_template("experiments")
        topic_url = _topic_url(topic["topic_slug"])
        html = self._build_common(
            template,
            metadata,
            f'{topic["topic_title"]} - Experiments - {metadata["title"]}',
            f'Experiments in {topic["topic_title"]}',
            topic_url,
            extra_css=_DOCS_EXTRA_CSS,
        )
        sections = []
        for st in topic["subtopics"]:
            file_links = "\n".join(
                f'    <a class="gb-file-link" href="{_exp_file_url(topic["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">{escape_html(f["ext"].upper())} file</span></a>'
                for f in st["files"]
            )
            sections.append(
                f'<section class="gb-index-section"><h2>{escape_html(st["subtopic_title"])}</h2>'
                f'<div class="gb-file-list">{file_links}</div></section>'
            )
        if topic["files"]:
            file_links = "\n".join(
                f'    <a class="gb-file-link" href="{_exp_file_url(topic["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">{escape_html(f["ext"].upper())} file</span></a>'
                for f in topic["files"]
            )
            sections.append(
                f'<section class="gb-index-section"><h2>Files</h2><div class="gb-file-list">{file_links}</div></section>'
            )
        html = _apply_template(
            html,
            {
                "experimentsSidebar": _experiments_sidebar_html(
                    experiments, {"topic_slug": topic["topic_slug"]}
                ),
                "experimentsTitle": escape_html(topic["topic_title"]),
                "experimentsLead": f'Experiments in {topic["topic_title"]}',
                "experimentsContent": "\n".join(sections),
                "experimentsPager": "",
            },
        )
        _write_page(
            OUT_DIR, f'experiments/{topic["topic_slug"]}/index.html', html
        )

    def build_subtopic_index(self, metadata: SiteMetadata, topic: ExperimentTopic, subtopic: dict, experiments: list[ExperimentTopic]) -> None:
        """Build an experiment subtopic index page."""
        template = self.data_loader.load_template("experiments")
        st_url = f'/experiments/{topic["topic_slug"]}/{subtopic["subtopic_path"]}/'
        html = self._build_common(
            template,
            metadata,
            f'{subtopic["subtopic_title"]} - {topic["topic_title"]} - Experiments - {metadata["title"]}',
            f'Experiments in {topic["topic_title"]} / {subtopic["subtopic_title"]}',
            st_url,
            extra_css=_DOCS_EXTRA_CSS,
        )
        file_links = "\n".join(
            f'    <a class="gb-file-link" href="{_exp_file_url(topic["topic_slug"], subtopic["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="gb-file-meta">{escape_html(f["ext"].upper())} file</span></a>'
            for f in subtopic["files"]
        )
        html = _apply_template(
            html,
            {
                "experimentsSidebar": _experiments_sidebar_html(
                    experiments,
                    {
                        "topic_slug": topic["topic_slug"],
                        "subtopic_path": subtopic["subtopic_path"],
                    },
                ),
                "experimentsTitle": escape_html(subtopic["subtopic_title"]),
                "experimentsLead": f'Experiments in {topic["topic_title"]} / {subtopic["subtopic_title"]}',
                "experimentsContent": (
                    f'<section class="gb-index-section"><div class="gb-file-list">{file_links}</div></section>'
                ),
                "experimentsPager": "",
            },
        )
        _write_page(
            OUT_DIR,
            f'experiments/{topic["topic_slug"]}/{subtopic["subtopic_path"]}/index.html',
            html,
        )

    def build_experiment(
        self, metadata: SiteMetadata, topic: ExperimentTopic, file_data: FileData, experiments: list[ExperimentTopic], subtopic_path: str | None = None
    ) -> None:
        """Build a single experiment file page."""
        rendered = _render_experiment_content(file_data, self.gfm_renderer)
        exp_url = _exp_file_url(topic["topic_slug"], subtopic_path, file_data["slug"])
        template = self.data_loader.load_template("experiment")
        html = self._build_common(
            template,
            metadata,
            f'{file_data["title"]} - {metadata["title"]}',
            f'Experiment: {file_data["title"]}',
            exp_url,
            extra_css=_DOCS_GITBOOK_EXTRA_CSS,
        )
        html = _apply_template(
            html,
            {
                "experimentsSidebar": _experiments_sidebar_html(
                    experiments,
                    {
                        "topic_slug": topic["topic_slug"],
                        "subtopic_path": subtopic_path,
                        "file_slug": file_data["slug"],
                    },
                ),
                "experiment.title": escape_html(file_data["title"]),
                "experiment.meta": escape_html(file_data["ext"].upper()),
                "experiment.content": rendered,
                "experimentsPager": _docs_pager(
                    _flatten_experiment_pages(experiments), exp_url
                ),
            },
        )
        exp_dir = f'experiments/{topic["topic_slug"]}'
        if subtopic_path:
            exp_dir += f'/{subtopic_path}'
        _write_page(OUT_DIR, f'{exp_dir}/{file_data["slug"]}.html', html)

    def build_about(self, metadata: SiteMetadata, author: dict, avatar: str) -> None:
        """Build the about page."""
        template = self.data_loader.load_template("about")
        site_url = metadata["siteUrl"].rstrip("/")

        main_entity = _main_entity_schema(metadata, site_url)
        about_page = {
            "@type": "ProfilePage",
            "name": f"About {metadata['author']}",
            "description": f"About {metadata['author']}",
            "url": site_url + "/about.html",
            "mainEntity": main_entity,
        }

        html = self._build_common(
            template,
            metadata,
            f"About - {metadata['title']}",
            f"About {metadata['author']}",
            "/about.html",
            extra_schemas=[about_page],
        )

        author_body = self.markdown_renderer.render(author["body"])

        html = _apply_template(
            html,
            {
                "metadata.author": escape_html(metadata["author"]),
                "author.occupation": escape_html(author.get("occupation", "")),
                "author.body": author_body,
                "avatar": avatar,
            },
        )

        _write_page(OUT_DIR, "about.html", html)

    def build_projects(self, metadata: SiteMetadata, projects: list[Project]) -> None:
        """Build the projects page."""
        template = self.data_loader.load_template("projects")

        best_rating = max((r.get("stars", 0) for r in projects), default=0)
        software_items = [
            _software_application_item(metadata, p, i, best_rating)
            for i, p in enumerate(projects, 1)
        ]
        collection_schema = _collection_schema(software_items)

        html = self._build_common(
            template,
            metadata,
            f"Projects - {metadata['title']}",
            f"Projects by {metadata['author']}",
            "/projects.html",
            extra_schemas=[collection_schema],
        )

        projects_list_html = (
            '<ul>\n'
            + "\n".join(
                f"""    <li><a href="{escape_html(p.get("website") or p["href"])}">{escape_html(p["title"])}</a> - <span class="desc">{escape_html(p.get("description", ""))}</span></li>"""
                for p in projects
            )
            + "\n</ul>"
        )

        html = _apply_template(html, {"projectsList": projects_list_html})
        _write_page(OUT_DIR, "projects.html", html)

    def build_bookshelf(self, metadata: SiteMetadata, books: dict) -> None:
        """Build the bookshelf page."""
        template = self.data_loader.load_template("bookshelf")

        category_configs = [
            {"label": "Curated", "dataKey": "curated", "tagClass": "tag-curated"},
            {
                "label": "Currently Reading",
                "dataKey": "currently-reading",
                "tagClass": "tag-current",
            },
            {"label": "Read", "dataKey": "read", "tagClass": "tag-read"},
        ]

        curated = books.get("curated", [])
        currently_reading = books.get("currently-reading", [])
        dedup_keys = set()
        for b in curated:
            dedup_keys.add(b["title"] + "||" + b.get("author", ""))
        for b in currently_reading:
            dedup_keys.add(b["title"] + "||" + b.get("author", ""))
        read_books = [
            b
            for b in books.get("read", [])
            if b["title"] + "||" + b.get("author", "") not in dedup_keys
        ]

        groups_data = [
            {**category_configs[0], "books": curated},
            {**category_configs[1], "books": currently_reading},
            {**category_configs[2], "books": read_books},
        ]
        groups = [g for g in groups_data if g["books"]]

        site_url = metadata["siteUrl"].rstrip("/")
        all_books = curated + currently_reading + read_books
        book_list_items = [
            _book_item(book, i, _resolve_book_image)
            for i, book in enumerate(all_books, 1)
        ]

        collection_schema = _collection_schema(
            book_list_items,
            name="Bookshelf",
            description="Books I've read",
            url=site_url + "/bookshelf.html",
        )

        html = self._build_common(
            template,
            metadata,
            f"Bookshelf - {metadata['title']}",
            "Books I've read",
            "/bookshelf.html",
            extra_schemas=[collection_schema],
        )

        html = _apply_template(
            html,
            {
                "bookshelfSection": _build_unified_bookcase(groups),
            },
        )

        _write_page(OUT_DIR, "bookshelf.html", html)

    def build_quotes(self, metadata: SiteMetadata, quotes: list[Quote]) -> None:
        """Build the quotes page."""
        template = self.data_loader.load_template("quotes")

        site_url = metadata["siteUrl"].rstrip("/")

        items_html = "\n".join(_render_quote_item(q) for q in quotes)
        quotes_list_html = f"<ul>\n{items_html}\n</ul>"

        html = self._build_common(
            template,
            metadata,
            f"Quotes - {metadata['title']}",
            "Quotes I like on Goodreads",
            "/quotes.html",
            extra_schemas=[
                {
                    "@type": "CollectionPage",
                    "name": "Quotes",
                    "description": "Quotes I like on Goodreads",
                    "url": site_url + "/quotes.html",
                }
            ],
        )

        html = _apply_template(html, {"quotesList": quotes_list_html})
        _write_page(OUT_DIR, "quotes.html", html)

    def build_tags(self, metadata: SiteMetadata, essays: list[Essay]) -> None:
        """Build the tags index and individual tag pages."""
        tag_map = {}
        for essay in essays:
            for tag in essay["tags"]:
                tag_map.setdefault(tag, []).append(essay)

        sorted_tags = sorted(tag_map.items(), key=lambda x: -len(x[1]))

        tags_index_template = self.data_loader.load_template("tags-index")
        tag_template = self.data_loader.load_template("tag")

        tags_index_html = self._build_common(
            tags_index_template,
            metadata,
            f"Tags - {metadata['title']}",
            "All tags",
            "/tags/",
        )
        tags_index_html = _apply_template(
            tags_index_html,
            {
                "tagsCount": str(len(sorted_tags)),
                "tagsList": "".join(
                    f'\n    <a href="{_tag_url(tag)}" class="tag">#{escape_html(tag)} <span class="count">{len(essays)}</span></a>'
                    for tag, essays in sorted_tags
                ),
            },
        )

        _write_page(OUT_DIR, "tags/index.html", tags_index_html)

        for tag, tagged_essays in tag_map.items():
            tag_html = self._build_common(
                tag_template,
                metadata,
                f"#{tag} - {metadata['title']}",
                f"Essays tagged with {tag}",
                _tag_url(tag),
            )
            count_label = "essays" if len(tagged_essays) != 1 else "essay"
            tag_html = _apply_template(
                tag_html,
                {
                    "tag": escape_html(tag),
                    "taggedEssaysCount": str(len(tagged_essays)),
                    "taggedEssaysCountLabel": count_label,
                    "taggedEssays": "\n".join(
                        _essay_article_html(e, tags=False)
                        for e in tagged_essays
                    ),
                },
            )

            _write_page(OUT_DIR, f"tags/{tag}.html", tag_html)

    def build_sitelinks(self, metadata: SiteMetadata, essays: list[Essay], projects: list[Project], notes: list[NoteTopic], experiments: list[ExperimentTopic]) -> None:
        """Build the site links page."""
        template = self.data_loader.load_template("sitelinks")
        html = self._build_common(
            template,
            metadata,
            f"Site Links - {metadata['title']}",
            "All internal links on this site",
            "/sitelinks.html",
        )

        site_url = metadata["siteUrl"].rstrip("/")
        site_hostname = urlparse(site_url).hostname

        static_pages = [
            ("/", "Home"),
            ("/essays/", "Essays"),
            ("/about.html", "About"),
            ("/projects.html", "Projects"),
            ("/bookshelf.html", "Bookshelf"),
            ("/notes/", "Notes"),
            ("/experiments/", "Experiments"),
            ("/quotes.html", "Quotes"),
            ("/tags/", "Tags"),
            ("/static/resume/prakash_s_resume.pdf", "Resume"),
        ]

        static_pages_html = "\n".join(
            f'    <li><a href="{url}">{escape_html(label)}</a></li>'
            for url, label in static_pages
        )

        essay_links_html = "\n".join(
            f'    <li><a href="{_essay_url(e["slug"])}">{escape_html(e["title"])}</a> <span class="meta">{_format_date(e["date"])}</span></li>'
            for e in essays
        )

        tag_set = set()
        for e in essays:
            tag_set.update(e["tags"])
        tags_sorted = sorted(tag_set)
        tag_links_html = "\n".join(
            f'    <li><a href="{_tag_url(t)}">#{escape_html(t)}</a></li>'
            for t in tags_sorted
        )

        same_domain_projects = []
        for p in projects:
            website = p.get("website")
            if not website:
                continue
            hostname = urlparse(website).hostname
            if hostname == site_hostname:
                same_domain_projects.append(p)

        project_links_html = "\n".join(
            f'    <li><a href="{escape_html(p["website"])}">{escape_html(p["title"])}</a></li>'
            for p in same_domain_projects
        )

        notes_links_html = "\n".join(
            f'    <li><a href="{_note_topic_url(n["topic_slug"])}">{escape_html(n["topic_title"])}</a></li>'
            for n in notes
        )

        experiment_links = []
        for exp in experiments:
            experiment_links.append(
                f'    <li><a href="{_topic_url(exp["topic_slug"])}">{escape_html(exp["topic_title"])}</a></li>'
            )
        experiment_links_html = "\n".join(experiment_links)

        html = _apply_template(
            html,
            {
                "staticPages": static_pages_html,
                "essayLinks": essay_links_html,
                "essayCount": str(len(essays)),
                "tagLinks": tag_links_html,
                "tagCount": str(len(tags_sorted)),
                "projectLinks": project_links_html,
                "projectCount": str(len(same_domain_projects)),
                "notesLinks": notes_links_html,
                "notesCount": str(len(notes)),
                "experimentLinks": experiment_links_html,
                "experimentCount": str(len(experiments)),
            },
        )

        _write_page(OUT_DIR, "sitelinks.html", html)


def _setup_logging() -> None:
    """Configure console logging for the build process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )


def build_site() -> None:
    """Build the entire static site into the out/ directory."""
    data_dir = pathlib.Path.cwd() / "data" / "non-public"
    data_loader = DataLoader(data_dir)
    markdown_renderer = MarkdownRenderer()
    gfm_renderer = MarkdownRenderer(gfm=True)
    page_builder = PageBuilder(data_loader, markdown_renderer, gfm_renderer)
    public_dir = pathlib.Path.cwd() / "data" / "public"

    _logger.info("Reading data...")
    metadata = data_loader.read_site_metadata()
    author = data_loader.read_author()
    essays = data_loader.get_essays()
    books = data_loader.get_books()
    precept = data_loader.get_precept()
    projects = data_loader.get_projects()
    leetcode_solutions = data_loader.get_leetcode_solutions()
    quotes = data_loader.get_quotes()
    notes = data_loader.get_notes()
    experiments = data_loader.get_experiments()

    _logger.info(
        "Found %d essays, %d projects, %d leetcode solutions, %d quotes, %d notes, %d experiment topics",
        len(essays),
        len(projects),
        len(leetcode_solutions),
        len(quotes),
        len(notes),
        len(experiments),
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(OUT_DIR)
    if public_dir.exists():
        shutil.copytree(public_dir, OUT_DIR, dirs_exist_ok=True)

    _logger.info("Building pages...")
    avatar = f"{BASE_PATH}/static/images/avatar.jpg"
    page_builder.build_home(metadata, essays, books, projects, author, avatar, precept)
    page_builder.build_essays_list(metadata, essays)
    for essay in essays:
        page_builder.build_essay(metadata, essay)
    page_builder.build_tags(metadata, essays)
    page_builder.build_about(metadata, author, avatar)
    page_builder.build_projects(metadata, projects)
    page_builder.build_bookshelf(metadata, books)
    page_builder.build_quotes(metadata, quotes)
    page_builder.build_notes_list(metadata, notes)
    for topic in notes:
        page_builder.build_note_topic_index(metadata, topic, notes)
        for f in topic["files"]:
            page_builder.build_note(metadata, topic, f, notes)
        for st in topic["subtopics"]:
            page_builder.build_note_subtopic_index(metadata, topic, st, notes)
            for f in st["files"]:
                page_builder.build_note(
                    metadata, topic, f, notes, subtopic_path=st["subtopic_path"]
                )
    page_builder.build_experiments_list(metadata, experiments)
    for exp in experiments:
        page_builder.build_topic_index(metadata, exp, experiments)
        for f in exp["files"]:
            page_builder.build_experiment(metadata, exp, f, experiments)
        for st in exp["subtopics"]:
            page_builder.build_subtopic_index(metadata, exp, st, experiments)
            for f in st["files"]:
                page_builder.build_experiment(
                    metadata, exp, f, experiments, subtopic_path=st["subtopic_path"]
                )
    page_builder.build_sitelinks(metadata, essays, projects, notes, experiments)

    _logger.info("Generating RSS, sitemap, and robots.txt...")
    (OUT_DIR / "feed.xml").write_text(
        generate_rss_feed(metadata, essays)
    )
    (OUT_DIR / "sitemap.xml").write_text(
        generate_sitemap(
            metadata, essays, projects, leetcode_solutions, notes, experiments
        )
    )
    (OUT_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {metadata['siteUrl']}sitemap.xml"
    )

    _logger.info("Done! Static site generated in out/")


def main() -> None:
    """Entry point: configure logging and build the site."""
    _setup_logging()
    build_site()


if __name__ == "__main__":
    main()
