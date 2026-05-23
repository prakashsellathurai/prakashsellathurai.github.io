import re


def parse_frontmatter(content):
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n(?:---|\.\.\.)\r?\n?", content)
    if not match:
        return {"data": {}, "content": content}

    yaml = match.group(1)
    body = content[match.end() :]
    data = {}

    for line in yaml.split("\n"):
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        colon_idx = trimmed.find(":")
        if colon_idx == -1:
            continue

        key = trimmed[:colon_idx].strip()
        raw = trimmed[colon_idx + 1 :].strip()

        if not key:
            continue

        if (raw.startswith("'") and raw.endswith("'")) or (
            raw.startswith('"') and raw.endswith('"')
        ):
            data[key] = raw[1:-1]
        elif raw.startswith("[") and raw.endswith("]"):
            try:
                data[key] = __import__("json").loads(raw.replace("'", '"'))
            except Exception:
                data[key] = []
        elif raw.lower() == "true":
            data[key] = True
        elif raw.lower() == "false":
            data[key] = False
        elif re.match(r"^\d+(\.\d+)?$", raw):
            data[key] = float(raw) if "." in raw else int(raw)
        else:
            data[key] = raw

    return {"data": data, "content": body}
