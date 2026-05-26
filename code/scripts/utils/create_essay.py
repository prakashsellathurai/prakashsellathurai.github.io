#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timezone

from lib.slug import slug

ROOT = os.getcwd()
ESSAYS_DIR = os.path.join(ROOT, "data", "non-public", "essays")

TEMPLATES = {
    "default": lambda: "",
    "opinion": lambda: """## Thesis
<!-- Your point of view in one sentence. -->

## Why It Matters
<!-- Stakes, consequences, or relevance. -->

## The Case
<!-- 2-4 key arguments with examples. -->

## Counterpoints
<!-- Address the strongest objections. -->

## Takeaway
<!-- What should the reader do or think next? -->
""",
    "howto": lambda: """## Goal
<!-- What the reader will achieve. -->

## Prerequisites
<!-- Tools, knowledge, or setup required. -->

## Steps
1.
2.
3.

## Gotchas
<!-- Common pitfalls and fixes. -->

## Next
<!-- Variations or deeper topics. -->
""",
    "review": lambda: """## Summary
<!-- What is this, in one paragraph? -->

## What Worked
<!-- Strengths and standout moments. -->

## What Didn't
<!-- Weaknesses or gaps. -->

## Who It's For
<!-- Ideal audience or use case. -->

## Verdict
<!-- Final rating or recommendation. -->
""",
    "research": lambda: """## Question
<!-- What are you trying to answer? -->

## Method
<!-- How you explored or tested it. -->

## Findings
<!-- Key results or observations. -->

## Implications
<!-- Why the findings matter. -->

## Open Questions
<!-- What remains unresolved. -->
""",
}


def usage():
    print("""Usage:
  python code/scripts/utils/create_essay.py --title "My New Essay" [options]

Options:
  --slug "custom-slug"       Optional custom slug (defaults to title)
  --template default         default | opinion | howto | review | research
  --tags "tag1,tag2"         Comma-separated tags
  --summary "Short summary"  Summary shown in lists
  --authors "default"        Comma-separated authors (default: "default")
  --layout "PostLayout"      Optional layout override
  --publish                  Sets draft to false (default is true)
  --ext "md"                 File extension (md or mdx)
""")


def parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if not arg.startswith("--"):
            i += 1
            continue
        key = arg[2:]
        next_val = argv[i + 1] if i + 1 < len(argv) else None
        if next_val and not next_val.startswith("--"):
            args[key] = next_val
            i += 2
        else:
            args[key] = True
            i += 1
    return args


def main():
    args = parse_args(sys.argv[1:])
    title = args.get("title")

    if not title:
        usage()
        sys.exit(1)

    os.makedirs(ESSAYS_DIR, exist_ok=True)

    template_key = (args.get("template") or "default").lower()
    template_fn = TEMPLATES.get(template_key)
    if not template_fn:
        print(f"Unknown template: {template_key}")
        print(f"Available: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    result_slug = args.get("slug") or slug(title)
    ext = (args.get("ext") or "md").lower()
    draft = not args.get("publish")

    tags_raw = args.get("tags", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    authors_raw = args.get("authors", "default")
    authors = [a.strip() for a in authors_raw.split(",") if a.strip()] if authors_raw else ["default"]

    summary = args.get("summary", "")
    layout = args.get("layout", "")

    date = datetime.now(timezone.utc).isoformat()

    frontmatter_lines = [
        "---",
        f"title: {json.dumps(title)}",
        f"date: '{date}'",
        f"draft: {'true' if draft else 'false'}",
        f"tags: {json.dumps(tags)}",
        f"summary: {json.dumps(summary)}",
        f"authors: {json.dumps(authors)}",
    ]
    if layout:
        frontmatter_lines.append(f"layout: {json.dumps(layout)}")
    frontmatter_lines.extend(["---", ""])

    frontmatter = "\n".join(frontmatter_lines)
    body = template_fn()

    filename = f"{result_slug}.{ext}"
    target_path = os.path.join(ESSAYS_DIR, filename)
    counter = 1
    while os.path.exists(target_path):
        filename = f"{result_slug}-{counter}.{ext}"
        target_path = os.path.join(ESSAYS_DIR, filename)
        counter += 1

    with open(target_path, "w") as f:
        f.write(f"{frontmatter}{body}")

    print(f"Created: {os.path.relpath(target_path, ROOT)}")


if __name__ == "__main__":
    main()
