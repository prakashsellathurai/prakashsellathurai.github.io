"""Page rendering and HTML generation."""

from __future__ import annotations

import pathlib
import re
import subprocess
from datetime import datetime
from urllib.parse import urlparse

from lib.dataloader import DataLoader
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
from lib.dates import format_date, format_date_iso
from lib.markdown import MarkdownRenderer, escape_html
from lib.rendering import (
    apply_template,
    build_toc,
    extract_body,
    heading_to_id,
    note_description,
    panel_section,
    render_experiment_content,
    render_markdown,
    render_notebook,
    render_code_as_notebook,
    sidebar_tree_html,
    write_page,
    _LINK_RE,
)
from lib.seo import (
    blog_posting_schema,
    book_item,
    breadcrumbs_for_url,
    build_author_schema,
    collection_schema,
    main_entity_schema,
    person_schema,
    software_application_item,
    website_schema,
)
from lib.slug import slug
from lib.url import (
    essay_url,
    exp_file_url,
    flatten_experiment_pages,
    flatten_note_pages,
    note_file_url,
    note_topic_url,
    tag_url,
    topic_url,
)

import logging

_logger = logging.getLogger(__name__)

OUT_DIR = pathlib.Path("out")


def _recent_notes(notes: list[NoteTopic], limit: int = 5) -> list[tuple[NoteTopic, FileData, str | None]]:
    """Return the most recently committed note files across all topics."""
    grimoire_dir = pathlib.Path("data/non-public/submodules/Grimoire")
    candidates: list[tuple[int, NoteTopic, FileData, str | None]] = []
    for note in notes:
        for st in note["subtopics"]:
            for f in st["files"]:
                rel = pathlib.Path("notes") / note["topic"] / st["subtopic_path"] / f["filename"]
                candidates.append((_note_commit_time(grimoire_dir, rel), note, f, st["subtopic_path"]))
        for f in note["files"]:
            rel = pathlib.Path("notes") / note["topic"] / f["filename"]
            candidates.append((_note_commit_time(grimoire_dir, rel), note, f, None))
    candidates.sort(key=lambda c: c[0], reverse=True)
    return [(note, f, st_path) for _, note, f, st_path in candidates[:limit]]


def _recent_experiments(experiments: list[ExperimentTopic], limit: int = 5) -> list[tuple[ExperimentTopic, FileData, str | None]]:
    """Return the most recently committed experiment files across all topics."""
    grimoire_dir = pathlib.Path("data/non-public/submodules/Grimoire")
    candidates: list[tuple[int, ExperimentTopic, FileData, str | None]] = []
    for exp in experiments:
        for st in exp["subtopics"]:
            for f in st["files"]:
                rel = pathlib.Path("experiments") / exp["topic"] / st["subtopic_path"] / f["filename"]
                candidates.append((_note_commit_time(grimoire_dir, rel), exp, f, st["subtopic_path"]))
        for f in exp["files"]:
            rel = pathlib.Path("experiments") / exp["topic"] / f["filename"]
            candidates.append((_note_commit_time(grimoire_dir, rel), exp, f, None))
    candidates.sort(key=lambda c: c[0], reverse=True)
    return [(exp, f, st_path) for _, exp, f, st_path in candidates[:limit]]


def _note_commit_time(grimoire_dir: pathlib.Path, rel_path: pathlib.Path) -> int:
    """Return the last commit timestamp for a note file in the Grimoire submodule."""
    try:
        result = subprocess.run(
            ["git", "-C", str(grimoire_dir), "log", "-1", "--format=%ct", "--", rel_path.as_posix()],
            capture_output=True,
            text=True,
            check=True,
        )
        ts = result.stdout.strip()
        return int(ts) if ts else 0
    except (subprocess.CalledProcessError, OSError, ValueError):
        return 0


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
                f'<a class="content-pager-{direction} disabled" href="#" tabindex="-1">'
                f'<span class="content-pager-label">{arrow} {label}</span>'
                f'<span class="content-pager-title"></span></a>'
            )
        return (
            f'<a class="content-pager-{direction}" href="{get_href(item)}">'
            f'<span class="content-pager-label">{arrow} {label}</span>'
            f'<span class="content-pager-title">{escape_html(item["title"])}</span></a>'
        )

    return f"""<nav class="content-pager" aria-label="{aria_label}">
  {cell("prev", prev_item)}
  {cell("next", next_item)}
</nav>"""


