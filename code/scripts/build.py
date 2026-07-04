#!/usr/bin/env python3
import json
import os
import pathlib
import re
import shutil
from datetime import datetime, timezone

from lib.frontmatter import parse_frontmatter
from lib.markdown import MarkdownRenderer

BASE_PATH = os.environ.get("BASE_PATH", "")


def _escape_html(text):
    if not text:
        return ""
    t = str(text)
    t = t.replace("&", "&amp;")
    t = t.replace("<", "&lt;")
    t = t.replace(">", "&gt;")
    t = t.replace('"', "&quot;")
    t = t.replace("'", "&#039;")
    return t


def _format_date_iso(date_str):
    d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return d.isoformat()


def _build_author_schema(metadata):
    details = metadata.get("authorDetails", {})
    author = {"@type": "Person", "name": metadata["author"]}
    for key in ("url", "sameAs", "email", "jobTitle", "image"):
        if key in details:
            author[key] = details[key]
    return author


def _format_date(date_str):
    d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return d.strftime("%b %d, %Y")


def _read_site_metadata(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    base_path = os.environ.get("BASE_PATH", "")

    content = content.replace("__BASE_PATH__", base_path)

    return json.loads(content)


class FileSystem:
    @staticmethod
    def ensure_dir(dir_path):
        pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clear_dir(dir_path):
        p = pathlib.Path(dir_path)
        if not p.exists():
            return
        for entry in p.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

    @staticmethod
    def copy_dir(src, dest):
        src_p = pathlib.Path(src)
        if not src_p.exists():
            return
        FileSystem.ensure_dir(dest)
        for entry in src_p.iterdir():
            s = str(entry)
            d = os.path.join(dest, entry.name)
            if entry.is_dir():
                FileSystem.copy_dir(s, d)
            else:
                shutil.copy2(s, d)

    @staticmethod
    def read(filepath):
        with open(filepath, "r") as f:
            return f.read()

    @staticmethod
    def write(filepath, content):
        with open(filepath, "w") as f:
            f.write(content)

    @staticmethod
    def exists(filepath):
        return os.path.exists(filepath)


class DataLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def read_json(self, filepath):
        with open(os.path.join(self.data_dir, filepath)) as f:
            return json.load(f)

    def read_md(self, filepath):
        content = FileSystem.read(filepath)
        return parse_frontmatter(content)

    def load_template(self, template_name):
        template_path = os.path.join(
            self.data_dir, "templates", f"{template_name}.html"
        )
        if not FileSystem.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        return FileSystem.read(template_path)

    def read_author(self):
        content = FileSystem.read(os.path.join(self.data_dir, "authors", "default.mdx"))
        parsed = parse_frontmatter(content)
        return {**parsed["data"], "body": parsed["content"]}

    def read_site_metadata(self):
        filepath = os.path.join(self.data_dir, "siteMetadata.json")
        return _read_site_metadata(filepath)

    def get_essays(self):
        essays_dir = os.path.join(self.data_dir, "essays")
        files = [f for f in os.listdir(essays_dir) if f.endswith(".md")]
        result = []
        for file in files:
            parsed = self.read_md(os.path.join(essays_dir, file))
            if parsed["data"].get("draft"):
                continue
            data = parsed["data"]
            result.append(
                {
                    "slug": file.replace(".md", ""),
                    "title": data.get("title", ""),
                    "date": data.get("date", ""),
                    "summary": data.get("summary", ""),
                    "tags": data.get("tags", []),
                    "content": parsed["content"],
                }
            )
        result.sort(key=lambda x: x["date"], reverse=True)
        return result

    def get_books(self):
        return self.read_json("books.json")

    def get_precept(self):
        return self.read_json("precept.json")

    def get_projects(self):
        return self.read_json("repos.json")

    def get_leetcode_solutions(self):
        return self.read_json("leetcode-solutions.json")


class TemplateRenderer:
    @staticmethod
    def _breadcrumbs_for_url(url, site_url):
        if not url or url == "/":
            return None

        page_names = {
            "/essays/": "Essays",
            "/about.html": "About",
            "/projects.html": "Projects",
            "/bookshelf.html": "Bookshelf",
            "/tags/": "Tags",
        }

        items = []

        if url in page_names:
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
                    "item": {"@id": site_url + url, "name": page_names[url]},
                }
            )
        else:
            parts = url.strip("/").split("/")
            if len(parts) >= 2:
                parent_path = "/" + parts[0] + "/"
                parent_name = page_names.get(
                    parent_path, parts[0].replace(".html", "").replace("-", " ").title()
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
                        "item": {"@id": site_url + parent_path, "name": parent_name},
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

    @staticmethod
    def render_head(metadata, page_info, extra_schemas=None):
        site_url = metadata["siteUrl"].rstrip("/")
        full_url = f"{site_url}{page_info['url']}" if page_info["url"] else site_url
        og_image = (
            page_info.get("image")
            or metadata.get("socialBanner")
            or metadata.get("siteLogo", "")
        )
        keywords = ", ".join(metadata.get("keywords", []))

        canonical = f'<link rel="canonical" href="{full_url}">'
        keywords_meta = (
            f'<meta name="keywords" content="{_escape_html(keywords)}">'
            if keywords
            else ""
        )

        open_graph = f"""
  <meta property="og:title" content="{_escape_html(page_info["title"])}">
  <meta property="og:description" content="{_escape_html(page_info["description"])}">
  <meta property="og:url" content="{full_url}">
  <meta property="og:image" content="{site_url}{og_image}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{_escape_html(metadata["title"])}">"""

        twitter_card = f"""
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{_escape_html(page_info["title"])}">
  <meta name="twitter:description" content="{_escape_html(page_info["description"])}">
  <meta name="twitter:image" content="{site_url}{og_image}">"""

        author_details = metadata.get("authorDetails", {})
        same_as = author_details.get("sameAs", [])
        author_name = metadata.get("author", "")
        job_title = author_details.get("jobTitle", "Software Engineer")
        author_desc = metadata.get("description", "")

        schemas = []

        schemas.append(
            {
                "@type": "WebSite",
                "url": site_url + "/",
                "name": metadata["title"],
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": site_url + "/?q={search_term_string}",
                    },
                    "query-input": "required name=search_term_string",
                },
            }
        )

        person_schema = {
            "@type": "Person",
            "name": author_name,
            "url": site_url,
            "sameAs": same_as,
            "jobTitle": job_title,
            "description": author_desc,
        }
        author_img = author_details.get("image") or metadata.get("siteLogo", "")
        if author_img:
            person_schema["image"] = site_url + author_img
        email = metadata.get("email")
        if email:
            person_schema["email"] = email
        knows_about = author_details.get("knowsAbout")
        if knows_about:
            person_schema["knowsAbout"] = knows_about
        schemas.append(person_schema)

        breadcrumbs = TemplateRenderer._breadcrumbs_for_url(
            page_info.get("url", ""), site_url
        )
        if breadcrumbs:
            schemas.append(breadcrumbs)

        if extra_schemas:
            schemas.extend(extra_schemas)

        if len(schemas) == 1:
            schemas[0]["@context"] = "https://schema.org"
            json_ld_obj = schemas[0]
        else:
            json_ld_obj = {"@context": "https://schema.org", "@graph": schemas}

        json_ld_str = json.dumps(json_ld_obj, indent=2)
        json_ld = f"""
  <script type="application/ld+json">
  {json_ld_str}
  </script>"""

        css_link = '<link rel="stylesheet" href="/static/css/style.css">'
        favicon = """
  <link rel="apple-touch-icon" sizes="180x180" href="/static/favicons/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/static/favicons/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/static/favicons/favicon-16x16.png">
  <link rel="manifest" href="/static/favicons/site.webmanifest">
  <link rel="mask-icon" href="/static/favicons/safari-pinned-tab.svg" color="#8b7355">"""

        rss_link = f'<link rel="alternate" type="application/rss+xml" title="{_escape_html(metadata["title"])}" href="{site_url}/feed.xml">'

        return f"""
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escape_html(page_info["title"])}</title>
  <meta name="description" content="{_escape_html(page_info["description"])}">
  {keywords_meta}
  {canonical}
  {open_graph}
  {twitter_card}
  {json_ld}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
  {rss_link}
  {favicon}
  {css_link}
</head>
"""

    @staticmethod
    def render_header(metadata):
        return """
<header>
  <a href="/">Home</a>
  <a href="/static/resume/prakash_s_resume.pdf">Resume</a>
  <a href="/essays/">Essays</a>
  <a href="/projects.html">Projects</a>
  <a href="/bookshelf.html">Bookshelf</a>
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

    @staticmethod
    def render_footer(metadata):
        year = datetime.now().year
        return f"""
