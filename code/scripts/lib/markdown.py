import mistune
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


_PAT_FN_DEF = re.compile(r"^\[\^([\w-]+)\]:\s*(.*)")
_PAT_FN_REF = re.compile(r"\[\^([\w-]+)\]")

_PLACEHOLDER = "\x00FN:{}\x00"

_md = mistune.create_markdown(escape=False)
_md_gfm = mistune.create_markdown(
    escape=False,
    plugins=["table", "strikethrough", "task_lists", "url"],
)


class MarkdownRenderer:
    def __init__(self, gfm=False):
        self._md = _md_gfm if gfm else _md

    def render(self, content):
        defs, body = self._extract_footnotes(content)
        body = _PAT_FN_REF.sub(lambda m: _PLACEHOLDER.format(m.group(1)), body)
        html = self._md(body)
        for fn_id, fn_content in defs.items():
            rendered = _md(fn_content).strip()
            if rendered.startswith("<p>") and rendered.endswith("</p>"):
                rendered = rendered[3:-4]
            sidenote = (
                f'<a class="sidenote-number" href="#sn-{fn_id}">{fn_id}</a>'
                f'<span class="sidenote" id="sn-{fn_id}"> {rendered}</span>'
            )
            html = html.replace(_PLACEHOLDER.format(fn_id), sidenote)
        return html

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
