"""Data loading utilities for the static site generator.

Provides the :class:`DataLoader` class for reading essays, books, notes,
experiments, and other site data from the filesystem. Also exposes a
module-level :func:`read_site_metadata` helper.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
from collections.abc import Sequence

from lib.datatypes import (
    Essay,
    ExperimentTopic,
    FileData,
    NoteTopic,
    Project,
    Quote,
    SiteMetadata,
)
from lib.frontmatter import parse_frontmatter
from lib.slug import slug

_logger = logging.getLogger(__name__)

NOTES_DIR = pathlib.Path("data/non-public/submodules/Grimoire/notes")
EXPERIMENTS_DIR = pathlib.Path("data/non-public/submodules/Grimoire/experiments")
_ALLOWED_EXTS = {".txt", ".py", ".c", ".md", ".ipynb"}


def read_site_metadata(filepath: str | pathlib.Path) -> SiteMetadata:
    """Read site metadata from a JSON file, substituting ``BASE_PATH``.

    Replaces the ``__BASE_PATH__`` placeholder in the file content with the
    value of the ``BASE_PATH`` environment variable before parsing.

    Args:
        filepath: Path to the JSON metadata file.

    Returns:
        Parsed site metadata dictionary.
    """
    content = pathlib.Path(filepath).read_text()
    content = content.replace("__BASE_PATH__", os.environ.get("BASE_PATH", ""))
    return json.loads(content)


class DataLoader:
    """Loads raw site data (JSON, markdown, templates, submodule content).

    All paths are resolved relative to *data_dir*. The loader reads essays,
    books, projects, quotes, notes, experiments, and other site assets from
    that root directory.

    Args:
        data_dir: Root directory containing site data files.
    """

    def __init__(self, data_dir: str | pathlib.Path) -> None:
        self.data_dir = pathlib.Path(data_dir)

    def read_json(self, filepath: str | pathlib.Path) -> dict:
        """Read and parse a JSON file relative to the data directory.

        Args:
            filepath: Path relative to the data directory.

        Returns:
            Parsed JSON content.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return json.loads((self.data_dir / filepath).read_text())

    def read_md(self, filepath: str | pathlib.Path) -> dict:
        """Read a markdown file and split its frontmatter from the body.

        Args:
            filepath: Absolute path to the markdown file.

        Returns:
            Dictionary with ``data`` (frontmatter dict) and ``content`` (body).
        """
        return parse_frontmatter(pathlib.Path(filepath).read_text())

    def load_template(self, template_name: str) -> str:
        """Load an HTML template by name.

        Args:
            template_name: Template filename without extension.

        Returns:
            Template content as a string.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        template_path = self.data_dir / "templates" / f"{template_name}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text()

    def load_partial(self, name: str) -> str:
        """Load an HTML partial from ``templates/partials/``.

        Args:
            name: Partial filename without extension.

        Returns:
            Partial content as a string.

        Raises:
            FileNotFoundError: If the partial file does not exist.
        """
        partial_path = self.data_dir / "templates" / "partials" / f"{name}.html"
        if not partial_path.exists():
            raise FileNotFoundError(f"Partial not found: {partial_path}")
        return partial_path.read_text()

    def read_author(self) -> dict:
        """Read the default author file and merge frontmatter with body.

        Returns:
            Dictionary containing author frontmatter fields and a ``body``
            key with the markdown body content.
        """
        content = (
            self.data_dir / "authors" / "default.mdx"
        ).read_text()
        parsed = parse_frontmatter(content)
        return {**parsed["data"], "body": parsed["content"]}

    def read_site_metadata(self) -> SiteMetadata:
        """Read site metadata from the data directory.

        Returns:
            Parsed site metadata.
        """
        return read_site_metadata(
            self.data_dir / "siteMetadata.json"
        )

    def get_essays(self) -> list[Essay]:
        """Read all published essays from the essays directory.

        Drafts are excluded. Results are sorted by date in descending order.

        Returns:
            List of essay dictionaries sorted newest-first.
        """
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

    def get_books(self) -> Sequence[dict]:
        """Read the books data file.

        Returns:
            List of book dictionaries.
        """
        return self.read_json("books.json")

    def get_precept(self) -> dict:
        """Read the precept data file.

        Returns:
            Parsed precept dictionary.
        """
        return self.read_json("precept.json")

    def get_projects(self) -> list[Project]:
        """Read the projects (repositories) data file.

        Returns:
            List of project dictionaries.
        """
        return self.read_json("repos.json")

    def get_leetcode_solutions(self) -> list[dict]:
        """Read the LeetCode solutions data file.

        Returns:
            List of solution dictionaries.
        """
        return self.read_json("leetcode-solutions.json")

    def get_quotes(self) -> list[Quote]:
        """Read the quotes data file.

        Returns:
            List of quote dictionaries.
        """
        return self.read_json("quotes.json")

    def get_notes(self) -> list[NoteTopic]:
        """Read all notes from the Grimoire submodule.

        Walks the notes directory and collects markdown files grouped by
        topic. Nested directories become subtopics. Hidden and cache
        directories are skipped.

        Returns:
            List of note topic dictionaries, each containing ``topic``,
            ``topic_slug``, ``topic_title``, ``files``, and ``subtopics``.
        """
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
                st_list = [
                    {
                        "subtopic_path": st_path,
                        "subtopic_title": st_path.replace("-", " ").replace("_", " ").title(),
                        "files": topic_data["subtopics"][st_path],
                    }
                    for st_path in sorted(topic_data["subtopics"])
                ]
                topic_data["subtopics"] = st_list
                notes.append(topic_data)
        return notes

    def get_experiments(self) -> list[ExperimentTopic]:
        """Read all experiments from the Grimoire submodule.

        Walks the experiments directory and collects files with allowed
        extensions (``.txt``, ``.py``, ``.c``, ``.md``, ``.ipynb``) grouped
        by topic. Nested directories become subtopics. Hidden and cache
        directories are skipped.

        Returns:
            List of experiment topic dictionaries, each containing ``topic``,
            ``topic_slug``, ``topic_title``, ``files``, and ``subtopics``.
        """
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
                st_list = [
                    {
                        "subtopic_path": st_path,
                        "subtopic_title": st_path.replace("-", " ").replace("_", " ").title(),
                        "files": topic_data["subtopics"][st_path],
                    }
                    for st_path in sorted(topic_data["subtopics"])
                ]
                topic_data["subtopics"] = st_list
                experiments.append(topic_data)
        return experiments
