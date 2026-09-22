"""Core rendering helpers: template application, TOC, markdown/notebook rendering."""

from __future__ import annotations

import json
import logging
import pathlib
import re
from collections.abc import Callable

from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
import nbformat
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


def apply_template(template_str: str, data: dict[str, object]) -> str:
    """Replace ``{{key}}`` placeholders in a template string.

    Args:
        template_str: Template string containing ``{{key}}`` placeholders.
        data: Mapping of placeholder names to replacement values.
            Entries with a ``None`` value are skipped.

    Returns:
        The template with all placeholders replaced by their values.
    """
    result = template_str
    for key, value in data.items():
        if value is not None:
            result = result.replace("{{" + key + "}}", str(value))
    return result


def write_page(out_dir: pathlib.Path, rel_path: str, html: str) -> None:
    """Write rendered HTML to a file relative to *out_dir*.

    Creates any missing parent directories automatically.

    Args:
        out_dir: Root output directory.
        rel_path: Relative path inside *out_dir* where the file is written.
        html: HTML content to write.
    """
    target = out_dir / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


def heading_to_id(text: str, used: dict[str, bool]) -> str:
    """Generate a unique DOM id from a heading's text content.

    Appends ``-N`` suffixes when the base slug is already present in *used*.

    Args:
        text: Raw heading text.
        used: Mutable dict of ids already in use; updated in place.

    Returns:
        A unique, slugified id string.
    """
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
    """Inject ids into h2/h3 headings and build a Wikipedia-style TOC box.

    Modifies heading elements in *content_html* to add ``id`` attributes,
    then builds a collapsible table of contents from those headings.

    Args:
        content_html: Raw HTML content to process.

    Returns:
        A tuple of ``(modified_html, toc_html)`` where *modified_html* has
        heading ids injected and *toc_html* is the rendered TOC markup
        (empty string if no h2 headings exist).
    """
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
    """Render a collapsible panel section with a title and body.

    Args:
        title: Panel heading text (HTML-escaped).
        body: HTML content for the panel body.
        id_attr: Optional ``id`` attribute for the wrapper div.

    Returns:
        HTML string for the panel section.
    """
    id_str = f' id="{escape_html(id_attr)}"' if id_attr else ""
    return f"""<div class="portal"{id_str}>
      <h3>{escape_html(title)}</h3>
      <div class="body">{body}</div>
    </div>"""


def sidebar_tree_html(
    items: list[dict[str, object]],
    current: dict[str, object] | None,
    file_url_fn: Callable[[str, str | None, str], str],
    topic_title_key: str,
    topic_slug_key: str,
    current_section_key: str,
) -> str:
    """Build a collapsible topic tree suitable for the wiki left panel.

    Args:
        items: List of topic dicts, each containing files and subtopics.
        current: Dict describing the currently active topic/file/section,
            or ``None`` if nothing is active.
        file_url_fn: Callable that builds a URL from
            ``(topic_slug, subtopic_path, file_slug)``.
        topic_title_key: Key in *items* dicts for the display title.
        topic_slug_key: Key in *items* dicts for the slug.
        current_section_key: Key used to look up the current section in *current*.

    Returns:
        HTML string for the navigation tree.
    """
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
    """Extract a plain-text description from a note's markdown content.

    Strips markdown syntax and link targets, then truncates to *limit* characters.

    Args:
        file_data: File dict with a ``content`` key holding markdown text.
        limit: Maximum character length for the description.

    Returns:
        Truncated plain-text description ending with an ellipsis if needed.
    """
    text = _LINK_RE.sub(r"\1", file_data["content"])
    for token in ("#", "`", "*", "_", ">", "[", "]"):
        text = text.replace(token, " ")
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "\u2026"
    return text


def extract_body(full_html: str) -> str:
    """Extract the inner content of a ``<body>`` tag from a full HTML document.

    Args:
        full_html: Complete HTML document string.

    Returns:
        The inner HTML of the ``<body>`` tag, or the original string if no
        ``<body>`` tag is found.
    """
    match = re.search(r"<body[^>]*>(.*)</body>", full_html, re.S)
    return match.group(1).strip() if match else full_html


def _hljs_language(highlight_cls: str) -> str | None:
    """Map an nbconvert 'hl-*' pygments class to a highlight.js language."""
    for token in highlight_cls.split():
        if token.startswith("hl-"):
            return _HLJS_LANG_MAP.get(token[3:].lower())
    return None


def make_code_cells_collapsible(body_html: str) -> str:
    """Wrap each notebook code cell input in a collapsible ``<details>`` block.

    Also annotates ``<code>`` elements inside highlight divs with the
    appropriate ``language-*`` class for highlight.js.

    Args:
        body_html: HTML body content from an nbconvert export.

    Returns:
        Modified HTML with code cells wrapped in collapsible containers.
    """
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
    """Render a markdown file as HTML via nbconvert.

    Falls back to the *markdown_renderer* if nbconvert fails.

    Args:
        file_data: File dict with ``content`` (markdown text) and ``ext`` keys.
        markdown_renderer: Fallback renderer used when nbconvert errors.

    Returns:
        Rendered HTML string.
    """
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
    except (nbformat.ValidationError, ValueError, OSError) as exc:
        _logger.warning("nbconvert failed for markdown, falling back to renderer: %s", exc)
    return markdown_renderer.render(content)


