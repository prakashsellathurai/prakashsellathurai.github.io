#!/usr/bin/env python3
"""Static site generator for prakashsellathurai.com."""

import logging
import os
import pathlib
import shutil

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
from lib.dataloader import DataLoader
from lib.dates import format_date, format_date_iso
from lib.markdown import MarkdownRenderer, escape_html
from lib.pagebuilder import PageBuilder
from lib.search import build_search_js
from lib.slug import slug
from lib.xmlgen import generate_rss_feed, generate_sitemap

_logger = logging.getLogger(__name__)

BASE_PATH = os.environ.get("BASE_PATH", "")
OUT_DIR = pathlib.Path("out")


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
    page_builder.build_home(metadata, essays, books, projects, author, avatar, precept, quotes, experiments, notes)
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

    _logger.info("Generating search index...")
    (OUT_DIR / "static" / "search-index.js").write_text(
        build_search_js(essays, notes, experiments, books, projects, quotes)
    )

    _logger.info("Generating RSS and sitemap...")
    (OUT_DIR / "feed.xml").write_text(
        generate_rss_feed(metadata, essays)
    )
    (OUT_DIR / "sitemap.xml").write_text(
        generate_sitemap(
            metadata, essays, projects, leetcode_solutions, notes, experiments
        )
    )

    _logger.info("Done! Static site generated in out/")


def main() -> None:
    """Entry point: configure logging and build the site."""
    _setup_logging()
    build_site()


if __name__ == "__main__":
    main()
