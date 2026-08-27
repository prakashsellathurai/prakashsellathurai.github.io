"""Core rendering helpers: template application, TOC, markdown/notebook rendering."""

from __future__ import annotations

import json
import logging
import pathlib
import re
import subprocess

from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
from nbformat import v4 as nbf, reads, NO_CONVERT

from lib.datatypes import FileData
from lib.markdown import MarkdownRenderer, escape_html
from lib.slug import slug

_logger = logging.getLogger(__name__)

_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")

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


def apply_template(template_str: str, data: dict) -> str:
    result = template_str
    for key, value in data.items():
        if value is not None:
            result = result.replace("{{" + key + "}}", str(value))
    return result


def write_page(out_dir: pathlib.Path, rel_path: str, html: str) -> None:
    """Write rendered HTML to out_dir/rel_path, creating parents as needed."""
    target = out_dir / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


def heading_to_id(text: str, used: dict) -> str:
    base = slug(text)
    if not base:
        base = "section"
    candidate = base
    n = 2
    while candidate in used:
        candidate = f"{base}-{n}"
        n += 1
    used[candidate] = True
    return candidate


def build_toc(content_html: str) -> tuple[str, str]:
    """Inject ids into h2/h3 headings and build a Wikipedia-style TOC box."""
    soup = BeautifulSoup(content_html, "html.parser")
    headings = soup.find_all(["h2", "h3"])
    if not headings:
        return content_html, ""

    used: dict = {}
    entries = []  # (level, id, text)
    for h in headings:
        text = " ".join(h.get_text(" ", strip=True).split())
        hid = heading_to_id(text, used)
        h["id"] = hid
        entries.append((h.name, hid, text))

    h2s = [e for e in entries if e[0] == "h2"]
    if not h2s:
        return str(soup), ""

    # Build nested list: h3 children nest under preceding h2.
    toc_items = []
    current_h2: dict | None = None
    for level, hid, text in entries:
        if level == "h2":
            current_h2 = {"id": hid, "text": text, "children": []}
            toc_items.append(current_h2)
        elif level == "h3" and current_h2 is not None:
            current_h2["children"].append({"id": hid, "text": text})

    def li_html(item: dict, counter: list) -> str:
        counter[0] += 1
        num = f'<span class="tocnumber">{counter[0]}</span>'
        text = f'<span class="toctext">{escape_html(item["text"])}</span>'
        inner = f'<li><a href="#{item["id"]}">{num}{text}</a>'
        if item["children"]:
            child_lis = "\n".join(
                f'<li><a href="#{c["id"]}"><span class="tocnumber">{counter[0]}.{i}</span>'
                f'<span class="toctext">{escape_html(c["text"])}</span></a></li>'
                for i, c in enumerate(item["children"], 1)
            )
            inner += f"\n<ul>{child_lis}</ul>"
        return inner + "</li>"

    counter = [0]
    lis = "\n".join(li_html(item, counter) for item in toc_items)

    toc_html = f"""<div id="toc" role="navigation" aria-labelledby="toctitle">
  <input type="checkbox" id="toctogglecheckbox" class="toctoggle">
  <div class="toctitle" id="toctitle"><h2>Contents</h2>
    <label for="toctogglecheckbox" class="toc-toggle">[hide]</label>
  </div>
  <ul>
    {lis}
  </ul>
</div>"""

    return str(soup), toc_html


def panel_section(title: str, body: str, id_attr: str = "") -> str:
    id_str = f' id="{escape_html(id_attr)}"' if id_attr else ""
    return f"""<div class="portal"{id_str}>
      <h3>{escape_html(title)}</h3>
      <div class="body">{body}</div>
    </div>"""