_WIDGET_DEPS = """\
<script>
(function() {
  function addWidgetsRenderer() {
    var mimeElement = document.querySelector('script[type="application/vnd.jupyter.widget-view+json"]');
    if (!mimeElement) return;
    var scriptElement = document.createElement('script');
    var widgetRendererSrc = 'https://unpkg.com/@jupyter-widgets/html-manager@*/dist/embed.js';

    var widgetState;
    try {
      widgetState = mimeElement && JSON.parse(mimeElement.innerHTML);
      if (widgetState && (widgetState.version_major < 2 || !widgetState.version_major)) {
        widgetRendererSrc = 'https://unpkg.com/@jupyter-js-widgets@*/dist/embed.js';
      }
    } catch(e) {}

    scriptElement.src = widgetRendererSrc;
    document.body.appendChild(scriptElement);
  }

  document.addEventListener('DOMContentLoaded', addWidgetsRenderer);
}());
</script>"""


def _has_widgets(full_html: str) -> bool:
    return "application/vnd.jupyter.widget-view+json" in full_html


def _extract_widget_state(full_html: str) -> str:
    match = re.search(
        r'<script type="application/vnd\.jupyter\.widget-state\+json">\s*(\{.*?\})\s*</script>',
        full_html,
        re.S,
    )
    if not match:
        return ""
    return (
        '<script type="application/vnd.jupyter.widget-state+json">'
        + match.group(1)
        + "</script>"
    )


def _extract_plotly_figures(full_html: str) -> str:
    """Extract Plotly figure data from widget state and render as static elements."""
    state_match = re.search(
        r'<script type="application/vnd\.jupyter\.widget-state\+json">\s*(\{.*?\})\s*</script>',
        full_html,
        re.S,
    )
    if not state_match:
        return ""
    try:
        widget_state = json.loads(state_match.group(1))
    except (json.JSONDecodeError, KeyError):
        return ""

    models = widget_state.get("state", {})
    plotly_divs = []
    div_counter = [0]

    for model_id, model in models.items():
        model_state = model.get("state", {})
        outputs = model_state.get("outputs", [])
        for output in outputs:
            data = output.get("data", {})
            plotly_data = data.get("application/vnd.plotly.v1+json")
            if not plotly_data:
                continue
            div_id = f"plotly-widget-{div_counter[0]}"
            div_counter[0] += 1
            fig_data_json = json.dumps(plotly_data.get("data", []))
            fig_layout_json = json.dumps(plotly_data.get("layout", {}))
            plotly_divs.append(
                f'<div id="{div_id}" style="width:100%;height:620px"></div>'
                f"<script>"
                f"Plotly.newPlot('{div_id}', {fig_data_json}, {fig_layout_json}, "
                f"{{responsive: true, displayModeBar: false}});"
                f"</script>"
            )

    if not plotly_divs:
        return ""

    plotly_script = (
        '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>'
    )
    return plotly_script + "\n" + "\n".join(plotly_divs)


def render_notebook(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    """Render a Jupyter notebook (``.ipynb``) as HTML.

    Handles widget state extraction for Plotly figures and collapses code
    cell inputs. Falls back to a ``<pre><code>`` block on parse or export failure.

    Args:
        file_data: File dict with ``content`` (JSON notebook string) and ``ext`` keys.
        markdown_renderer: Unused; kept for call-signature compatibility.

    Returns:
        Rendered HTML string.
    """
    content = file_data["content"]
    try:
        nb = reads(content, NO_CONVERT)
    except (nbformat.ValidationError, ValueError) as exc:
        _logger.warning("Invalid notebook, rendering as code: %s", exc)
        return f"<pre><code>{escape_html(content)}</code></pre>"
    try:
        exporter = HTMLExporter(template_name="classic")
        full_html, _resources = exporter.from_notebook_node(nb)
        body = extract_body(full_html)
        if _has_widgets(full_html):
            widget_state_tag = _extract_widget_state(full_html)
            plotly_html = _extract_plotly_figures(full_html)
            injection = _WIDGET_DEPS + widget_state_tag + plotly_html
            body = body.replace("</main>", injection + "</main>", 1)
        return make_code_cells_collapsible(body)
    except (nbformat.ValidationError, ValueError, OSError) as exc:
        _logger.warning("Notebook export failed, rendering as code: %s", exc)
    return f"<pre><code>{escape_html(content)}</code></pre>"


def render_code_as_notebook(file_data: FileData, markdown_renderer: MarkdownRenderer) -> str:
    """Render a source-code file as a ``<pre><code>`` block.

    Args:
        file_data: File dict with ``content`` (source text) and ``ext`` keys.
        markdown_renderer: Unused; kept for call-signature compatibility.

    Returns:
        HTML string containing the escaped source code.
    """
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
    """Render an experiment file using the strategy matching its extension.

    Dispatches to ``render_markdown``, ``render_notebook``, or
    ``render_code_as_notebook`` based on the file extension.

    Args:
        file_data: File dict with ``content`` and ``ext`` keys.
        markdown_renderer: Renderer passed through to the chosen strategy.

    Returns:
        Rendered HTML string.
    """
    strategy = _RENDER_STRATEGIES.get(file_data["ext"], render_code_as_notebook)
    return strategy(file_data, markdown_renderer)
