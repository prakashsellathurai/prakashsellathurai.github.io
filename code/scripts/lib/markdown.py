import re

ESCAPE = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"}


def _escape_html(s):
    if not s:
        return ""
    return "".join(ESCAPE.get(c, c) for c in str(s))


def _escape_attr(s):
    if not s:
        return ""
    return "".join(ESCAPE.get(c, c) for c in str(s))


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
            m = re.match(r"^\[\^([\w-]+)\]:\s*(.*)", line)
            if m:
                fn_id = m.group(1)
                content = m.group(2)
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    if next_line == "" or re.match(r"^[ \t]", next_line):
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

            if line.lstrip().startswith(">"):
                quote_lines = []
                while i < len(lines) and lines[i].lstrip().startswith(">"):
                    quote_lines.append(re.sub(r"^>\s?", "", lines[i]))
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
        if t == "blockquote":
            return f"<blockquote>\n{self._render_blocks(block['content'], defs)}\n</blockquote>"
        elif t == "paragraph":
            return f"<p>{self._render_inline(block['content'], defs)}</p>"
        return ""

    def _render_inline(self, text, defs):
        result = ""
        i = 0

        while i < len(text):
            code_match = re.match(r"^`([^`]*)`", text[i:])
            if code_match:
                result += f"<code>{code_match.group(1)}</code>"
                i += len(code_match.group(0))
                continue

            fn_match = re.match(r"^\[\^([\w-]+)\]", text[i:])
            if fn_match:
                fn_id = fn_match.group(1)
                if fn_id in defs:
                    result += f'<a class="sidenote-number" href="#sn-{fn_id}">{fn_id}</a><span class="sidenote" id="sn-{fn_id}"> {self._render_inline(defs[fn_id], defs)}</span>'
                else:
                    result += f"[^{fn_id}]"
                i += len(fn_match.group(0))
                continue

            link_match = re.match(r"^\[([^\]]*)\]\(([^)]+)\)", text[i:])
            if link_match:
                link_text = link_match.group(1)
                url_part = link_match.group(2)
                title_match = re.match(r'^(\S+)\s+"([^"]*)"\s*$', url_part)
                if title_match:
                    url = title_match.group(1)
                    title = title_match.group(2)
                else:
                    url = url_part
                    title = None
                title_attr = f' title="{_escape_attr(title)}"' if title else ""
                result += f'<a href="{_escape_attr(url)}"{title_attr}>{self._render_inline(link_text, defs)}</a>'
                i += len(link_match.group(0))
                continue

            auto_match = re.match(r"^<([^>\s]+)>", text[i:])
            if auto_match:
                url = auto_match.group(1)
                result += f'<a href="{_escape_attr(url)}">{_escape_html(url)}</a>'
                i += len(auto_match.group(0))
                continue

            bold_match = re.match(r"^\*\*([^*]+)\*\*", text[i:])
            if bold_match:
                result += f"<strong>{self._render_inline(bold_match.group(1), defs)}</strong>"
                i += len(bold_match.group(0))
                continue

            italic_match = re.match(r"^\*([^*]+)\*", text[i:])
            if italic_match:
                result += f"<em>{self._render_inline(italic_match.group(1), defs)}</em>"
                i += len(italic_match.group(0))
                continue

            bare_match = re.match(r"^https?://[^\s<>\]\)]+", text[i:])
            if bare_match:
                url = bare_match.group(0)
                url = re.sub(r"[.,;:!?]+$", "", url)
                if url:
                    result += f'<a href="{_escape_attr(url)}">{_escape_html(url)}</a>'
                else:
                    result += _escape_html(text[i])
                    i += 1
                    continue
                i += len(bare_match.group(0))
                continue

            if text[i] == "\\" and i + 1 < len(text):
                result += text[i + 1]
                i += 2
                continue

            result += _escape_html(text[i])
            i += 1

        return result
