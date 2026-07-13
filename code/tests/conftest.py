import subprocess
import time
import urllib.request
import urllib.error

import pytest


@pytest.fixture(scope="session")
def build_site():
    result = subprocess.run(
        ["make", "build"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed:\n{result.stderr}"
    return True


BASE_URL = "http://localhost:3000"


@pytest.fixture(scope="session")
def server(build_site):
    proc = subprocess.Popen(
        ["make", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(30):
        try:
            urllib.request.urlopen(BASE_URL, timeout=1)
            break
        except urllib.error.URLError:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Server did not start within 15 seconds")
    yield
    proc.terminate()
    proc.wait()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "base_url": "http://localhost:3000"}


@pytest.fixture(autouse=True)
def setup_page(page, server):
    page.set_default_timeout(10000)
    return page