def _docs_pager(items: list[dict], current_url: str) -> str:
    return _pager_html(
        items, current_url, lambda i: i["url"], lambda i: i["url"],
        "Documents navigation",
    )


def _notes_pager_html(notes: list[NoteTopic], current_url: str) -> str:
    return _docs_pager(flatten_note_pages(notes), current_url)


def _essay_article_html(e: Essay, indent: int = 0, tags: bool = True) -> str:
    p = " " * indent
    i = p + "  "
    t = ""
    if tags:
        t = "".join(
            f'<a href="{tag_url(tag)}">#{escape_html(tag)}</a>'
            for tag in e["tags"][:3]
        )
        t = f'{i}<div class="tags">\n{i}  {t}\n{i}</div>\n'
    return (
        f'{p}<article class="essay-item">\n'
        f'{i}<h2><a href="{essay_url(e["slug"])}">{escape_html(e["title"])}</a></h2>\n'
        f'{i}<p class="meta"><time>{format_date(e["date"])}</time></p>\n'
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


def _essays_sidebar_html(essays: list[Essay]) -> str:
    """Return a flat list of essay links as a wiki-panel portal section."""
    links = "\n".join(
        f'      <a class="nav-tree-file" href="{essay_url(e["slug"])}">{escape_html(e["title"])}</a>'
        for e in essays
    )
    return panel_section("Essays", f"    <div class=\"nav-tree-inner\">\n{links}\n    </div>", "site-essays")


def _notes_sidebar_html(notes: list[NoteTopic], current: dict | None = None) -> str:
    """Return the notes tree as a wiki-panel portal section."""
    tree = sidebar_tree_html(
        notes,
        current,
        note_file_url,
        "topic_title",
        "topic_slug",
        "notes",
    )
    return panel_section("Notes", tree, "site-notes")


def _experiments_sidebar_html(experiments: list[ExperimentTopic], current: dict | None = None) -> str:
    """Return the experiments tree as a wiki-panel portal section."""
    tree = sidebar_tree_html(
        experiments,
        current,
        exp_file_url,
        "topic_title",
        "topic_slug",
        "experiments",
    )
    return panel_section("Experiments", tree, "p-experiments")


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
    json_ld_str = __import__("json").dumps(json_ld_obj, indent=2)
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


def render_head(metadata: SiteMetadata, page_info: dict, extra_schemas=None, extra_css=None, noindex: bool = False) -> str:
    """Render the <head> HTML for a page."""
    site_url = metadata["siteUrl"].rstrip("/")
    full_url = f"{site_url}{page_info['url']}" if page_info["url"] else site_url
    og_image = (
        page_info.get("image")
        or metadata.get("socialBanner")
        or metadata.get("siteLogo", "")
    )

    canonical = f'<link rel="canonical" href="{full_url}">'
    noindex_meta = '<meta name="robots" content="noindex, nofollow">' if noindex else ""

    schemas = [
        website_schema(site_url, metadata["title"]),
        person_schema(metadata, site_url),
    ]
    breadcrumbs = breadcrumbs_for_url(page_info.get("url", ""), site_url)
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
  {noindex_meta}
  {_render_open_graph(page_info, site_url, full_url, og_image, metadata["title"])}
  {_render_twitter_card(page_info, site_url, og_image)}
  {_render_json_ld(schemas)}
  {rss_link}
  {_FAVICON_LINKS}
  <script>(function(){{var t;try{{t=localStorage.getItem("theme")}}catch(e){{}}if(!t)t=window.matchMedia&&window.matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light";document.documentElement.setAttribute("data-theme",t)}})()</script>
  {_render_css_link(extra_css)}
</head>
"""


def _personal_tools_html(metadata: SiteMetadata) -> str:
    links = []
    for label, key in (("GitHub", "github"), ("LinkedIn", "linkedin"), ("Instagram", "instagram")):
        url = metadata.get(key)
        if url:
            links.append(f'<li><a href="{escape_html(url)}" rel="me">{escape_html(label)}</a></li>')
    links.append('<li><a href="/feed.xml">RSS</a></li>')
    return f'<ul>{"".join(links)}</ul>'


def _search_html(metadata: SiteMetadata) -> str:
    domain = metadata["siteUrl"].rstrip("/").split("//", 1)[-1]
    return f"""<form action="https://www.google.com/search" method="get" role="search" data-site-domain="{escape_html(domain)}">
<input type="search" name="q" placeholder="Search this site" aria-label="Search" data-search>
<button type="submit" aria-label="Search"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg></button></form>"""


def _nav_links_html(metadata: SiteMetadata) -> str:
    items = [
        ("/", "Main page"),
        ("/essays/", "Essays"),
        ("/projects.html", "Projects"),
        ("/bookshelf.html", "Bookshelf"),
        ("/notes/", "Notes"),
        ("/experiments/", "Experiments"),
        ("/quotes.html", "Quotes"),
        ("/about.html", "About"),
        ("/tags/", "Tags"),
        ("/static/resume/prakash_s_resume.pdf", "Resume"),
    ]
    return f'<ul>{"".join(f'<li><a href="{url}">{label}</a></li>' for url, label in items)}</ul>'


def _tools_links_html(metadata: SiteMetadata) -> str:
    items = [
        ("/sitelinks.html", "Site links"),
        ("/feed.xml", "RSS feed"),
    ]
    github = metadata.get("github")
    if github:
        items.append((github, "GitHub profile"))
    return f'<ul>{"".join(f'<li><a href="{url}">{label}</a></li>' for url, label in items)}</ul>'


def render_header(metadata: SiteMetadata, sidebar_html: str = "", main_class: str = "") -> str:
    extra = f" {main_class}" if main_class else ""
    return f"""<input type="checkbox" id="nav-toggle" class="nav-toggle" aria-hidden="true">
<label for="nav-toggle" class="nav-burger" aria-label="Toggle navigation"><span>&#9776;</span></label>
<header id="site-header">
  <div id="site-logo">
    <a href="/" aria-label="Home">
      <span class="logo-initials">PS</span>
    </a>
  </div>
  <div id="site-personal">{_personal_tools_html(metadata)}<button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">&#127769;</button></div>
  <div id="site-search">{_search_html(metadata)}</div>
</header>
<aside id="site-sidebar">
  {panel_section("Navigation", _nav_links_html(metadata), "site-navigation")}
  {sidebar_html}
  {panel_section("Tools", _tools_links_html(metadata), "site-tools")}
</aside>
<main id="content" class="site-main{extra}">
  <div id="bodyContent">
"""


def render_footer(metadata: SiteMetadata) -> str:
    year = datetime.now().year
    return f"""  </div>
</main>
<footer id="footer">
  <div id="footer-places">
    <h3>Places</h3>
    <ul>
      <li><a href="/about.html">About</a></li>
      <li><a href="/sitelinks.html">Site links</a></li>
      <li><a href="/feed.xml">RSS</a></li>
    </ul>
  </div>
  <div id="footer-text">
    <h3>{escape_html(metadata['author'])}</h3>
    <p>&copy; {year} {escape_html(metadata['author'])}. All rights reserved.</p>
    <p>This page is written and maintained by {escape_html(metadata['author'])}.</p>
  </div>
  <div id="footer-icons">
    <h3>Elsewhere</h3>
    <ul>
      {f'<li><a href="{escape_html(metadata["github"])}">GitHub</a></li>' if metadata.get("github") else ''}
      {f'<li><a href="{escape_html(metadata["linkedin"])}">LinkedIn</a></li>' if metadata.get("linkedin") else ''}
    </ul>
  </div>
</footer>
<script src="/static/js/search.js"></script>
<script src="/static/js/theme.js"></script>
"""


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
        sidebar_html: str = "",
        main_class: str = "",
        noindex: bool = False,
    ) -> str:
        """Fill a template's head/header/footer with site-wide HTML."""
        return apply_template(
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
                    noindex=noindex,
                ),
                "header": render_header(metadata, sidebar_html=sidebar_html, main_class=main_class),
                "footer": render_footer(metadata),
                "metadata.author": escape_html(metadata["author"]),
            },
        )

    def build_home(self, metadata: SiteMetadata, essays: list[Essay], books: dict, projects: list[Project], author: dict, avatar: str, precept: dict, quotes: list[Quote], experiments: list[ExperimentTopic], notes: list[NoteTopic]) -> None:
        """Build the homepage (index.html)."""
        template = self.data_loader.load_template("home")
        html = self._build_common(
            template, metadata, metadata["title"], metadata["description"], "/",
            sidebar_html=_essays_sidebar_html(essays),
        )

        featured = _essay_article_html(essays[0], indent=4) if essays else ""
        featured += '\n    <p class="section-footer"><a href="/essays/">All essays &rarr;</a></p>'

        did_you_know_html = "\n".join(_render_quote_item(q) for q in quotes[:4])
        if did_you_know_html:
            did_you_know_html = f'    <ul>\n{did_you_know_html}\n    </ul>'

        recent_experiments = _recent_experiments(experiments)
        in_the_news_html = "\n".join(
            f'    <li><a href="{exp_file_url(exp["topic_slug"], st_path, f["slug"])}">{escape_html(f["title"])}</a>'
            f' <span class="meta">{escape_html(exp["topic_title"])}</span></li>'
            for exp, f, st_path in recent_experiments
        )
        if in_the_news_html:
            in_the_news_html = f"    <ul>\n{in_the_news_html}\n    </ul>"

        on_this_day_html = "\n".join(
            f'    <li><a href="{escape_html(p["link"])}" target="_blank" rel="noopener">{escape_html(p["title"])}</a></li>'
            for p in (precept[:5] or [])
        )
        if on_this_day_html:
            on_this_day_html = f"    <ul>\n{on_this_day_html}\n    </ul>"

        recent_notes_html = "\n".join(
            f'    <li><a href="{note_file_url(note["topic_slug"], st_path, f["slug"])}">{escape_html(f["title"])}</a>'
            f' <span class="meta">{escape_html(note["topic_title"])}</span></li>'
            for note, f, st_path in _recent_notes(notes)
        )
        if recent_notes_html:
            recent_notes_html = (
                f"    <ul>\n{recent_notes_html}\n    </ul>"
                '\n    <p class="section-footer"><a href="/notes/">All notes &rarr;</a></p>'
            )

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

        first_para = author["body"].split("\n\n")[0] if author["body"] else ""

        html = apply_template(
            html,
            {
                "featuredArticle": featured,
                "didYouKnow": did_you_know_html,
                "inTheNews": in_the_news_html,
                "onThisDay": on_this_day_html,
                "recentNotes": recent_notes_html,
                "featuredProjects": featured_projects_html,
                "metadata.shortDescription": escape_html(
                    first_para or metadata["description"]
                ),
                "metadata.author": escape_html(metadata["author"]),
                "avatar": avatar,
            },
        )

        write_page(OUT_DIR, "index.html", html)

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

        html = apply_template(html, {"essaysList": essays_list_html})

        write_page(OUT_DIR, "essays/index.html", html)

    def build_essay(self, metadata: SiteMetadata, essay: Essay) -> None:
        """Build a single essay page."""
        template = self.data_loader.load_template("essay")
        site_url = metadata["siteUrl"].rstrip("/")
        essay_url_val = essay_url(essay["slug"])

        blog_posting = blog_posting_schema(metadata, essay, site_url, essay_url_val)

        html = self._build_common(
            template,
            metadata,
            f"{essay['title']} - {metadata['title']}",
            essay["summary"],
            essay_url_val,
            extra_schemas=[blog_posting],
        )

        essay_content = self.markdown_renderer.render(essay["content"])
        essay_content, toc_html = build_toc(essay_content)

        html = apply_template(
            html,
            {
                "toc": toc_html,
                "essay.title": escape_html(essay["title"]),
                "essay.date": format_date(essay["date"]),
                "essay.tags": " ".join(
                    f'<a href="{tag_url(t)}">#{escape_html(t)}</a>'
                    for t in essay["tags"]
                ),
                "essay.content": essay_content,
            },
        )

        write_page(OUT_DIR, f"essays/{essay['slug']}.html", html)

    def build_notes_list(self, metadata: SiteMetadata, notes: list[NoteTopic]) -> None:
        """Build the notes index page."""
        template = self.data_loader.load_template("notes")
        html = self._build_common(
            template,
            metadata,
            f"Notes - {metadata['title']}",
            "Quick references and notes",
            "/notes/",
            sidebar_html=_notes_sidebar_html(notes),
            main_class="page-note",
        )

        sections = []
        for note in notes:
            file_links = []
            for st in note["subtopics"]:
                for f in st["files"]:
                    file_links.append(
                        f'        <li><a class="content-file-link" href="{note_file_url(note["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">note</span></a></li>'
                    )
            for f in note["files"]:
                file_links.append(
                    f'        <li><a class="content-file-link" href="{note_file_url(note["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">note</span></a></li>'
                )
            sections.append(
                f'<section class="content-index-section"><h2><a class="content-topic-title" href="{note_topic_url(note["topic_slug"])}">{escape_html(note["topic_title"])}</a></h2>'
                f'<ul class="content-file-list">\n{"".join(file_links)}\n    </ul></section>'
            )

        html = apply_template(
            html,
            {
                "notesTitle": "Notes",
                "notesLead": "Quick references and notes on various topics",
                "notesContent": "\n".join(sections),
            },
        )

        write_page(OUT_DIR, "notes/index.html", html)

    def build_note_topic_index(self, metadata: SiteMetadata, topic: NoteTopic, notes: list[NoteTopic]) -> None:
        """Build a note topic index page."""
        template = self.data_loader.load_template("notes")
        t_url = note_topic_url(topic["topic_slug"])
        html = self._build_common(
            template,
            metadata,
            f'{topic["topic_title"]} - Notes - {metadata["title"]}',
            f'Notes in {topic["topic_title"]}',
            t_url,
            sidebar_html=_notes_sidebar_html(
                notes, {"topic_slug": topic["topic_slug"]}
            ),
            main_class="page-note",
        )
        sections = []
        for st in topic["subtopics"]:
            file_links = "\n".join(
                f'        <li><a class="content-file-link" href="{note_file_url(topic["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">note</span></a></li>'
                for f in st["files"]
            )
            sections.append(
                f'<section class="content-index-section"><h2>{escape_html(st["subtopic_title"])}</h2>'
                f'<ul class="content-file-list">\n{file_links}\n    </ul></section>'
            )
        if topic["files"]:
            file_links = "\n".join(
                f'        <li><a class="content-file-link" href="{note_file_url(topic["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">note</span></a></li>'
                for f in topic["files"]
            )
            sections.append(
                f'<section class="content-index-section"><h2>Notes</h2><ul class="content-file-list">\n{file_links}\n    </ul></section>'
            )
        html = apply_template(
            html,
            {
                "notesTitle": escape_html(topic["topic_title"]),
                "notesLead": f'Notes in {topic["topic_title"]}',
                "notesContent": "\n".join(sections),
            },
        )
        write_page(OUT_DIR, f'notes/{topic["topic_slug"]}/index.html', html)

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
            sidebar_html=_notes_sidebar_html(
                notes,
                {
                    "topic_slug": topic["topic_slug"],
                    "subtopic_path": subtopic["subtopic_path"],
                },
            ),
            main_class="page-note",
        )
        file_links = "\n".join(
            f'        <li><a class="content-file-link" href="{note_file_url(topic["topic_slug"], subtopic["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">note</span></a></li>'
            for f in subtopic["files"]
        )
        html = apply_template(
            html,
            {
                "notesTitle": escape_html(subtopic["subtopic_title"]),
                "notesLead": f'Notes in {topic["topic_title"]} / {subtopic["subtopic_title"]}',
                "notesContent": f'<section class="content-index-section"><ul class="content-file-list">\n{file_links}\n    </ul></section>',
            },
        )
        write_page(
            OUT_DIR,
            f'notes/{topic["topic_slug"]}/{subtopic["subtopic_path"]}/index.html',
            html,
        )

    def build_note(self, metadata: SiteMetadata, topic: NoteTopic, file_data: FileData, notes: list[NoteTopic], subtopic_path: str | None = None) -> None:
        """Build a single note page."""
        template = self.data_loader.load_template("note")
        n_url = note_file_url(topic["topic_slug"], subtopic_path, file_data["slug"])

        note_content = self.gfm_renderer.render(file_data["content"])
        note_content, toc_html = build_toc(note_content)

        html = self._build_common(
            template,
            metadata,
            f"{file_data['title']} - Notes - {metadata['title']}",
            f"Notes on {file_data['title']}",
            n_url,
            sidebar_html=_notes_sidebar_html(
                notes,
                {
                    "topic_slug": topic["topic_slug"],
                    "subtopic_path": subtopic_path,
                    "file_slug": file_data["slug"],
                },
            ),
            main_class="page-note",
        )

        html = apply_template(
            html,
            {
                "toc": toc_html,
                "note.title": escape_html(file_data["title"]),
                "note.content": note_content,
                "notesPager": _notes_pager_html(notes, n_url),
            },
        )

        note_dir = f'notes/{topic["topic_slug"]}'
        if subtopic_path:
            note_dir += f'/{subtopic_path}'
        write_page(OUT_DIR, f'{note_dir}/{file_data["slug"]}.html', html)

    def build_experiments_list(self, metadata: SiteMetadata, experiments: list[ExperimentTopic]) -> None:
        """Build the experiments index page."""
        template = self.data_loader.load_template("experiments")
        html = self._build_common(
            template,
            metadata,
            f"Experiments - {metadata['title']}",
            "Document explorations and experiments",
            "/experiments/",
            sidebar_html=_experiments_sidebar_html(experiments),
            main_class="page-experiment",
        )
        sections = []
        for exp in experiments:
            file_links = []
            for st in exp["subtopics"]:
                for f in st["files"]:
                    file_links.append(
                        f'        <li><a class="content-file-link" href="{exp_file_url(exp["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">{escape_html(f["ext"].upper())} file</span></a></li>'
                    )
            for f in exp["files"]:
                file_links.append(
                    f'        <li><a class="content-file-link" href="{exp_file_url(exp["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">{escape_html(f["ext"].upper())} file</span></a></li>'
                )
            sections.append(
                f'<section class="content-index-section"><h2><a class="content-topic-title" href="{topic_url(exp["topic_slug"])}">{escape_html(exp["topic_title"])}</a></h2>'
                f'<ul class="content-file-list">\n{"".join(file_links)}\n    </ul></section>'
            )
        html = apply_template(
            html,
            {
                "experimentsTitle": "Experiments",
                "experimentsLead": "Code experiments and explorations",
                "experimentsContent": "\n".join(sections),
                "experimentsPager": "",
            },
        )
        write_page(OUT_DIR, "experiments/index.html", html)

    def build_topic_index(self, metadata: SiteMetadata, topic: ExperimentTopic, experiments: list[ExperimentTopic]) -> None:
        """Build an experiment topic index page."""
        template = self.data_loader.load_template("experiments")
        t_url = topic_url(topic["topic_slug"])
        html = self._build_common(
            template,
            metadata,
            f'{topic["topic_title"]} - Experiments - {metadata["title"]}',
            f'Experiments in {topic["topic_title"]}',
            t_url,
            sidebar_html=_experiments_sidebar_html(
                experiments, {"topic_slug": topic["topic_slug"]}
            ),
            main_class="page-experiment",
        )
        sections = []
        for st in topic["subtopics"]:
            file_links = "\n".join(
                f'        <li><a class="content-file-link" href="{exp_file_url(topic["topic_slug"], st["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">{escape_html(f["ext"].upper())} file</span></a></li>'
                for f in st["files"]
            )
            sections.append(
                f'<section class="content-index-section"><h2>{escape_html(st["subtopic_title"])}</h2>'
                f'<ul class="content-file-list">\n{file_links}\n    </ul></section>'
            )
        if topic["files"]:
            file_links = "\n".join(
                f'        <li><a class="content-file-link" href="{exp_file_url(topic["topic_slug"], None, f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">{escape_html(f["ext"].upper())} file</span></a></li>'
                for f in topic["files"]
            )
            sections.append(
                f'<section class="content-index-section"><h2>Files</h2><ul class="content-file-list">\n{file_links}\n    </ul></section>'
            )
        html = apply_template(
            html,
            {
                "experimentsTitle": escape_html(topic["topic_title"]),
                "experimentsLead": f'Experiments in {topic["topic_title"]}',
                "experimentsContent": "\n".join(sections),
                "experimentsPager": "",
            },
        )
        write_page(
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
            sidebar_html=_experiments_sidebar_html(
                experiments,
                {
                    "topic_slug": topic["topic_slug"],
                    "subtopic_path": subtopic["subtopic_path"],
                },
            ),
            main_class="page-experiment",
        )
        file_links = "\n".join(
            f'        <li><a class="content-file-link" href="{exp_file_url(topic["topic_slug"], subtopic["subtopic_path"], f["slug"])}">{escape_html(f["title"])}<span class="content-file-meta">{escape_html(f["ext"].upper())} file</span></a></li>'
            for f in subtopic["files"]
        )
        html = apply_template(
            html,
            {
                "experimentsTitle": escape_html(subtopic["subtopic_title"]),
                "experimentsLead": f'Experiments in {topic["topic_title"]} / {subtopic["subtopic_title"]}',
                "experimentsContent": (
                    f'<section class="content-index-section"><ul class="content-file-list">\n{file_links}\n    </ul></section>'
                ),
                "experimentsPager": "",
            },
        )
        write_page(
            OUT_DIR,
            f'experiments/{topic["topic_slug"]}/{subtopic["subtopic_path"]}/index.html',
            html,
        )

    def build_experiment(
        self, metadata: SiteMetadata, topic: ExperimentTopic, file_data: FileData, experiments: list[ExperimentTopic], subtopic_path: str | None = None
    ) -> None:
        """Build a single experiment file page."""
        rendered = render_experiment_content(file_data, self.gfm_renderer)
        rendered, toc_html = build_toc(rendered)
        e_url = exp_file_url(topic["topic_slug"], subtopic_path, file_data["slug"])
        template = self.data_loader.load_template("experiment")

        is_raw_source = file_data["ext"] in {"py", "c", "cpp", "txt"}

        html = self._build_common(
            template,
            metadata,
            f'{file_data["title"]} - {metadata["title"]}',
            f'Experiment: {file_data["title"]}',
            e_url,
            sidebar_html=_experiments_sidebar_html(
                experiments,
                {
                    "topic_slug": topic["topic_slug"],
                    "subtopic_path": subtopic_path,
                    "file_slug": file_data["slug"],
                },
            ),
            main_class="page-experiment",
            noindex=is_raw_source,
        )
        html = apply_template(
            html,
            {
                "toc": toc_html,
                "experiment.title": escape_html(file_data["title"]),
                "experiment.meta": escape_html(file_data["ext"].upper()),
                "experiment.content": rendered,
                "experimentsPager": _docs_pager(
                    flatten_experiment_pages(experiments), e_url
                ),
            },
        )
        exp_dir = f'experiments/{topic["topic_slug"]}'
        if subtopic_path:
            exp_dir += f'/{subtopic_path}'
        write_page(OUT_DIR, f'{exp_dir}/{file_data["slug"]}.html', html)

    def build_about(self, metadata: SiteMetadata, author: dict, avatar: str) -> None:
        """Build the about page."""
        template = self.data_loader.load_template("about")
        site_url = metadata["siteUrl"].rstrip("/")

        main_entity = main_entity_schema(metadata, site_url)
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

        html = apply_template(
            html,
            {
                "metadata.author": escape_html(metadata["author"]),
                "author.occupation": escape_html(author.get("occupation", "")),
                "author.body": author_body,
                "avatar": avatar,
            },
        )

        write_page(OUT_DIR, "about.html", html)

    def build_projects(self, metadata: SiteMetadata, projects: list[Project]) -> None:
        """Build the projects page."""
        template = self.data_loader.load_template("projects")

        best_rating = max((r.get("stars", 0) for r in projects), default=0)
        software_items = [
            software_application_item(metadata, p, i, best_rating)
            for i, p in enumerate(projects, 1)
        ]
        c_schema = collection_schema(software_items)

        html = self._build_common(
            template,
            metadata,
            f"Projects - {metadata['title']}",
            f"Projects by {metadata['author']}",
            "/projects.html",
            extra_schemas=[c_schema],
        )

        projects_list_html = (
            '<ul>\n'
            + "\n".join(
                f"""    <li><a href="{escape_html(p.get("website") or p["href"])}">{escape_html(p["title"])}</a> - <span class="desc">{escape_html(p.get("description", ""))}</span></li>"""
                for p in projects
            )
            + "\n</ul>"
        )

        html = apply_template(html, {"projectsList": projects_list_html})
        write_page(OUT_DIR, "projects.html", html)

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
            book_item(b, i, _resolve_book_image)
            for i, b in enumerate(all_books, 1)
        ]

        c_schema = collection_schema(
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
            extra_schemas=[c_schema],
        )

        html = apply_template(
            html,
            {
                "bookshelfSection": _build_unified_bookcase(groups),
            },
        )

        write_page(OUT_DIR, "bookshelf.html", html)

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

        html = apply_template(html, {"quotesList": quotes_list_html})
        write_page(OUT_DIR, "quotes.html", html)

    def build_tags(self, metadata: SiteMetadata, essays: list[Essay]) -> None:
        """Build the tags index and individual tag pages."""
        tag_map = {}
        for essay in essays:
            for t in essay["tags"]:
                tag_map.setdefault(t, []).append(essay)

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
        tags_index_html = apply_template(
            tags_index_html,
            {
                "tagsCount": str(len(sorted_tags)),
                "tagsList": "".join(
                    f'\n    <a href="{tag_url(tag)}" class="tag">#{escape_html(tag)} <span class="count">{len(essays)}</span></a>'
                    for tag, essays in sorted_tags
                ),
            },
        )

        write_page(OUT_DIR, "tags/index.html", tags_index_html)

        for tag, tagged_essays in tag_map.items():
            tag_html = self._build_common(
                tag_template,
                metadata,
                f"#{tag} - {metadata['title']}",
                f"Essays tagged with {tag}",
                tag_url(tag),
            )
            count_label = "essays" if len(tagged_essays) != 1 else "essay"
            tag_html = apply_template(
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

            write_page(OUT_DIR, f"tags/{tag}.html", tag_html)

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
            f'    <li><a href="{essay_url(e["slug"])}">{escape_html(e["title"])}</a> <span class="meta">{format_date(e["date"])}</span></li>'
            for e in essays
        )

        tag_set = set()
        for e in essays:
            tag_set.update(e["tags"])
        tags_sorted = sorted(tag_set)
        tag_links_html = "\n".join(
            f'    <li><a href="{tag_url(t)}">#{escape_html(t)}</a></li>'
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
            f'    <li><a href="{note_topic_url(n["topic_slug"])}">{escape_html(n["topic_title"])}</a></li>'
            for n in notes
        )

        experiment_links = []
        for exp in experiments:
            experiment_links.append(
                f'    <li><a href="{topic_url(exp["topic_slug"])}">{escape_html(exp["topic_title"])}</a></li>'
            )
        experiment_links_html = "\n".join(experiment_links)

        html = apply_template(
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

        write_page(OUT_DIR, "sitelinks.html", html)
