"""Search index: trie builder and compact serializer.

Builds a prefix trie over normalized tokens from site content, then
serializes it to a compact JavaScript file consumed by static/js/search.js.

Serialized format (three parallel arrays indexed by node):

    window.__SEARCH__ = {
      "d": [["Title", "/url", 0], ...],   // docs: title, url, type code
      "c": ["ab", "t", ...],              // children chars of each node
      "k": [[1, 2], [3], ...],            // child node indices (aligned with c)
      "w": [[], [[0, 3]], ...]            // [doc_id, weight] pairs at word ends
    }
"""

from __future__ import annotations

import json
import re
import string

_STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's
    her here here's hers herself him himself his how how's i i'd i'll i'm i've
    if in into is isn't it it's its itself let's me more most mustn't my myself
    no nor not of off on once only or other ought our ours ourselves out over
    own same shan't she she'd she'll she's should shouldn't so some such than
    that that's the their theirs them themselves then there there's these they
    they'd they'll they're they've this those through to too under until up
    very was wasn't we we'd we'll we're we've were weren't what what's when
    when's where where's which while who who's whom why why's with won't would
    wouldn't you you'd you'll you're you've your yours yourself yourselves
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_MAX_BODY_TOKENS = 40
_WEIGHT_BASE = 16  # pack [doc_id, weight] pairs into doc_id * base + weight

# Type codes kept as the ordering hint for client-side ranking (lower = higher).
TYPE_ESSAY = 0
TYPE_NOTE = 1
TYPE_EXPERIMENT = 2
TYPE_BOOK = 3
TYPE_PROJECT = 4
TYPE_QUOTE = 5
TYPE_LEETCODE = 6

_TYPE_LABELS = {
    TYPE_ESSAY: "Essay",
    TYPE_NOTE: "Note",
    TYPE_EXPERIMENT: "Experiment",
    TYPE_BOOK: "Book",
    TYPE_PROJECT: "Project",
    TYPE_QUOTE: "Quote",
    TYPE_LEETCODE: "LeetCode",
}


def tokenize(text: str) -> list[str]:
    """Lowercase, split into alphanumeric tokens, drop stopwords and short words."""
    tokens = []
    for tok in _TOKEN_RE.findall(text.lower()):
        if len(tok) >= 3 and tok not in _STOPWORDS:
            tokens.append(tok)
    return tokens


class TrieNode:
    __slots__ = ("children", "weights")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.weights: dict[int, int] = {}


class SearchIndexBuilder:
    """Collect documents, build a token trie, and serialize it compactly."""

    def __init__(self) -> None:
        self._docs: list[dict] = []
        self._root = TrieNode()

    def add(
        self,
        title: str,
        url: str,
        type_code: int,
        *,
        tags: str = "",
        body: str = "",
        title_weight: int = 3,
    ) -> None:
        doc_id = len(self._docs)
        self._docs.append({"title": title, "url": url, "type": type_code})
        self._add_tokens(doc_id, tokenize(title), title_weight)
        if tags:
            self._add_tokens(doc_id, tokenize(tags), 2)
        if body:
            body_tokens = tokenize(body)
            counts: dict[str, int] = {}
            for tok in body_tokens:
                counts[tok] = counts.get(tok, 0) + 1
            top = sorted(counts, key=lambda t: (-counts[t], t))[:_MAX_BODY_TOKENS]
            self._add_tokens(doc_id, top, 1)

    def _add_tokens(self, doc_id: int, tokens: list[str], weight: int) -> None:
        for tok in tokens:
            node = self._root
            for ch in tok:
                node = node.children.setdefault(ch, TrieNode())
            node.weights[doc_id] = node.weights.get(doc_id, 0) + weight

    def to_js(self) -> str:
        """Serialize the trie to a compact JS literal assigning window.__SEARCH__.

        Single-child chains without word boundaries are merged into multi-char
        segments (edge compression), which shrinks the node count substantially.
        """
        chars: list[str] = []
        kids: list[list[int]] = []
        weights: list[list[list[int]]] = []
        counter = [0]

        def compress(node: TrieNode, seg: str) -> int:
            while len(node.children) == 1 and not node.weights:
                ch, child = next(iter(node.children.items()))
                seg += ch
                node = child
            idx = counter[0]
            counter[0] += 1
            chars.append(seg)
            kids.append([])
            weights.append(
                [d * _WEIGHT_BASE + w for d, w in sorted(node.weights.items())]
            )
            for ch, child in node.children.items():
                kids[idx].append(compress(child, ch))
            return idx

        compress(self._root, "")

        docs = [
            [doc["title"], doc["url"], doc["type"]]
            for doc in self._docs
        ]
        payload = {"d": docs, "c": chars, "k": kids, "w": weights}
        return "window.__SEARCH__=" + json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        ) + ";\n"


