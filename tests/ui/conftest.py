"""Playwright UI test configuration and fixtures."""

import os
import signal
import socket
import subprocess
import time
import urllib.request

import pytest
from playwright.sync_api import Page

# Track server process for cleanup
_server_proc = None


def _kill_port_process(port: int):
    """Kill any process using the specified port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except (ProcessLookupError, ValueError):
                    pass
            time.sleep(1)
    except Exception:
        pass


def _verify_wiki_server(port: int) -> bool:
    """Verify the server is Wiki Notebook (not another app)."""
    try:
        response = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2)
        content = response.read().decode("utf-8")
        return "Wiki|Note" in content or 'id="editor-container"' in content
    except Exception:
        return False


def _start_wiki_server(port: int) -> subprocess.Popen:
    """Start the Wiki Notebook server."""
    env = os.environ.copy()
    env["FLASK_DEBUG"] = "0"
    env["FLASK_APP"] = "wiki_notebook.app"

    proc = subprocess.Popen(
        ["python", "-m", "wiki_notebook"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    return proc


@pytest.fixture(scope="session", autouse=True)
def _live_server():
    """Start a live Flask server for UI testing (session scope)."""
    global _server_proc

    port = 5000

    # First, kill any existing process on the port
    _kill_port_process(port)

    # Start our server
    _server_proc = _start_wiki_server(port)

    # Wait for server to be ready (up to 15 seconds)
    max_wait = 15.0
    start = time.time()
    server_ready = False

    while time.time() - start < max_wait:
        time.sleep(0.5)
        if _verify_wiki_server(port):
            server_ready = True
            break

    if not server_ready:
        # Get error output for debugging
        stderr_output = ""
        if _server_proc:
            try:
                stderr_output = _server_proc.stderr.read().decode()
            except Exception:
                pass
            _server_proc.kill()
        raise RuntimeError(
            f"Server failed to start on port {port}\nStderr: {stderr_output}"
        )

    yield

    # Cleanup
    if _server_proc:
        _server_proc.kill()
        try:
            _server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass


@pytest.fixture(scope="session")
def base_url(_live_server) -> str:
    """Return the base URL for the app (used by pytest-playwright)."""
    return "http://127.0.0.1:5000"


@pytest.fixture
def note_data():
    """Sample note data for testing."""
    return {
        "title": "Test Note Title",
        "body": "This is the **test note** body with _markdown_.",
    }


@pytest.fixture
def app_page(page: Page, base_url: str) -> Page:
    """Create a page that has navigated to the app."""
    # Set a desktop viewport
    page.set_viewport_size({"width": 1280, "height": 800})

    page.goto(base_url)

    # Wait for the page to load - check for editor container instead
    page.wait_for_selector("#editor-container", timeout=10000)

    # Wait a bit for JS to initialize
    page.wait_for_timeout(500)

    return page
