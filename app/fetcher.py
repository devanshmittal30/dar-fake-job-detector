"""app/fetcher.py
Safe job advertisement link fetcher for DAR Fake Job Detector.

Implements all safety rules defined in docs/03_TECHNICAL_DESIGN.md (section 9):
1. Protocols: http and https only (rejects file://, ftp://, gopher://, etc.).
2. SSRF Protection: Resolves hostname to IP before making request; rejects private,
   loopback, link-local, multicast, and cloud metadata addresses (e.g. 127.0.0.1, 10.x, 169.254.169.254).
3. Timeout: Strictly 8 seconds.
4. Size Limit: Maximum 1 MB (1,048,576 bytes); aborts stream if exceeded.
5. Redirects: Maximum 3 redirects followed manually, re-validating the resolved IP on each hop.
6. Cookies: No cookies sent or stored across requests.
7. Plain User-Agent: Identifies DAR clearly.
8. Text Extraction: Uses BeautifulSoup to remove scripts/styles/navigation and extract clean body text.
"""

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests

USER_AGENT = "DAR-JobFetcher/1.0 (+https://github.com/devanshmittal30/dar-fake-job-detector)"
TIMEOUT_SECONDS = 8
MAX_BYTES = 1024 * 1024  # 1 MB
MAX_REDIRECTS = 3

# Tags to remove before text extraction
IGNORED_TAGS = [
    "script", "style", "noscript", "svg", "header", "footer",
    "nav", "aside", "form", "button", "select", "option", "iframe"
]


class FetchError(Exception):
    """Exception raised when URL fetching fails safety or extraction rules."""
    pass


def validate_url_safety(url: str) -> None:
    """Validate that the URL uses http/https and does not resolve to an unsafe IP address.

    Args:
        url: Full URL string.

    Raises:
        FetchError: If the URL or its resolved IP violates SSRF rules.
    """
    if not url or not isinstance(url, str):
        raise FetchError("Invalid URL provided.")

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        raise FetchError(f"Malformed URL: {e}")

    # 1. Protocol check: http/https only
    if parsed.scheme.lower() not in ("http", "https"):
        raise FetchError(f"Unsupported protocol '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise FetchError("URL must contain a valid hostname.")

    # 2. Reject explicit localhost names
    if hostname.lower() in ("localhost", "localhost.localdomain", "broadcasthost"):
        raise FetchError(f"Requests to local addresses ('{hostname}') are forbidden.")

    # 3. Resolve hostname and inspect all resolved IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise FetchError(f"Could not resolve hostname '{hostname}': {e}")
    except Exception as e:
        raise FetchError(f"DNS resolution error for '{hostname}': {e}")

    if not addr_info:
        raise FetchError(f"No IP addresses resolved for hostname '{hostname}'.")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise FetchError(f"Invalid resolved IP format: '{ip_str}'")

        # Reject private, loopback, link-local, reserved, multicast, or metadata addresses
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or str(ip) in ("0.0.0.0", "255.255.255.255", "169.254.169.254")
        ):
            raise FetchError(
                f"Security violation: Resolved IP '{ip_str}' belongs to a private, loopback, or internal network."
            )


def extract_visible_text(html_content: str) -> str:
    """Extract clean, visible job advertisement text from raw HTML using BeautifulSoup.

    Args:
        html_content: Raw HTML text.

    Returns:
        Clean, extracted text string.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove non-content tags
    for tag in soup(IGNORED_TAGS):
        tag.decompose()

    # Extract text with single spaces separating elements
    text = soup.get_text(separator=" ", strip=True)

    # Collapse consecutive whitespace characters
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    return cleaned_text


def safe_fetch_job_text(url: str) -> str:
    """Safely fetch a job posting page and extract visible text.

    Enforces all SSRF protections, redirect limits, byte limits, and timeouts.

    Args:
        url: Destination URL.

    Returns:
        Extracted visible text from the page.

    Raises:
        FetchError: If the page cannot be fetched, exceeds safety limits, or has no readable text.
    """
    current_url = url.strip()
    redirects_followed = 0

    # Clean session without cookie persistence
    session = requests.Session()
    session.cookies.clear()

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    while True:
        # Validate URL safety before EVERY request (including redirect hops)
        validate_url_safety(current_url)

        try:
            # allow_redirects=False to manually validate each hop against SSRF
            response = session.get(
                current_url,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
                allow_redirects=False,
                stream=True
            )
        except requests.exceptions.Timeout:
            raise FetchError(f"Connection timed out after {TIMEOUT_SECONDS} seconds.")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Network error while connecting to destination: {e}")

        # Handle redirects manually
        if response.status_code in (301, 302, 303, 307, 308):
            redirects_followed += 1
            if redirects_followed > MAX_REDIRECTS:
                raise FetchError(f"Too many redirects (exceeded maximum of {MAX_REDIRECTS}).")

            location = response.headers.get("Location")
            if not location:
                raise FetchError("Redirect response received with no Location header.")

            # Resolve relative redirect URLs against the current URL
            current_url = urljoin(current_url, location)
            continue

        # Handle non-success HTTP status codes
        if response.status_code != 200:
            raise FetchError(f"Server returned HTTP status code {response.status_code}.")

        # Check content type if provided
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and not any(t in content_type for t in ("text/html", "application/xhtml+xml", "text/plain")):
            raise FetchError(f"Unsupported content type '{content_type}'. Expected HTML web page.")

        # Read response content safely up to MAX_BYTES (1 MB)
        content_bytes = bytearray()
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content_bytes.extend(chunk)
                    if len(content_bytes) > MAX_BYTES:
                        raise FetchError(f"Page content exceeded maximum size limit of 1 MB.")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Error while reading page stream: {e}")

        break

    # Decode HTML text
    encoding = response.encoding or "utf-8"
    try:
        html_text = content_bytes.decode(encoding, errors="replace")
    except Exception:
        html_text = content_bytes.decode("utf-8", errors="replace")

    # Extract clean text via BeautifulSoup
    extracted = extract_visible_text(html_text)

    if not extracted or len(extracted.split()) < 5:
        raise FetchError("We couldn't read that page (it may need a login). Paste the text instead.")

    return extracted
