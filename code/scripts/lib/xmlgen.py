import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlparse

from lib.datatypes import Essay, Project, LeetcodeSolution, Note, ExperimentTopic

_ATOM_URI = "http://www.w3.org/2005/Atom"
_SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _xml_str(root: ET.Element) -> str:
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def _add_url(urlset: ET.Element, loc: str, lastmod: str, priority: str) -> None:
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = loc
    ET.SubElement(url, "lastmod").text = lastmod
    ET.SubElement(url, "priority").text = priority


def generate_sitemap(
    metadata: dict,
    essays: list[Essay],
    projects: list[Project],
    leetcode_solutions: list[LeetcodeSolution],
    notes: list[Note],
    experiments: list[ExperimentTopic],
) -> str:
    site_url = metadata["siteUrl"].rstrip("/")
    today = _utc_today()

    tag_set: set[str] = set()
    for e in essays:
        tag_set.update(e["tags"])

    urlset = ET.Element("urlset", xmlns=_SITEMAP_NS)

    _add_url(urlset, f"{site_url}/", today, "1.0")
    _add_url(urlset, f"{site_url}/essays/", today, "0.9")
    _add_url(urlset, f"{site_url}/about.html", today, "0.9")
    _add_url(urlset, f"{site_url}/tags/", today, "0.8")
    _add_url(urlset, f"{site_url}/projects.html", today, "0.8")
    _add_url(urlset, f"{site_url}/bookshelf.html", today, "0.8")
    _add_url(urlset, f"{site_url}/notes/", today, "0.8")
    _add_url(urlset, f"{site_url}/experiments/", today, "0.7")
    _add_url(urlset, f"{site_url}/quotes.html", today, "0.7")
    _add_url(urlset, f"{site_url}/sitelinks.html", today, "0.6")
    _add_url(urlset, f"{site_url}/leetcode-solutions/", today, "0.6")
    _add_url(urlset, f"{site_url}/static/resume/prakash_s_resume.pdf", today, "0.7")

    for t in sorted(tag_set):
        _add_url(urlset, f"{site_url}/tags/{t}.html", today, "0.6")

    for e in essays:
        _add_url(
            urlset,
            f"{site_url}/essays/{e['slug']}.html",
            datetime.fromisoformat(e["date"].replace("Z", "+00:00")).isoformat(),
            "0.7",
        )

    site_hostname = urlparse(site_url).hostname
    for p in projects:
        website = p.get("website")
        if not website:
            continue
        hostname = urlparse(website).hostname
        if hostname == site_hostname:
            loc = website.replace("http://", "https://")
            _add_url(urlset, loc, today, "0.6")

    for s in leetcode_solutions:
        _add_url(urlset, s["href"], today, "0.5")

    for n in notes:
        _add_url(urlset, f"{site_url}/notes/{n['slug']}.html", today, "0.6")

    for exp in experiments:
        _add_url(
            urlset, f"{site_url}/experiments/{exp['topic_slug']}/", today, "0.6"
        )
        for f in exp["files"]:
            _add_url(
                urlset,
                f'{site_url}/experiments/{exp["topic_slug"]}/{f["slug"]}.html',
                today,
                "0.5",
            )
        for st in exp["subtopics"]:
            _add_url(
                urlset,
                f'{site_url}/experiments/{exp["topic_slug"]}/{st["subtopic_path"]}/',
                today,
                "0.6",
            )
            for f in st["files"]:
                _add_url(
                    urlset,
                    f'{site_url}/experiments/{exp["topic_slug"]}/{st["subtopic_path"]}/{f["slug"]}.html',
                    today,
                    "0.5",
                )

    return _xml_str(urlset)


def generate_rss_feed(metadata: dict, essays: list[Essay]) -> str:
    site_url = metadata["siteUrl"].rstrip("/")
    sorted_essays = sorted(essays, key=lambda x: x["date"], reverse=True)

    ET.register_namespace("atom", _ATOM_URI)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = metadata["title"]
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = metadata.get("description", "")
    ET.SubElement(channel, "language").text = metadata.get("language", "en-us")

    if sorted_essays:
        d = datetime.fromisoformat(sorted_essays[0]["date"].replace("Z", "+00:00"))
        ET.SubElement(channel, "lastBuildDate").text = d.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    atom_link = ET.SubElement(channel, f"{{{_ATOM_URI}}}link")
    atom_link.set("href", f"{site_url}/feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for e in sorted_essays:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "guid").text = f'{site_url}/essays/{e["slug"]}.html'
        ET.SubElement(item, "title").text = e["title"]
        ET.SubElement(item, "link").text = f'{site_url}/essays/{e["slug"]}.html'
        ET.SubElement(item, "description").text = e.get("summary", "")
        d = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        ET.SubElement(item, "pubDate").text = d.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    return _xml_str(rss)
