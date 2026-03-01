# API Reference

## Base URL

```
http://<raspberry-pi-ip>       # Production (port 80)
http://<raspberry-pi-ip>:5000  # Development
```

## Authentication

Admin endpoints (`/api/admin/*`) require a Bearer token:

```
Authorization: Bearer <token>
```

Get a token from the device itself:

```http
GET /api/auth/token
```

Only accessible from localhost (`127.0.0.1` / `::1`). Returns `403` from any other IP.

**Response:**
```json
{ "token": "abc123..." }
```

---

## Analytics

### Get Dashboard Statistics

```http
GET /api/stats/<layout>
```

Returns PostHog analytics formatted for the requested dashboard layout.

**Layouts:** `classic`, `modern`, `analytics`, `executive`

**Classic** — 3 metrics:
```json
{
  "top":   { "label": "Events", "value": 1234 },
  "left":  { "label": "Users",  "value": 56 },
  "right": { "label": "Views",  "value": 89 },
  "demo_mode": false
}
```

**Modern** — 6 metrics + timestamp:
```json
{
  "primary":        { "label": "Events",   "value": 1500 },
  "secondaryLeft":  { "label": "Users",    "value": 3000 },
  "secondaryRight": { "label": "Views",    "value": 4500 },
  "miniStat1":      { "label": "Sessions", "value": 200 },
  "miniStat2":      { "label": "Avg/User", "value": 3.8 },
  "miniStat3":      { "label": "Events/h", "value": 12 },
  "demo_mode": false,
  "lastUpdated": "2024-01-20T12:00:00Z"
}
```

Returns `404` for unknown layouts, `503` with `{"error": "network_lost", "redirect": "/setup"}` when offline.

### Get Raw Metrics

```http
GET /api/stats
```

Returns all PostHog metrics without layout formatting. Includes `last_updated` timestamp.

### Get Available Metrics

```http
GET /api/metrics/available
```

Returns the list of metric types available for dashboard configuration (events_24h, unique_users_24h, page_views_24h, sessions_24h, events_1h, avg_events_per_user, custom_events_24h).

### Health Check

```http
GET /api/health
```

```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T12:00:00Z",
  "ap_mode": false
}
```

---

## Configuration

### Get Config Version

```http
GET /api/config/version
```

Returns a hash of the current config for change detection (polled by the frontend).

```json
{
  "version": "a1b2c3d4",
  "timestamp": "2024-01-20T12:00:00Z"
}
```

### Get Device Config (auth required)

```http
GET /api/admin/config
```

Returns the full device config including posthog, display, network (with live IP), advanced, and ota sections.

### Update Device Config (auth required)

```http
POST /api/admin/config
Content-Type: application/json
```

Merges the provided keys into the config. Allowed top-level keys: `posthog`, `display`, `network`, `advanced`, `ota`, `custom_themes`. Returns `400` for unknown keys.

### Delete PostHog Config (auth required)

```http
DELETE /api/admin/config
```

Clears PostHog credentials (api_key, project_id) from the device config.

### Validate PostHog Credentials (auth required)

```http
POST /api/admin/config/validate/posthog
Content-Type: application/json
```

**Body:**
```json
{
  "api_key": "phx_...",
  "project_id": "12345",
  "host": "https://app.posthog.com"
}
```

Tests the credentials against the PostHog API. Host must be a `posthog.com` domain. Returns `{"valid": true}` on success.

---

## Network

### Scan WiFi Networks

```http
GET /api/network/scan
```

Returns array of visible WiFi networks with SSID, signal quality, and encryption status.

### Connect to WiFi (auth required)

```http
POST /api/network/connect
Content-Type: application/json
```

**Body:**
```json
{ "ssid": "MyNetwork", "password": "secret123" }
```

SSID must be 1-32 alphanumeric characters. Password must be 8-63 printable ASCII characters.

### Network Status

```http
GET /api/network/status
```

Returns current network state: connectivity, WiFi SSID, signal strength, AP mode status.

---

## Themes

### List All Themes

```http
GET /api/themes
```

Returns all built-in and custom themes.

### Get Theme

```http
GET /api/themes/<theme_id>
```

Returns a single theme by ID. Returns `404` if not found.

### Export Theme

```http
GET /api/themes/<theme_id>/export
```

Returns theme data as downloadable JSON.

### Import Theme (auth required)

```http
POST /api/themes/import
Content-Type: application/json
```

Imports a theme from JSON data.

### Create Custom Theme (auth required)

```http
POST /api/themes/custom
Content-Type: application/json
```

**Body:**
```json
{ "id": "my-theme", "theme": { "name": "My Theme", "colors": { ... } } }
```

### Delete Custom Theme (auth required)

```http
DELETE /api/themes/custom/<theme_id>
```

Deletes a custom theme. Returns `404` for built-in or missing themes.

---

## OTA Updates

All OTA endpoints require admin auth. See [OTA_README.md](OTA_README.md) for full documentation.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/ota/status` | Current OTA status |
| GET | `/api/admin/ota/check` | Check for updates |
| POST | `/api/admin/ota/update` | Pull latest updates |
| POST | `/api/admin/ota/switch-branch` | Switch git branch |
| GET | `/api/admin/ota/branches` | List remote branches |
| GET | `/api/admin/ota/backups` | List backup tags |
| POST | `/api/admin/ota/rollback` | Rollback to backup |
| GET/POST | `/api/admin/ota/config` | OTA configuration |
| POST | `/api/admin/ota/update-cron` | Update cron schedule |
| GET | `/api/admin/ota/test-connection` | Test git connectivity |
| GET | `/api/admin/ota/history` | Update log history |
| POST | `/api/admin/ota/clean-cache` | Clean git cache |

---

## Error Responses

```json
{
  "error": "Error description"
}
```

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request / validation error |
| 401 | Invalid API key (PostHog validation) |
| 403 | Invalid or missing auth token |
| 404 | Resource not found |
| 408 | Timeout (PostHog validation) |
| 500 | Server error |
| 503 | Network lost / service unavailable |
