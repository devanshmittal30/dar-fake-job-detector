"""tests/test_fetcher.py
Unit tests for SSRF prevention, URL validation, and text extraction in app/fetcher.py.
Following docs/03_TECHNICAL_DESIGN.md (section 9) and prompt P9.
"""

import pytest
from app.fetcher import (
    FetchError,
    extract_visible_text,
    validate_url_safety,
)


def test_unsafe_urls_rejected():
    """Verify that all private, loopback, link-local, file, and metadata URLs are rejected."""
    unsafe_urls = [
        "http://localhost",
        "http://localhost:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "file:///C:/Windows/win.ini",
        "http://10.0.0.1/internal",
        "http://10.254.254.1",
        "http://192.168.1.1",
        "http://172.16.0.1",
        "ftp://example.com/job.txt",
        "gopher://evil.com",
        "javascript:alert(1)"
    ]

    for url in unsafe_urls:
        with pytest.raises(FetchError) as exc_info:
            validate_url_safety(url)
        # Ensure an informative security/protocol error is raised
        assert len(str(exc_info.value)) > 0, f"No error message for unsafe URL: {url}"


def test_invalid_and_empty_urls():
    """Verify that empty, None, and unresolvable hostnames raise FetchError."""
    with pytest.raises(FetchError):
        validate_url_safety("")

    with pytest.raises(FetchError):
        validate_url_safety(None)

    with pytest.raises(FetchError):
        validate_url_safety("https://this-domain-does-not-exist-at-all-xyz123456789.com")


def test_extract_visible_text():
    """Verify that HTML tags, scripts, and styles are stripped cleanly."""
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Careers at Acme Corp</title>
        <style>body { font-family: sans-serif; }</style>
        <script>console.log("analytics tracking");</script>
      </head>
      <body>
        <nav><a href="/">Home</a><a href="/jobs">Jobs</a></nav>
        <main>
          <h1>Senior Backend Engineer</h1>
          <p>Acme Corp is hiring a Senior Backend Engineer for our platform team.</p>
          <p>Responsibilities include building microservices with Python and PostgreSQL.</p>
        </main>
        <footer><p>&copy; 2026 Acme Corp. All rights reserved.</p></footer>
      </body>
    </html>
    """

    extracted = extract_visible_text(sample_html)

    # Content from body should be present
    assert "Senior Backend Engineer" in extracted
    assert "Acme Corp is hiring" in extracted
    assert "microservices with Python" in extracted

    # Script, style, nav, and footer must be stripped
    assert "console.log" not in extracted
    assert "font-family" not in extracted
    assert "analytics tracking" not in extracted
    assert "<nav>" not in extracted
