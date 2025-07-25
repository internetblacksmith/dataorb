# API Reference

## Overview

PostHog Pi provides a RESTful API for accessing analytics data and managing the device.

## Base URL

```
http://<raspberry-pi-ip>:5000
```

## Endpoints

### Analytics

#### Get Statistics
```http
GET /api/stats
```

Returns PostHog analytics for the last 24 hours.

**Response:**
```json
{
  "events_count": 1234,
  "unique_users": 456,
  "page_views": 789,
  "avg_events_per_user": 2.7
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
