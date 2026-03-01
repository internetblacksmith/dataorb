"""Shared test helpers for building mock PostHog data."""

from datetime import datetime, timezone
from unittest.mock import MagicMock


def make_posthog_event(
    event="$pageview",
    distinct_id="user-abc",
    session_id="sess-001",
    timestamp=None,
):
    """Build a realistic PostHog event dict."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    result = {
        "event": event,
        "distinct_id": distinct_id,
        "timestamp": timestamp,
        "properties": {},
    }
    if session_id:
        result["properties"]["$session_id"] = session_id
    return result


def mock_posthog_response(events=None, status_code=200):
    """Build a mock requests.Response for PostHog API calls."""
    resp = MagicMock()
    resp.status_code = status_code
    if events is not None:
        resp.json.return_value = {"results": events}
    else:
        resp.json.return_value = {"results": []}
    return resp