def _build_index(
    essays: list[dict],
    notes: list[dict],
    experiments: list[dict],
    books: list[dict],
    projects: list[dict],
    quotes: list[dict],
) -> SearchIndexBuilder:
    """Populate a builder from the site's loaded data collections."""
    builder = SearchIndexBuilder()

    for e in essays:
        builder.add(
            e["title"],
            f"/essays/{e['slug']}.html",
            TYPE_ESSAY,
            tags=" ".join(e.get("tags", [])),
            body=e.get("content", ""),
        )

    for topic in notes:
        builder.add(
            topic["topic_title"],
            f"/notes/{topic['topic_slug']}/",
            TYPE_NOTE,
            body=_note_body(topic),
        )
        for f in topic["files"]:
            builder.add(
                f["title"],
                f"/notes/{topic['topic_slug']}/{f['slug']}.html",
                TYPE_NOTE,
                body=f.get("content", ""),
            )
        for st in topic["subtopics"]:
            for f in st["files"]:
                builder.add(
                    f["title"],
                    f"/notes/{topic['topic_slug']}/{st['subtopic_path']}/{f['slug']}.html",
                    TYPE_NOTE,
                    body=f.get("content", ""),
                )

    for exp in experiments:
        builder.add(
            exp["topic_title"],
            f"/experiments/{exp['topic_slug']}/",
            TYPE_EXPERIMENT,
            body=_note_body(exp),
        )
        for f in exp["files"]:
            builder.add(
                f["title"],
                f"/experiments/{exp['topic_slug']}/{f['slug']}.html",
                TYPE_EXPERIMENT,
                body=f.get("content", ""),
            )
        for st in exp["subtopics"]:
            for f in st["files"]:
                builder.add(
                    f["title"],
                    f"/experiments/{exp['topic_slug']}/{st['subtopic_path']}/{f['slug']}.html",
                    TYPE_EXPERIMENT,
                    body=f.get("content", ""),
                )

    all_books = []
    for group in books.values() if isinstance(books, dict) else [books]:
        all_books.extend(group or [])
    for b in all_books:
        builder.add(
            b["title"],
            "/bookshelf.html",
            TYPE_BOOK,
            body=b.get("author", ""),
            title_weight=2,
        )

    for p in projects:
        url = p.get("website") or p.get("href") or "/projects.html"
        builder.add(
            p["title"],
            url,
            TYPE_PROJECT,
            tags=" ".join(p.get("tags", [])),
            body=p.get("description", ""),
            title_weight=2,
        )

    for q in quotes:
        title = q["quote"].strip()
        if len(title) > 80:
            title = title[:80].rsplit(" ", 1)[0] + "\u2026"
        builder.add(
            title,
            q.get("url") or "/quotes.html",
            TYPE_QUOTE,
            tags=" ".join(q.get("tags", [])),
            body=(q.get("author", "") + " " + q.get("book", "")),
            title_weight=1,
        )

    builder.add(
        "LeetCode Solutions",
        "/leetcode-solutions/",
        TYPE_LEETCODE,
        body="problems solutions algorithms",
    )
    return builder


def _note_body(topic: dict) -> str:
    """Concatenate a topic's file contents for body indexing."""
    parts = [f.get("content", "") for f in topic["files"]]
    for st in topic["subtopics"]:
        parts.extend(f.get("content", "") for f in st["files"])
    return " ".join(parts)


def build_search_js(
    essays: list[dict],
    notes: list[dict],
    experiments: list[dict],
    books: list[dict],
    projects: list[dict],
    quotes: list[dict],
) -> str:
    """Build and serialize the full search index as a JavaScript string."""
    return _build_index(essays, notes, experiments, books, projects, quotes).to_js()