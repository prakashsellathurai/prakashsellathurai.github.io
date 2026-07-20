import re
import yaml


def parse_frontmatter(content):
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n(?:---|\.\.\.)\r?\n?", content)
    if not match:
        return {"data": {}, "content": content}

    raw = match.group(1)
    body = content[match.end() :]
    data = yaml.safe_load(raw) or {}

    return {"data": data, "content": body}