<footer>
  <p>&copy; {year} {_escape_html(metadata["author"])}. &middot; <a href="/sitelinks.html">Site Links</a></p>
</footer>
"""

    @staticmethod
    def apply(template, data):
        result = template
        for key, value in data.items():
            if value is not None:
                result = result.replace("{{" + key + "}}", str(value))
        return result


class FeedGenerator:
    @staticmethod
    def generate_sitemap(metadata, essays, projects, leetcode_solutions):
        site_url = metadata["siteUrl"].rstrip("/")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        tag_set = set()
        for e in essays:
            for t in e["tags"]:
                tag_set.add(t)

        tag_entries = [
            {"loc": f"/tags/{t}.html", "lastmod": today, "priority": "0.6"}
            for t in sorted(tag_set)
        ]

        pages = [
            {"loc": "/", "lastmod": today, "priority": "1.0"},
            {"loc": "/essays/", "lastmod": today, "priority": "0.9"},
            {"loc": "/about.html", "lastmod": today, "priority": "0.9"},
            {"loc": "/tags/", "lastmod": today, "priority": "0.8"},
            {"loc": "/projects.html", "lastmod": today, "priority": "0.8"},
            {"loc": "/bookshelf.html", "lastmod": today, "priority": "0.8"},
            {"loc": "/sitelinks.html", "lastmod": today, "priority": "0.6"},
            {"loc": "/leetcode-solutions/", "lastmod": today, "priority": "0.6"},
            {
                "loc": "/static/resume/prakash_s_resume.pdf",
                "lastmod": today,
                "priority": "0.7",
            },
        ]

        essay_entries = [
            {
                "loc": f"/essays/{e['slug']}.html",
                "lastmod": _format_date_iso(e["date"]),
                "priority": "0.7",
            }
            for e in essays
        ]

        site_hostname = site_url.split("://")[1].split("/")[0]
        project_entries = []
        for p in projects:
            website = p.get("website")
            if not website:
                continue
            try:
                hostname = (
                    website.split("://")[1].split("/")[0]
                    if "://" in website
                    else website.split("/")[0]
                )
            except Exception:
                continue
            if hostname == site_hostname:
                loc = website.replace("http://", "https://")
                project_entries.append(
                    {"loc": loc, "lastmod": today, "priority": "0.6"}
                )

        leetcode_entries = [
            {"loc": s["href"], "lastmod": today, "priority": "0.5"}
            for s in leetcode_solutions
        ]

        urls_data = (
            pages + essay_entries + tag_entries + project_entries + leetcode_entries
        )
        url_lines = []
        for p in urls_data:
            if p["loc"].startswith("http"):
                loc = p["loc"]
            else:
                loc = (
                    site_url + ("/" if not p["loc"].startswith("/") else "") + p["loc"]
                )
            url_lines.append(
                f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{p['lastmod']}</lastmod>\n    <priority>{p['priority']}</priority>\n  </url>"
            )

        urls_xml = "\n".join(url_lines)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}
</urlset>"""

    @staticmethod
    def generate_rss_feed(metadata, essays):
        site_url = metadata["siteUrl"].rstrip("/")
        sorted_essays = sorted(essays, key=lambda x: x["date"], reverse=True)

        items = []
        for e in sorted_essays:
            d = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
            pub_date = d.strftime("%a, %d %b %Y %H:%M:%S GMT")
            items.append(f"""  <item>
    <guid>{site_url}/essays/{e["slug"]}.html</guid>
    <title><![CDATA[{e["title"]}]]></title>
    <link>{site_url}/essays/{e["slug"]}.html</link>
    <description><![CDATA[{e.get("summary", "")}]]></description>
    <pubDate>{pub_date}</pubDate>
  </item>""")

        items_xml = "\n".join(items)

        first_date = sorted_essays[0]["date"] if sorted_essays else ""
        last_build = ""
        if first_date:
            d = datetime.fromisoformat(first_date.replace("Z", "+00:00"))
            last_build = d.strftime("%a, %d %b %Y %H:%M:%S GMT")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title><![CDATA[{metadata["title"]}]]></title>
    <link>{site_url}</link>
    <description><![CDATA[{metadata["description"]}]]></description>
    <language>{metadata.get("language", "en-us")}</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <atom:link href="{site_url}/feed.xml" rel="self" type="application/rss+xml"/>
{items_xml}
  </channel>
