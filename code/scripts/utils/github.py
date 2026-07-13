#!/usr/bin/env python3
import json
import os
import re
import subprocess
import urllib.request

GITHUB_API_URL = "https://api.github.com/users/prakashsellathurai/repos?per_page=100"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def get_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


GITHUB_TOKEN = get_github_token()


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Python", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8"), dict(resp.headers)


def fetch_all_repos(url):
    repos = []
    next_url = url
    while next_url:
        data, headers = fetch_url(next_url)
        page_data = json.loads(data)
        repos.extend(page_data)
        link_header = headers.get("Link", "")
        if link_header:
            links = {}
            for part in link_header.split(","):
                m = re.match(r"<([^>]+)>;\s*rel=\"([^\"]+)\"", part.strip())
                if m:
                    links[m.group(2)] = m.group(1)
            next_url = links.get("next")
        else:
            next_url = None
    return repos


def fetch_pinned_repos():
    if not GITHUB_TOKEN:
        print("No GITHUB_TOKEN env var, skipping pinned repos")
        return []

    query = """
    query {
      user(login: "prakashsellathurai") {
        pinnedItems(first: 6, types: REPOSITORY) {
          nodes {
            ... on Repository {
              name
              description
            }
          }
        }
      }
    }
    """
    body = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        GITHUB_GRAPHQL_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "User-Agent": "Python",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    pinned = result.get("data", {}).get("user", {}).get("pinnedItems", {}).get("nodes", [])
    return [{"name": r["name"], "description": r.get("description")} for r in pinned]


def fetch_repos():
    try:
        all_repos = fetch_all_repos(GITHUB_API_URL)
        pinned_repos = fetch_pinned_repos()

        all_repos.sort(key=lambda r: r.get("pushed_at", ""), reverse=True)
        pinned_names = {p["name"] for p in pinned_repos}

        repos_with_pinned = []
        for repo in all_repos:
            name = repo["name"]
            repos_with_pinned.append({
                "title": name,
                "href": repo["html_url"],
                "website": repo.get("homepage"),
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count", 0),
                "pinned": name in pinned_names,
            })

        pinned_first = [r for r in repos_with_pinned if r["pinned"]]
        rest = [r for r in repos_with_pinned if not r["pinned"]]
        final_data = pinned_first + rest

        with open("./data/non-public/repos.json", "w") as f:
            json.dump(final_data, f, indent=4)
        print(f"Updated repos.json with {len(final_data)} repos ({len(pinned_first)} pinned)")

    except Exception as e:
        print(f"Error fetching GitHub repositories: {e}")


def list_subtree(github_repo, path, ref="main"):
    url = f"https://api.github.com/repos/{github_repo}/git/trees/{ref}?recursive=1"
    data, _ = fetch_url(url)
    tree = json.loads(data).get("tree", [])
    files = [f["path"] for f in tree if f["type"] == "blob" and f["path"].startswith(path)]
    return files


def write_leetcode_solutions_as_json():
    files = list_subtree("prakashsellathurai/leetcode-solutions", "problems", "gh-pages")
    yamldata = [{"title": f, "href": f"leetcode-solutions/{f}"} for f in files]
    with open("./data/non-public/leetcode-solutions.json", "w") as f:
        json.dump(yamldata, f, indent=4)


PRECEPT_URL = "https://raw.githubusercontent.com/prakashsellathurai/grimoire/main/precept.txt"


def update_precept():
    try:
        data, _ = fetch_url(PRECEPT_URL)
        data = data.replace("\r\n", "\n")
        entries = []
        blocks = [b.strip() for b in data.split("\n\n") if b.strip()]
        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if len(lines) < 3:
                continue
            title = lines[0]
            author_line = lines[1]
            link = lines[2]

            if author_line.startswith("by "):
                author = author_line[3:]
                description = None
            elif " by " in author_line:
                parts = author_line.split(" by ", 1)
                description = parts[0].strip()
                author = parts[1].strip()
            else:
                author = author_line
                description = None

            entry = {
                "title": title,
                "author": author,
                "link": link,
            }
            if description:
                entry["description"] = description
            entries.append(entry)

        with open("./data/non-public/precept.json", "w") as f:
            json.dump(entries, f, indent=2)
        print(f"Updated precept.json with {len(entries)} entries")

    except Exception as e:
        print(f"Error updating precept: {e}")


if __name__ == "__main__":
    fetch_repos()
    write_leetcode_solutions_as_json()
    update_precept()
