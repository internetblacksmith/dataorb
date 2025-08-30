# API Reference

## Overview

DataOrb provides a RESTful API for accessing analytics data and managing the device.

## Base URL

```
http://<raspberry-pi-ip>:5000
```

## Endpoints

### Analytics

#### Get Statistics
```http
GET /api/stats/<layout>
```

Returns PostHog analytics for the last 24 hours, formatted for the requested dashboard layout.

**Layouts:** `classic`, `modern`, `analytics`, `executive`

**Example — Classic (`/api/stats/classic`):**
```json
{
  "top":   { "label": "Events",  "value": 1234 },
  "left":  { "label": "Users",   "value": 5678 },
  "right": { "label": "Devices", "value": 91011 },
  "demo_mode": false,
  "device_ip": "192.168.1.1"
}
```

**Example — Modern (`/api/stats/modern`):**
```json
{
  "primary":        { "label": "Active Users",    "value": 1500 },
  "secondaryLeft":  { "label": "Total Events",    "value": 3000 },
  "secondaryRight": { "label": "Unique Devices",  "value": 4500 },
  "miniStat1":      { "label": "New Signups",     "value": 200 },
  "miniStat2":      { "label": "Errors",          "value": 50 },
  "miniStat3":      { "label": "API Calls",       "value": 1200 },
  "demo_mode": false,
  "device_ip": "192.168.1.1",
  "lastUpdated": "2023-10-01T12:00:00Z"
}
```

#### Get Health Status
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T12:00:00Z"
}
```

### Configuration

#### Get Available Metrics
```http
GET /api/metrics/available
```

Returns list of metrics available for dashboard configuration.

### OTA Updates

See [OTA API Documentation](OTA_README.md#api-endpoints) for complete OTA endpoints.

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid request
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "error": "Error description",
  "details": "Additional information"
}
```