</rss>"""


class PageBuilder:
    def __init__(self, data_loader, markdown_renderer):
        self.data_loader = data_loader
        self.markdown_renderer = markdown_renderer

    def build_common(
        self,
        template,
        metadata,
        page_title,
        page_description,
        url="",
        image="",
        extra_schemas=None,
    ):
        return TemplateRenderer.apply(
            template,
            {
                "head": TemplateRenderer.render_head(
                    metadata,
                    {
                        "title": page_title,
                        "description": page_description,
                        "url": url,
                        "image": image,
                    },
                    extra_schemas=extra_schemas,
                ),
                "header": TemplateRenderer.render_header(metadata),
                "footer": TemplateRenderer.render_footer(metadata),
            },
        )

    def build_home(self, metadata, essays, books, projects, author, avatar, precept):
        template = self.data_loader.load_template("home")
        html = self.build_common(
            template, metadata, metadata["title"], metadata["description"], "/"
        )

        recent_essays_html = (
            "\n".join(
                f"""    <article>
      <h2><a href="/essays/{e["slug"]}.html">{_escape_html(e["title"])}</a></h2>
      <p class="meta"><time>{_format_date(e["date"])}</time></p>
      <p class="summary">{_escape_html(e["summary"])}</p>
      <div class="tags">
        {"".join(f'<a href="/tags/{t}.html">#{_escape_html(t)}</a>' for t in e["tags"][:3])}
      </div>
    </article>"""
                for e in essays[:4]
            )
            + '\n    <p class="section-footer"><a href="/essays/">All essays &rarr;</a></p>'
        )

        featured_projects_html = (
            '<div class="project-grid">'
            + "".join(
                f"""    <div class="project-card">
      <h3>{f'<a href="{_escape_html(p["website"])}">{_escape_html(p["title"])}</a>' if p.get("website") else _escape_html(p["title"])}</h3>
      <p class="summary">{_escape_html(p.get("description", ""))}</p>
      {('<div class="tags">' + "".join(f"<span>#{_escape_html(t)}</span>" for t in p.get("tags", [])) + "</div>") if p.get("tags") else ""}
    </div>"""
                for p in projects[:6]
            )
            + '\n    </div>\n    <p class="section-footer"><a href="/projects.html">All projects &rarr;</a></p>'
        )

        curated_books = books.get("curated", [])
        reading_list_html = "\n".join(
            f"""    <li>
      <a href="{_escape_html(b["link"])}" target="_blank" rel="noopener">{_escape_html(b["title"])}</a>
    </li>"""
            for b in curated_books[:5]
        )

        first_para = author["body"].split("\n\n")[0] if author["body"] else ""

        precept_html = "\n".join(
            f"""    <li>
      <a href="{_escape_html(p["link"])}" target="_blank" rel="noopener">{_escape_html(p["title"])}</a>
    </li>"""
            for p in (precept[:4] or [])
        )

        html = TemplateRenderer.apply(
            html,
            {
                "recentEssays": recent_essays_html,
                "featuredProjects": featured_projects_html,
                "authorPreview": _escape_html(first_para),
                "readingList": reading_list_html,
                "preceptList": precept_html,
                "metadata.author": _escape_html(metadata["author"]),
                "avatar": avatar,
            },
        )

        FileSystem.write(os.path.join(os.getcwd(), "out", "index.html"), html)

    def build_essays_list(self, metadata, essays):
        template = self.data_loader.load_template("essays-list")
        html = self.build_common(
            template,
            metadata,
            metadata["title"],
            f"Essays by {metadata['author']}",
            "/essays/",
        )

        essays_list_html = "\n".join(
            f"""<article>
  <h2><a href="/essays/{e["slug"]}.html">{_escape_html(e["title"])}</a></h2>
  <p class="meta"><time>{_format_date(e["date"])}</time></p>
  <p class="summary">{_escape_html(e["summary"])}</p>
  <div class="tags">
    {"".join(f'<a href="/tags/{t}.html">#{_escape_html(t)}</a>' for t in e["tags"][:3])}
  </div>
