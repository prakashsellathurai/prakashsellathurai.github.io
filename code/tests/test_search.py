import json
import sys

sys.path.insert(0, "code/scripts")

from lib.search import SearchIndexBuilder, build_search_js, tokenize


def _load(js: str) -> dict:
    return json.loads(js.split("=", 1)[1].rstrip(";\n"))


def _find(payload: dict, term: str) -> int:
    node = 0
    i = 0
    while i < len(term):
        seg = payload["c"][node]
        j = 0
        while j < len(seg) and i < len(term) and seg[j] == term[i]:
            j += 1
            i += 1
        if i == len(term):
            return node
        if j < len(seg):
            return -1
        found = -1
        for m in payload["k"][node]:
            if payload["c"][m][0] == term[i]:
                found = m
                break
        if found == -1:
            return -1
        node = found
    return node


def _collect(payload: dict, node: int) -> set[int]:
    docs: set[int] = set()
    if node < 0:
        return docs
    stack = [node]
    while stack:
        n = stack.pop()
        for packed in payload["w"][n]:
            docs.add(packed >> 4)
        stack.extend(payload["k"][n])
    return docs


def _match(payload: dict, query: str) -> set[int]:
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return set()
    result = _collect(payload, _find(payload, terms[0]))
    for term in terms[1:]:
        result &= _collect(payload, _find(payload, term))
    return result


class TestTokenizer:
    def test_case_and_punctuation(self):
        assert tokenize("Hello, WORLD! foo.bar") == ["hello", "world", "foo", "bar"]

    def test_stopwords_and_short_tokens(self):
        assert tokenize("a the of on go it") == []

    def test_digits(self):
        assert tokenize("python3 c++ 123") == ["python3", "123"]


class TestSearchIndexBuilder:
    def _builder(self):
        b = SearchIndexBuilder()
        b.add(
            "Agentic Systems",
            "/essays/agentic-systems.html",
            0,
            tags="ai agents",
            body="deep learning language models reasoning",
        )
        b.add(
            "CPython Internals",
            "/notes/cpython/internals.html",
            1,
            tags="python",
            body="garbage collector memory management reference counting",
        )
        b.add(
            "Deep Learning",
            "/experiments/deep-learning.html",
            2,
            body="neural networks backpropagation training",
        )
        return b

    def test_serialization_roundtrip_shape(self):
        payload = _load(self._builder().to_js())
        assert payload["d"][0][0] == "Agentic Systems"
        assert payload["d"][0][1] == "/essays/agentic-systems.html"
        assert payload["d"][0][2] == 0
        assert len(payload["c"]) == len(payload["k"]) == len(payload["w"])

    def test_prefix_matches_title_and_body(self):
        payload = _load(self._builder().to_js())
        assert _match(payload, "agent") == {0}
        assert _match(payload, "cpython") == {1}
        assert _match(payload, "garbage") == {1}
        assert _match(payload, "backprop") == {2}

    def test_multi_term_intersection(self):
        payload = _load(self._builder().to_js())
        assert _match(payload, "deep learning") == {0, 2}
        assert _match(payload, "garbage backprop") == set()

    def test_no_match(self):
        payload = _load(self._builder().to_js())
        assert _match(payload, "zzzzz") == set()

    def test_title_and_tag_weighting(self):
        b = self._builder()
        payload = _load(b.to_js())
        node = _find(payload, "python")
        assert any(packed >> 4 == 1 for packed in payload["w"][node])

    def test_compression_merges_single_child_chains(self):
        b = SearchIndexBuilder()
        b.add("foobar", "/foobar.html", 0)
        payload = _load(b.to_js())
        assert len(payload["c"]) == 1
        assert payload["c"][0] == "foobar"

    def test_word_boundary_not_merged(self):
        b = SearchIndexBuilder()
        b.add("foo", "/foo.html", 0)
        b.add("foobar", "/foobar.html", 0)
        payload = _load(b.to_js())
        assert payload["c"][0] == "foo"
        assert _match(payload, "foo") == {0, 1}
        assert _match(payload, "foob") == {1}


def test_build_search_js_accepts_site_data():
    essays = [{"slug": "a", "title": "Essay A", "tags": ["x"], "content": "body text"}]
    notes = [
        {
            "topic_slug": "n",
            "topic_title": "Note Topic",
            "files": [{"slug": "f", "title": "Note File", "content": "note body"}],
            "subtopics": [],
        }
    ]
    experiments = [
        {
            "topic_slug": "e",
            "topic_title": "Exp Topic",
            "files": [{"slug": "g", "title": "Exp File", "content": "exp body"}],
            "subtopics": [],
        }
    ]
    books = {"read": [{"title": "Book One", "author": "Author"}], "curated": []}
    projects = [{"title": "Project", "website": "/projects.html", "tags": ["py"], "description": "desc"}]
    quotes = [{"quote": "A quote here", "author": "Author", "book": "", "tags": []}]

    js = build_search_js(essays, notes, experiments, books, projects, quotes)
    payload = _load(js)
    titles = [d[0] for d in payload["d"]]
    assert "Essay A" in titles
    assert "Note Topic" in titles
    assert "Exp Topic" in titles
    assert "Book One" in titles
    assert "Project" in titles
    assert "LeetCode Solutions" in titles
    assert _match(payload, "essay") == {titles.index("Essay A")}