"""Tests for PostHog integration — the demo-critical data path.

Covers: fetch_posthog_metrics(), fetch_dashboard_stats(),
/api/stats/<layout>, and error/fallback behaviour.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from helpers import make_posthog_event, mock_posthog_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _events_fixture():
    """A realistic set of PostHog events for metric calculation tests."""
    now = datetime.now(timezone.utc)
    return [
        make_posthog_event("$pageview", "user-a", "sess-1", (now - timedelta(minutes=10)).isoformat()),
        make_posthog_event("$pageview", "user-a", "sess-1", (now - timedelta(minutes=9)).isoformat()),
        make_posthog_event("button_click", "user-b", "sess-2", (now - timedelta(minutes=30)).isoformat()),
        make_posthog_event("$pageview", "user-c", "sess-3", (now - timedelta(hours=2)).isoformat()),
        make_posthog_event("form_submit", "user-c", "sess-3", (now - timedelta(hours=3)).isoformat()),
        make_posthog_event("$pageleave", "user-a", "sess-1", (now - timedelta(minutes=5)).isoformat()),
        make_posthog_event("signup", "user-d", None, (now - timedelta(hours=5)).isoformat()),
    ]


# ---------------------------------------------------------------------------
# fetch_posthog_metrics — unit tests
# ---------------------------------------------------------------------------


@patch("app.subprocess.run")  # ping in check_and_start_wap_if_needed
@patch("app.requests.get")
def test_returns_all_metric_keys(mock_get, mock_subprocess, app_client, configured_posthog):
    """All 7 metric keys + recent_events + demo_mode: False must be present."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()

    assert error is None
    expected_keys = {
        "events_24h", "unique_users_24h", "page_views_24h",
        "custom_events_24h", "sessions_24h", "events_1h",
        "avg_events_per_user", "recent_events", "demo_mode",
    }
    assert expected_keys == set(metrics.keys())
    assert metrics["demo_mode"] is False


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_unique_users_counted_by_distinct_id(mock_get, mock_subprocess, app_client, configured_posthog):
    """Unique users = number of distinct distinct_id values."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    import app as app_module

    metrics, _ = app_module.fetch_posthog_metrics()
    # user-a, user-b, user-c, user-d = 4
    assert metrics["unique_users_24h"] == 4


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_pageview_vs_custom_separated(mock_get, mock_subprocess, app_client, configured_posthog):
    """$pageview counted as page_views; non-$pageview/non-$pageleave as custom."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    import app as app_module

    metrics, _ = app_module.fetch_posthog_metrics()
    assert metrics["page_views_24h"] == 3  # 3 $pageview events
    # custom = button_click + form_submit + signup = 3 (excluding $pageview and $pageleave)
    assert metrics["custom_events_24h"] == 3


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_sessions_exclude_null_session_ids(mock_get, mock_subprocess, app_client, configured_posthog):
    """Sessions counted by distinct $session_id; events without session_id excluded."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    import app as app_module

    metrics, _ = app_module.fetch_posthog_metrics()
    # sess-1, sess-2, sess-3 (user-d has no session_id)
    assert metrics["sessions_24h"] == 3


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_events_1h_filters_by_timestamp(mock_get, mock_subprocess, app_client, configured_posthog):
    """events_1h counts only events from the last hour."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    import app as app_module

    metrics, _ = app_module.fetch_posthog_metrics()
    # Events within 1h: user-a @10min, user-a @9min, user-b @30min, user-a @5min = 4
    assert metrics["events_1h"] == 4


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_avg_events_per_user_zero_division(mock_get, mock_subprocess, app_client, configured_posthog):
    """avg_events_per_user = 0 when there are no events (no ZeroDivisionError)."""
    mock_get.return_value = mock_posthog_response([])

    import app as app_module

    # First call returns empty, second call (7-day fallback) also returns empty
    metrics, _ = app_module.fetch_posthog_metrics()
    assert metrics["avg_events_per_user"] == 0