</article>"""
            for e in essays
        )

        html = TemplateRenderer.apply(html, {"essaysList": essays_list_html})

        FileSystem.ensure_dir(os.path.join(os.getcwd(), "out", "essays"))
        FileSystem.write(os.path.join(os.getcwd(), "out", "essays", "index.html"), html)

    def build_essay(self, metadata, essay):
        template = self.data_loader.load_template("essay")
        site_url = metadata["siteUrl"].rstrip("/")
        essay_url = f"/essays/{essay['slug']}.html"

        blog_posting = {
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

        html = self.build_common(
            template,
            metadata,
            f"{essay['title']} - {metadata['title']}",
            essay["summary"],
            essay_url,
            extra_schemas=[blog_posting],
        )

        essay_content = self.markdown_renderer.render(essay["content"])

        html = TemplateRenderer.apply(
            html,
            {
                "essay.title": _escape_html(essay["title"]),
                "essay.date": _format_date(essay["date"]),
                "essay.tags": " ".join(
                    f'<a href="/tags/{t}.html">#{_escape_html(t)}</a>'
                    for t in essay["tags"]
                ),
                "essay.content": essay_content,
            },
        )

        FileSystem.write(
            os.path.join(os.getcwd(), "out", "essays", f"{essay['slug']}.html"), html
        )

    def build_about(self, metadata, author, avatar):
        template = self.data_loader.load_template("about")
        site_url = metadata["siteUrl"].rstrip("/")
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

        about_page = {
            "@type": "ProfilePage",
            "name": f"About {metadata['author']}",
            "description": f"About {metadata['author']}",
            "url": site_url + "/about.html",
            "mainEntity": main_entity,
        }

        html = self.build_common(
            template,
            metadata,
            f"About - {metadata['title']}",
            f"About {metadata['author']}",
            "/about.html",
            extra_schemas=[about_page],
        )

        author_body = self.markdown_renderer.render(author["body"])

        html = TemplateRenderer.apply(
            html,
            {
                "metadata.author": _escape_html(metadata["author"]),
                "author.occupation": _escape_html(author.get("occupation", "")),
                "author.body": author_body,
                "avatar": avatar,
            },
        )

        FileSystem.write(os.path.join(os.getcwd(), "out", "about.html"), html)

    def build_projects(self, metadata, projects):
        template = self.data_loader.load_template("projects")
        site_url = metadata["siteUrl"].rstrip("/")

        software_items = []
        for i, p in enumerate(projects, 1):
            app_url = p.get("website") or p["href"]
            app = {
                "@type": "SoftwareApplication",
                "name": p["title"],
                "description": p.get("description", ""),
                "url": app_url,
                "codeRepository": p["href"],
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
                    "ratingValue": p.get("stars", 0),
                    "bestRating": max((r.get("stars", 0) for r in projects), default=0),
                    "worstRating": 0,
                    "ratingCount": 1,
                },
            }
            software_items.append(
                {
                    "@type": "ListItem",
                    "position": i,
                    "item": app,
                }
            )

        collection_schema = {
            "@type": "CollectionPage",
            "mainEntity": {
                "@type": "ItemList",
                "itemListElement": software_items,
            },
        }

        html = self.build_common(
            template,
            metadata,
            f"Projects - {metadata['title']}",
            f"Projects by {metadata['author']}",
            "/projects.html",
            extra_schemas=[collection_schema],
        )

        projects_list_html = (
            '<div class="project-grid">'
            + "".join(
                f"""    <div class="project-card">
      <h3>{f'<a href="{_escape_html(p["website"])}">{_escape_html(p["title"])}</a>' if p.get("website") else _escape_html(p["title"])}</h3>
      <p class="summary">{_escape_html(p.get("description", ""))}</p>
      {('<div class="tags">' + "".join(f"<span>#{_escape_html(t)}</span>" for t in p.get("tags", [])) + "</div>") if p.get("tags") else ""}
      <p class="meta"><a href="{_escape_html(p["href"])}">GitHub</a></p>
    </div>"""
                for p in projects
            )
            + "\n    </div>"
        )

        html = TemplateRenderer.apply(html, {"projectsList": projects_list_html})
        FileSystem.write(os.path.join(os.getcwd(), "out", "projects.html"), html)

    def build_bookshelf(self, metadata, books):
        template = self.data_loader.load_template("bookshelf")

        def _render_stars(rating):
            try:
                n = int(rating)
            except ValueError, TypeError:
                return ""
            if not n:
                return ""
            return "★" * n + "☆" * (5 - n)

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

        def _resolve_image(book):
            url = book.get("imageUrl", "")
            if not url or "nophoto" in url:
                return ""
            if url.startswith("/"):
                local = os.path.join(os.getcwd(), "data", "public", url.lstrip("/"))
                if not os.path.exists(local):
                    url = book.get("imageUrlRemote", "")
            return url if url and "nophoto" not in url else ""

        site_url = metadata["siteUrl"].rstrip("/")
        all_books = curated + currently_reading + read_books
        book_list_items = []
        for i, book in enumerate(all_books, 1):
            b_schema = {"@type": "Book", "name": book["title"]}
            b_schema["author"] = book.get("author", "")
            b_schema["url"] = book.get("link", "")
            img = _resolve_image(book)
            if img:
                b_schema["image"] = img
            try:
                rating = int(book.get("rating", 0))
            except ValueError, TypeError:
                rating = 0
            if rating > 0:
                b_schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": rating,
                    "ratingCount": 1,
                    "bestRating": 5,
                    "worstRating": 1,
                }
            book_list_items.append(
                {"@type": "ListItem", "position": i, "item": b_schema}
            )

        collection_schema = {
            "@type": "CollectionPage",
            "name": "Bookshelf",
            "description": "Books I've read",
            "url": site_url + "/bookshelf.html",
            "mainEntity": {
                "@type": "ItemList",
                "itemListElement": book_list_items,
            },
        }

        html = self.build_common(
            template,
            metadata,
            f"Bookshelf - {metadata['title']}",
            "Books I've read",
            "/bookshelf.html",
            extra_schemas=[collection_schema],
        )

        def _build_card(book, category):
            escaped_title = _escape_html(book.get("title", ""))
            escaped_author = _escape_html(book.get("author", ""))
            stars = _render_stars(book.get("rating"))
            href = _escape_html(book.get("link", "#"))
            img_url = _resolve_image(book)

            has_image = bool(img_url)
            is_current = category["dataKey"] == "currently-reading"

            style = f' style="background-image:url({_escape_html(img_url)})"' if has_image else ""
            placeholder = f'<div class="book-placeholder">{escaped_title}</div>' if not has_image else ""
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

        def _build_unified_bookcase(groups):
            shelves_el = []
            for group in groups:
                books_html = "".join(_build_card(b, group) for b in group["books"])
                shelves_el.append(f'''
    <section class="shelf-section">
      <div class="shelf-label {group["tagClass"]}">
        <span class="tag-dot"></span>{group["label"]}<span class="n">{len(group["books"])} book{"s" if len(group["books"]) != 1 else ""}</span>
      </div>
      <div class="compartment">
        <div class="shelf-boards">{books_html}</div>
      </div>
    </section>''')
            return f'''
    <div class="bookcase">
      {"".join(shelves_el)}
    </div>'''

        html = TemplateRenderer.apply(
            html,
            {
                "bookshelfSection": _build_unified_bookcase(groups),
            },
        )

        FileSystem.write(os.path.join(os.getcwd(), "out", "bookshelf.html"), html)

    def build_tags(self, metadata, essays):
        tag_map = {}
        for essay in essays:
            for tag in essay["tags"]:
                if tag not in tag_map:
                    tag_map[tag] = []
                tag_map[tag].append(essay)

        sorted_tags = sorted(tag_map.items(), key=lambda x: -len(x[1]))

        tags_index_template = self.data_loader.load_template("tags-index")
        tag_template = self.data_loader.load_template("tag")

        tags_index_html = self.build_common(
            tags_index_template,
            metadata,
            f"Tags - {metadata['title']}",
            "All tags",
            "/tags/",
        )
        tags_index_html = TemplateRenderer.apply(
            tags_index_html,
            {
                "tagsCount": str(len(sorted_tags)),
                "tagsList": "".join(
                    f'\n    <a href="/tags/{tag}.html" class="tag">#{_escape_html(tag)} <span class="count">{len(essays)}</span></a>'
                    for tag, essays in sorted_tags
                ),
            },
        )

        FileSystem.ensure_dir(os.path.join(os.getcwd(), "out", "tags"))
        FileSystem.write(
            os.path.join(os.getcwd(), "out", "tags", "index.html"), tags_index_html
        )

        for tag, tagged_essays in tag_map.items():
            tag_html = self.build_common(
                tag_template,
                metadata,
                f"#{tag} - {metadata['title']}",
                f"Essays tagged with {tag}",
                f"/tags/{tag}.html",
            )
            count_label = "essays" if len(tagged_essays) != 1 else "essay"
            tag_html = TemplateRenderer.apply(
                tag_html,
                {
                    "tag": _escape_html(tag),
                    "taggedEssaysCount": str(len(tagged_essays)),
                    "taggedEssaysCountLabel": count_label,
                    "taggedEssays": "\n".join(
                        f"""<article>
  <h2><a href="/essays/{e["slug"]}.html">{_escape_html(e["title"])}</a></h2>
  <p class="meta"><time>{_format_date(e["date"])}</time></p>
  <p class="summary">{_escape_html(e["summary"])}</p>
