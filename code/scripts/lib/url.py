"""URL generation functions for site pages."""

from __future__ import annotations

from lib.datatypes import ExperimentTopic, NoteTopic


def essay_url(slug: str) -> str:
    """Return the URL path for an essay slug."""
    return f"/essays/{slug}.html"


def note_topic_url(topic_slug: str) -> str:
    """Return the URL path for a note topic index."""
    return f"/notes/{topic_slug}/"


def note_file_url(topic_slug: str, subtopic_path: str | None, file_slug: str) -> str:
    """Return the URL path for a file within a note topic.

    Args:
        topic_slug: Slug of the parent note topic.
        subtopic_path: Optional nested subtopic path segments.
        file_slug: Slug of the individual file.

    Returns:
        Full URL path to the note file.
    """
    base = f"/notes/{topic_slug}"
    if subtopic_path:
        base += "/" + subtopic_path
    return f"{base}/{file_slug}.html"


def tag_url(tag: str) -> str:
    """Return the URL path for a tag page."""
    return f"/tags/{tag}.html"


def topic_url(topic_slug: str) -> str:
    """Return the URL path for an experiment topic index."""
    return f"/experiments/{topic_slug}/"


def exp_file_url(topic_slug: str, subtopic_path: str | None, file_slug: str) -> str:
    """Return the URL path for a file within an experiment topic.

    Args:
        topic_slug: Slug of the parent experiment topic.
        subtopic_path: Optional nested subtopic path segments.
        file_slug: Slug of the individual file.

    Returns:
        Full URL path to the experiment file.
    """
    base = f"/experiments/{topic_slug}"
    if subtopic_path:
        base += "/" + subtopic_path
    return f"{base}/{file_slug}.html"


def flatten_experiment_pages(experiments: list[ExperimentTopic]) -> list[dict]:
    """Flatten all experiment topics into a list of page entries.

    Includes both top-level files and files nested under subtopics.

    Args:
        experiments: List of experiment topics with files and subtopics.

    Returns:
        List of dicts with ``url`` and ``title`` keys.
    """
    pages = []
    for exp in experiments:
        base = topic_url(exp["topic_slug"])
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


def flatten_note_pages(notes: list[NoteTopic]) -> list[dict]:
    """Flatten all note topics into a list of page entries.

    Includes both top-level files and files nested under subtopics.

    Args:
        notes: List of note topics with files and subtopics.

    Returns:
        List of dicts with ``url`` and ``title`` keys.
    """
    pages = []
    for n in notes:
        base = note_topic_url(n["topic_slug"])
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