def test_no_credentials_returns_none(app_client):
    """Without PostHog credentials, returns (None, error message)."""
    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert metrics is None
    assert "not configured" in error


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_401_returns_invalid_key_error(mock_get, mock_subprocess, app_client, configured_posthog):
    mock_get.return_value = mock_posthog_response(status_code=401)

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert metrics is None
    assert "Invalid API key" in error


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_403_returns_missing_permissions(mock_get, mock_subprocess, app_client, configured_posthog):
    mock_get.return_value = mock_posthog_response(status_code=403)

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert metrics is None
    assert "Missing permissions" in error


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_500_returns_demo_metrics(mock_get, mock_subprocess, app_client, configured_posthog):
    """Server error returns demo metrics as fallback."""
    mock_get.return_value = mock_posthog_response(status_code=500)

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert error is None
    assert metrics["demo_mode"] is True
    assert metrics["events_24h"] == 142  # DEMO_METRICS value


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_connection_error_returns_network_error(mock_get, mock_subprocess, app_client, configured_posthog):
    mock_get.side_effect = requests.exceptions.ConnectionError("No route to host")

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert metrics is None
    assert error == "NETWORK_ERROR"


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_timeout_returns_network_error(mock_get, mock_subprocess, app_client, configured_posthog):
    mock_get.side_effect = requests.exceptions.Timeout("Read timed out")

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert metrics is None
    assert error == "NETWORK_ERROR"


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_empty_24h_retries_7day(mock_get, mock_subprocess, app_client, configured_posthog):
    """Empty 24h results triggers a retry with 7-day window."""
    events = _events_fixture()
    empty_resp = mock_posthog_response([])
    full_resp = mock_posthog_response(events)
    mock_get.side_effect = [empty_resp, full_resp]

    import app as app_module

    metrics, error = app_module.fetch_posthog_metrics()
    assert error is None
    assert metrics["events_24h"] == len(events)
    assert mock_get.call_count == 2


# ---------------------------------------------------------------------------
# /api/stats/<layout> — route-level tests
# ---------------------------------------------------------------------------


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_classic_layout_response_shape(mock_get, mock_subprocess, app_client, configured_posthog):
    """/api/stats/classic returns top, left, right with label + value."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    response = app_client.get("/api/stats/classic")
    assert response.status_code == 200
    data = response.get_json()

    for position in ("top", "left", "right"):
        assert position in data
        assert "label" in data[position]
        assert "value" in data[position]


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_modern_layout_response_shape(mock_get, mock_subprocess, app_client, configured_posthog):
    """/api/stats/modern returns primary, secondaryLeft/Right, miniStat1/2/3, lastUpdated."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    response = app_client.get("/api/stats/modern")
    assert response.status_code == 200
    data = response.get_json()

    for key in ("primary", "secondaryLeft", "secondaryRight", "miniStat1", "miniStat2", "miniStat3"):
        assert key in data
    assert "lastUpdated" in data


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_executive_layout_has_recent_events(mock_get, mock_subprocess, app_client, configured_posthog):
    """/api/stats/executive includes recent_events list."""
    mock_get.return_value = mock_posthog_response(_events_fixture())

    response = app_client.get("/api/stats/executive")
    assert response.status_code == 200
    data = response.get_json()
    assert "recent_events" in data
    assert isinstance(data["recent_events"], list)


def test_nonexistent_layout_returns_404(app_client):
    """/api/stats/nonexistent returns 404."""
    response = app_client.get("/api/stats/nonexistent")
    assert response.status_code == 404


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_network_error_returns_503_with_redirect(mock_get, mock_subprocess, app_client, configured_posthog):
    """Network error returns 503 with {error: 'network_lost', redirect: '/setup'}."""
    mock_get.side_effect = requests.exceptions.ConnectionError()

    response = app_client.get("/api/stats/classic")
    assert response.status_code == 503
    data = response.get_json()
    assert data["error"] == "network_lost"
    assert data["redirect"] == "/setup"


@patch("app.subprocess.run")
@patch("app.requests.get")
def test_recent_events_user_truncated(mock_get, mock_subprocess, app_client, configured_posthog):
    """recent_events[*].user is truncated to 8 characters."""
    events = [make_posthog_event("$pageview", "very-long-distinct-id-1234567890")]
    mock_get.return_value = mock_posthog_response(events)

    import app as app_module

    metrics, _ = app_module.fetch_posthog_metrics()
    assert len(metrics["recent_events"][0]["user"]) == 8
