"""Schema.org structured data (JSON-LD) builders."""

from __future__ import annotations

from collections.abc import Callable

from lib.dates import format_date_iso
from lib.datatypes import Book, Essay, Project, SiteMetadata


_PAGE_NAMES = {
    "/essays/": "Essays",
    "/about.html": "About",
    "/projects.html": "Projects",
    "/bookshelf.html": "Bookshelf",
    "/notes/": "Notes",
    "/tags/": "Tags",
    "/experiments/": "Experiments",
}


def build_author_schema(metadata: SiteMetadata) -> dict:
    """Build a minimal Person schema from site metadata for JSON-LD author fields.

    Args:
        metadata: Site-wide metadata containing author details.

    Returns:
        A dict with @type Person and available author attributes.
    """
    details = metadata.get("authorDetails", {})
    author = {"@type": "Person", "name": metadata["author"]}
    for key in ("url", "sameAs", "email", "jobTitle", "image"):
        if key in details:
            author[key] = details[key]
    return author


def website_schema(site_url: str, site_title: str) -> dict:
    """Build the WebSite structured-data entry for a page's JSON-LD graph.

    Args:
        site_url: Base URL of the site (no trailing slash).
        site_title: Human-readable site name.

    Returns:
        A dict representing a Schema.org WebSite node.
    """
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


def person_schema(metadata: SiteMetadata, site_url: str) -> dict:
    """Build the Person structured-data entry for a page's JSON-LD graph.

    Args:
        metadata: Site-wide metadata containing author details.
        site_url: Base URL of the site.

    Returns:
        A dict representing a Schema.org Person node with rich attributes.
    """
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


def blog_posting_schema(metadata: SiteMetadata, essay: Essay, site_url: str, essay_url: str) -> dict:
    """Build the BlogPosting structured-data entry for an essay page.

    Args:
        metadata: Site-wide metadata containing author details.
        essay: Essay data with title, date, and summary.
        site_url: Base URL of the site.
        essay_url: Relative path to the essay page.

    Returns:
        A dict representing a Schema.org BlogPosting node.
    """
    return {
        "@type": "BlogPosting",
        "headline": essay["title"],
        "description": essay.get("summary", ""),
        "datePublished": format_date_iso(essay["date"]),
        "dateModified": format_date_iso(essay["date"]),
        "author": build_author_schema(metadata),
        "url": site_url + essay_url,
        "image": site_url
        + (metadata.get("socialBanner") or metadata.get("siteLogo", "")),
        "mainEntityOfPage": {"@type": "WebPage", "@id": site_url + essay_url},
    }


def main_entity_schema(metadata: SiteMetadata, site_url: str) -> dict:
    """Build the Person entity used as mainEntity in the About page schema.

    Args:
        metadata: Site-wide metadata containing author details.
        site_url: Base URL of the site.

    Returns:
        A dict representing a Schema.org Person node for the About page.
    """
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


def collection_schema(
    item_list: list[dict],
    name: str | None = None,
    description: str | None = None,
    url: str | None = None,
) -> dict:
    """Build a CollectionPage schema with the given ItemList.

    Args:
        item_list: List of ListItem dicts to include in the collection.
        name: Optional page title.
        description: Optional page description.
        url: Optional canonical URL for the collection page.

    Returns:
        A dict representing a Schema.org CollectionPage node.
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


def software_application_item(metadata: SiteMetadata, project: Project, position: int, best_rating: int) -> dict:
    """Build a ListItem schema wrapping a SoftwareApplication for a project.

    Args:
        metadata: Site-wide metadata containing author details.
        project: Project data with title, href, stars, and description.
        position: Position in the ItemList (1-based).
        best_rating: Maximum rating value for the aggregate score.

    Returns:
        A dict representing a Schema.org ListItem containing a SoftwareApplication.
    """
    app_url = project.get("website") or project["href"]
    app = {
        "@type": "SoftwareApplication",
        "name": project["title"],
        "description": project.get("description", ""),
        "url": app_url,
        "codeRepository": project["href"],
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Any",
        "author": build_author_schema(metadata),
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


def book_item(book: Book, position: int, resolve_image: Callable[[Book], str]) -> dict:
    """Build a ListItem schema wrapping a Book for the bookshelf.

    Args:
        book: Book data with title, author, link, and optional rating.
        position: Position in the ItemList (1-based).
        resolve_image: Callback that returns the image URL for a book.

    Returns:
        A dict representing a Schema.org ListItem containing a Book node.
    """
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


def breadcrumbs_for_url(url: str, site_url: str) -> dict | None:
    """Build a BreadcrumbList schema for a given page URL.

    Args:
        url: Relative path of the page (e.g. "/essays/some-post.html").
        site_url: Base URL of the site.

    Returns:
        A dict representing a Schema.org BreadcrumbList, or None for the
        homepage or unrecognized root paths.
    """
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
