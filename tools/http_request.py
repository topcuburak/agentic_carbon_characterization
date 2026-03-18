"""
HTTP request tool for calling the local mock API server.
"""

import json
import urllib.request
import urllib.error
from config import MOCK_API_HOST, MOCK_API_PORT


def http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str = "",
) -> str:
    """
    Make an HTTP request to the local mock API server.
    Returns status code and response body.
    """
    if headers is None:
        headers = {}

    # Ensure requests only go to the mock server
    allowed_prefix = f"http://{MOCK_API_HOST}:{MOCK_API_PORT}"
    if not url.startswith(allowed_prefix):
        return (
            f"Error: Only requests to the mock API server are allowed. "
            f"URL must start with {allowed_prefix}"
        )

    method = method.upper()
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        return f"Error: Unsupported HTTP method '{method}'"

    try:
        data = body.encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, method=method)

        # Set default content type for requests with body
        if data and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        for key, value in headers.items():
            req.add_header(key, value)

        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            resp_body = resp.read().decode("utf-8")

            # Try to pretty-print JSON responses
            try:
                parsed = json.loads(resp_body)
                resp_body = json.dumps(parsed, indent=2)
            except (json.JSONDecodeError, ValueError):
                pass

            if len(resp_body) > 5000:
                resp_body = resp_body[:5000] + "\n... [response truncated]"

            return f"Status: {status}\n\n{resp_body}"

    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        return f"HTTP Error {e.code}: {e.reason}\n{body_text}"
    except urllib.error.URLError as e:
        return f"Error: Could not connect to mock API server at {allowed_prefix}. Is it running? ({e.reason})"
    except Exception as e:
        return f"Error making HTTP request: {e}"