def sidebar_tree_html(
    items: list[dict],
    current: dict | None,
    file_url_fn,
    topic_title_key: str,
    topic_slug_key: str,
    current_section_key: str,
) -> str:
    """Build a collapsible topic tree suitable for the wiki left panel."""
    current = current or {}

    parts_html = []
    for item in items:
        topic_slug = item[topic_slug_key]
        root = {"dirs": {}, "files": list(item["files"])}
        for st in item["subtopics"]:
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
                href = file_url_fn(topic_slug, cur_sub, f["slug"])
                active = (
                    current.get(topic_slug_key) == topic_slug
                    and current.get("subtopic_path") == cur_sub
                    and current.get("file_slug") == f["slug"]
                )
                cls = ' class="nav-tree-file active"' if active else ' class="nav-tree-file"'
                out.append(f'<a{cls} href="{href}">{escape_html(f["title"])}</a>')
            return "\n".join(out)

        def dirs_html(dirs, path_parts):
            out = []
            for name, sub in sorted(dirs.items()):
                child_path = "/".join(path_parts + [name])
                current_path = current.get("subtopic_path") or ""
                expanded = current.get(topic_slug_key) == topic_slug and (
                    current_path == child_path
                    or current_path.startswith(child_path + "/")
                )
                inner = files_html(sub, path_parts + [name]) + dirs_html(
                    sub["dirs"], path_parts + [name]
                )
                open_attr = " open" if expanded else ""
                out.append(
                    f'<details class="nav-tree-sub"{open_attr}><summary>{escape_html(name)}</summary>'
                    f'<div class="nav-tree-inner">{inner}</div></details>'
                )
            return "\n".join(out)

        topic_active = current.get(topic_slug_key) == topic_slug
        summary_cls = ' class="topic-active"' if topic_active else ""
        inner = files_html(root, []) + dirs_html(root["dirs"], [])
        open_attr = " open" if topic_active else ""
        parts_html.append(
            f'<details class="nav-tree-dir"{open_attr}><summary{summary_cls}>{escape_html(item[topic_title_key])}</summary>'
            f'<div class="nav-tree-inner">{inner}</div></details>'
        )

    return f'<nav class="nav-tree">\n    {"\n    ".join(parts_html)}\n  </nav>'


def note_description(file_data: FileData, limit: int = 160) -> str:
    text = _LINK_RE.sub(r"\1", file_data["content"])
    for token in ("#", "`", "*", "_", ">", "[", "]"):
        text = text.replace(token, " ")
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "\u2026"
    return text


def extract_body(full_html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", full_html, re.S)
    return match.group(1).strip() if match else full_html


def _hljs_language(highlight_cls: str) -> str | None:
    """Map an nbconvert 'hl-*' pygments class to a highlight.js language."""
    for token in highlight_cls.split():
        if token.startswith("hl-"):
            return _HLJS_LANG_MAP.get(token[3:].lower())
    return None


def make_code_cells_collapsible(body_html: str) -> str:
    """Wrap each notebook code cell input in a collapsible <details> block."""
    soup = BeautifulSoup(body_html, "html.parser")
    for cell in soup.select("div.code_cell"):
        inp = cell.find("div", class_="input", recursive=False)
        if inp is None:
            continue
        inner = inp.find("div", class_="inner_cell", recursive=False)
        if inner is None:
            continue
        details = soup.new_tag("details", attrs={"class": "notebook-cell"})
        summary = soup.new_tag("summary")
        expand = soup.new_tag("span", attrs={"class": "notebook-expand"})
        expand.string = "Expand Code"
        collapse = soup.new_tag("span", attrs={"class": "notebook-collapse"})
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


def render_markdown(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
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
        return extract_body(full_html)
    except Exception as exc:
        _logger.warning("nbconvert failed for markdown, falling back to renderer: %s", exc)
    return markdown_renderer.render(content)


def render_notebook(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    content = file_data["content"]
    try:
        nb = reads(content, NO_CONVERT)
    except Exception as exc:
        _logger.warning("Invalid notebook, rendering as code: %s", exc)
        return f"<pre><code>{escape_html(content)}</code></pre>"
    try:
        exporter = HTMLExporter(template_name="classic")
        full_html, _resources = exporter.from_notebook_node(nb)
        return make_code_cells_collapsible(extract_body(full_html))
    except Exception as exc:
        _logger.warning("Notebook export failed, rendering as code: %s", exc)
    return f"<pre><code>{escape_html(content)}</code></pre>"


def render_code_as_notebook(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    escaped = escape_html(file_data["content"])
    return f'<pre><code class="language-{file_data["ext"]}">{escaped}</code></pre>'


_RENDER_STRATEGIES = {
    "md": render_markdown,
    "ipynb": render_notebook,
    "py": render_code_as_notebook,
    "c": render_code_as_notebook,
    "txt": render_code_as_notebook,
}


def render_experiment_content(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    strategy = _RENDER_STRATEGIES.get(file_data["ext"], render_code_as_notebook)
    return strategy(file_data, markdown_renderer)
