import pathlib
import subprocess

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "out"


@pytest.fixture(scope="session")
def out_dir():
    return OUT_DIR


@pytest.fixture(scope="session")
def build_site():
    result = subprocess.run(
        ["make", "build"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed:\n{result.stderr}"
    return True


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, build_site):
    return {**browser_context_args, "base_url": OUT_DIR.as_uri() + "/"}


@pytest.fixture(autouse=True)
def setup_page(page, build_site):
    page.set_default_timeout(10000)

    def _serve_static(route):
        url = route.request.url
        if url.startswith("file:///"):
            rel = url[len("file:///"):]
            target = OUT_DIR / rel if rel else OUT_DIR
            if target.is_dir():
                target = target / "index.html"
            if target.is_file():
                route.fulfill(path=str(target))
                return
        route.fallback()

    page.route("**/*", _serve_static)
    return page