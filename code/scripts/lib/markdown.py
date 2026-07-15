import re

_ESCAPE_TABLE = str.maketrans({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
})


def escape_html(text):
    if not text:
        return ""
    return str(text).translate(_ESCAPE_TABLE)


_PAT_CODE = re.compile(r"^`([^`]*)`")
_PAT_FN = re.compile(r"^\[\^([\w-]+)\]")
_PAT_LINK = re.compile(r"^\[([^\]]*)\]\(([^)]+)\)")
_PAT_LINK_TITLE = re.compile(r'^(\S+)\s+"([^"]*)"\s*$')
_PAT_AUTO_LINK = re.compile(r"^<([^>\s]+)>")
_PAT_BOLD = re.compile(r"^\*\*([^*]+)\*\*")
_PAT_ITALIC = re.compile(r"^\*([^*]+)\*")
_PAT_BARE_URL = re.compile(r"^https?://[^\s<>\]\)]+")
_PAT_TRAILING_PUNCT = re.compile(r"[.,;:!?]+$")
_PAT_FN_DEF = re.compile(r"^\[\^([\w-]+)\]:\s*(.*)")
_PAT_BQ_PREFIX = re.compile(r"^>\s?")


class MarkdownRenderer:
    def render(self, content):
        defs, body = self._extract_footnotes(content)
        return self._render_blocks(body, defs)

    def _extract_footnotes(self, text):
        defs = {}
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m = _PAT_FN_DEF.match(line)
            if m:
                fn_id = m.group(1)
                content = m.group(2)
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line == "" or next_line[0] in (" ", "\t"):
                        content += "\n\n" if next_line == "" else " " + next_line.strip()
                        i += 1
                    else:
                        break
                defs[fn_id] = content.strip()
            else:
                result.append(line)
                i += 1
        return defs, "\n".join(result)

    def _render_blocks(self, text, defs):
        lines = text.split("\n")
        blocks = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                i += 1
                continue

            m = re.match(r"^(#{1,6})\s+(.+)$", line)
            if m:
                level = len(m.group(1))
                blocks.append({"type": "heading", "level": level, "content": m.group(2)})
                i += 1
                continue

            m = re.match(r"^(`{3,})\s*(\w*)\s*$", line)
            if m:
                fence = m.group(1)
                lang = m.group(2)
                code_lines = []
                i += 1
                while i < len(lines):
                    if re.match(r"^`{3,}\s*$", lines[i]):
                        i += 1
                        break
                    code_lines.append(lines[i])
                    i += 1
                code_content = "\n".join(code_lines)
                blocks.append({"type": "code", "lang": lang, "content": code_content})
                continue

            if line.lstrip().startswith(">"):
                quote_lines = []
                while i < len(lines) and lines[i].lstrip().startswith(">"):
                    quote_lines.append(_PAT_BQ_PREFIX.sub("", lines[i]))
                    i += 1
                blocks.append({"type": "blockquote", "content": "\n".join(quote_lines)})
                continue
            para_lines = []
            while i < len(lines) and lines[i].strip() != "":
                para_lines.append(lines[i])
                i += 1
            blocks.append({"type": "paragraph", "content": " ".join(para_lines).strip()})
        return "\n".join(self._render_block(b, defs) for b in blocks)

    def _render_block(self, block, defs):
        t = block["type"]
        if t == "heading":
            level = block["level"]
            return f"<h{level}>{self._render_inline(block['content'], defs)}</h{level}>"
        if t == "code":
            lang = block.get("lang", "")
            code = escape_html(block["content"])
            if lang:
                return f'<pre><code class="language-{escape_html(lang)}">\n{code}\n</code></pre>'
            return f"<pre><code>\n{code}\n</code></pre>"
        if t == "blockquote":
            return f"<blockquote>\n{self._render_blocks(block['content'], defs)}\n</blockquote>"
        if t == "paragraph":
            return f"<p>{self._render_inline(block['content'], defs)}</p>"
        return ""

    def _render_inline(self, text, defs):
        result = []
        i = 0
        while i < len(text):
            suffix = text[i:]

            m = _PAT_CODE.match(suffix)
            if m:
                result.append(f"<code>{m.group(1)}</code>")
                i += len(m.group(0))
                continue

            m = _PAT_FN.match(suffix)
            if m:
                fn_id = m.group(1)
                if fn_id in defs:
                    rendered = self._render_inline(defs[fn_id], defs)
                    result.append(
                        f'<a class="sidenote-number" href="#sn-{fn_id}">{fn_id}</a>'
                        f'<span class="sidenote" id="sn-{fn_id}"> {rendered}</span>'
                    )
                else:
                    result.append(f"[^{fn_id}]")
                i += len(m.group(0))
                continue

            m = _PAT_LINK.match(suffix)
            if m:
                link_text = m.group(1)
                url_part = m.group(2)
                title_m = _PAT_LINK_TITLE.match(url_part)
                if title_m:
                    url = title_m.group(1)
                    title = title_m.group(2)
                else:
                    url = url_part
                    title = None
                title_attr = f' title="{escape_html(title)}"' if title else ""
                result.append(
                    f'<a href="{escape_html(url)}"{title_attr}>'
                    f"{self._render_inline(link_text, defs)}</a>"
                )
                i += len(m.group(0))
                continue

            m = _PAT_AUTO_LINK.match(suffix)
            if m:
                url = m.group(1)
                result.append(f'<a href="{escape_html(url)}">{escape_html(url)}</a>')
                i += len(m.group(0))
                continue

            m = _PAT_BOLD.match(suffix)
            if m:
                result.append(
                    f"<strong>{self._render_inline(m.group(1), defs)}</strong>"
                )
                i += len(m.group(0))
                continue

            m = _PAT_ITALIC.match(suffix)
            if m:
                result.append(f"<em>{self._render_inline(m.group(1), defs)}</em>")
                i += len(m.group(0))
                continue

            m = _PAT_BARE_URL.match(suffix)
            if m:
                url = _PAT_TRAILING_PUNCT.sub("", m.group(0))
                if url:
                    result.append(
                        f'<a href="{escape_html(url)}">{escape_html(url)}</a>'
                    )
                    i += len(m.group(0))
                    continue
                result.append(escape_html(text[i]))
                i += 1
                continue

            if text[i] == "\\" and i + 1 < len(text):
                result.append(text[i + 1])
                i += 2
                continue

            result.append(escape_html(text[i]))
            i += 1

        return "".join(result)