</article>"""
                        for e in tagged_essays
                    ),
                },
            )

            FileSystem.write(
                os.path.join(os.getcwd(), "out", "tags", f"{tag}.html"), tag_html
            )


    def build_sitelinks(self, metadata, essays, projects):
        template = self.data_loader.load_template("sitelinks")
        html = self.build_common(
            template,
            metadata,
            f"Site Links - {metadata['title']}",
            "All internal links on this site",
            "/sitelinks.html",
        )

        site_url = metadata["siteUrl"].rstrip("/")
        site_hostname = site_url.split("://")[1].split("/")[0]

        static_pages = [
            ("/", "Home"),
            ("/essays/", "Essays"),
            ("/about.html", "About"),
            ("/projects.html", "Projects"),
            ("/bookshelf.html", "Bookshelf"),
            ("/tags/", "Tags"),
            ("/static/resume/prakash_s_resume.pdf", "Resume"),
        ]

        static_pages_html = "\n".join(
            f'    <li><a href="{url}">{_escape_html(label)}</a></li>'
            for url, label in static_pages
        )

        essay_links_html = "\n".join(
            f'    <li><a href="/essays/{e["slug"]}.html">{_escape_html(e["title"])}</a> <span class="meta">{_format_date(e["date"])}</span></li>'
            for e in essays
        )

        tag_set = set()
        for e in essays:
            for t in e["tags"]:
                tag_set.add(t)
        tags_sorted = sorted(tag_set)
        tag_links_html = "\n".join(
            f'    <li><a href="/tags/{t}.html">#{_escape_html(t)}</a></li>'
            for t in tags_sorted
        )

        same_domain_projects = []
        for p in projects:
            website = p.get("website")
            if not website:
                continue
            try:
                hostname = (
                    website.split("://")[1].split("/")[0]
                    if "://" in website
                    else website.split("/")[0]
                )
            except Exception:
                continue
            if hostname == site_hostname:
                same_domain_projects.append(p)

        project_links_html = "\n".join(
            f'    <li><a href="{_escape_html(p["website"])}">{_escape_html(p["title"])}</a></li>'
            for p in same_domain_projects
        )

        html = TemplateRenderer.apply(
            html,
            {
                "staticPages": static_pages_html,
                "essayLinks": essay_links_html,
                "essayCount": str(len(essays)),
                "tagLinks": tag_links_html,
                "tagCount": str(len(tags_sorted)),
                "projectLinks": project_links_html,
                "projectCount": str(len(same_domain_projects)),
            },
        )

        FileSystem.write(os.path.join(os.getcwd(), "out", "sitelinks.html"), html)


class SiteBuilder:
    def __init__(self):
        data_dir = os.path.join(os.getcwd(), "data", "non-public")
        self.data_loader = DataLoader(data_dir)
        self.markdown_renderer = MarkdownRenderer()
        self.page_builder = PageBuilder(self.data_loader, self.markdown_renderer)
        self.out_dir = os.path.join(os.getcwd(), "out")
        self.public_dir = os.path.join(os.getcwd(), "data", "public")

    def build(self):
        print("Reading data...")
        metadata = self.data_loader.read_site_metadata()
        author = self.data_loader.read_author()
        essays = self.data_loader.get_essays()
        books = self.data_loader.get_books()
        precept = self.data_loader.get_precept()
        projects = self.data_loader.get_projects()
        leetcode_solutions = self.data_loader.get_leetcode_solutions()

        print(
            f"Found {len(essays)} essays, {len(projects)} projects, {len(leetcode_solutions)} leetcode solutions"
        )

        FileSystem.ensure_dir(self.out_dir)
        FileSystem.clear_dir(self.out_dir)
        FileSystem.copy_dir(self.public_dir, self.out_dir)

        print("Building pages...")
        avatar = f"{BASE_PATH}/static/images/avatar.jpg"
        self.page_builder.build_home(
            metadata, essays, books, projects, author, avatar, precept
        )
        self.page_builder.build_essays_list(metadata, essays)
        for essay in essays:
            self.page_builder.build_essay(metadata, essay)
        self.page_builder.build_tags(metadata, essays)
        self.page_builder.build_about(metadata, author, avatar)
        self.page_builder.build_projects(metadata, projects)
        self.page_builder.build_bookshelf(metadata, books)
        self.page_builder.build_sitelinks(metadata, essays, projects)

        print("Generating RSS, sitemap, and robots.txt...")
        FileSystem.write(
            os.path.join(self.out_dir, "feed.xml"),
            FeedGenerator.generate_rss_feed(metadata, essays),
        )
        FileSystem.write(
            os.path.join(self.out_dir, "sitemap.xml"),
            FeedGenerator.generate_sitemap(
                metadata, essays, projects, leetcode_solutions
            ),
        )
        FileSystem.write(
            os.path.join(self.out_dir, "robots.txt"),
            f"User-agent: *\nAllow: /\n\nSitemap: {metadata['siteUrl']}sitemap.xml",
        )

        print("Done! Static site generated in out/")


if __name__ == "__main__":
    SiteBuilder().build()
