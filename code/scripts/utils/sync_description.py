#!/usr/bin/env python3
import json
import os
import re

ROOT = os.getcwd()
author_path = os.path.join(ROOT, "data", "non-public", "authors", "default.mdx")
site_metadata_path = os.path.join(ROOT, "data", "non-public", "siteMetadata.json")

with open(author_path) as f:
    content = f.read().replace("\r\n", "\n")

body = re.sub(r"---[\s\S]*?---", "", content).strip()
paragraphs = [p.strip() for p in re.split(r"\n\n+", body) if p.strip()]
first_paragraph = paragraphs[0] if paragraphs else ""

with open(site_metadata_path) as f:
    metadata = json.load(f)

metadata["description"] = first_paragraph

with open(site_metadata_path, "w") as f:
    json.dump(metadata, f, indent=2)
    f.write("\n")

print("siteMetadata.json description updated from default.mdx")
