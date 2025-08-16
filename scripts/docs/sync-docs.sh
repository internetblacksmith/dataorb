#!/bin/bash

# Sync documentation files for Docsify
# This script copies and processes markdown files for the documentation website

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📚 Syncing documentation for Docsify...${NC}"

# Create docs directory if it doesn't exist
mkdir -p docs

# Copy main documentation files
echo -e "${YELLOW}Copying documentation files...${NC}"

# Copy and rename README.md to be the home page
cp README.md docs/README.md
echo -e "${GREEN}✓ Copied README.md${NC}"

# Copy other documentation files
for file in QUICK_START.md PROJECT_CONTEXT.md OTA_README.md CLAUDE.md DOCUMENTATION_CHECKLIST.md; do
    if [ -f "$file" ]; then
        cp "$file" "docs/$file"
        echo -e "${GREEN}✓ Copied $file${NC}"
    fi
done

# Create _sidebar.md for navigation
echo -e "\n${YELLOW}Creating navigation...${NC}"
cat > docs/_sidebar.md << 'EOF'
<!-- docs/_sidebar.md -->

* **Getting Started**
  * [Overview](README.md)
  * [Quick Start](QUICK_START.md)
  * [Installation](QUICK_START.md#-easy-installation-on-fresh-raspberry-pi)

* **Configuration**
  * [PostHog Setup](QUICK_START.md#️-configuration)
  * [Display Setup](QUICK_START.md#-hyperpixel-round-display-setup)
  * [Device Config](README.md#device-configuration)

* **Features**
  * [Dashboard](README.md#features)
  * [API Endpoints](README.md#api-endpoints)
  * [OTA Updates](OTA_README.md)
  * [Quality Gate](README.md#quality-gate)

* **Development**
  * [Development Guide](CLAUDE.md)
  * [Project Context](PROJECT_CONTEXT.md)
  * [Documentation Guide](DOCUMENTATION_CHECKLIST.md)
  * [Quality Standards](CLAUDE.md#quality-gate-requirements)

* **API Reference**
  * [Stats API](README.md#api-endpoints)
  * [OTA API](OTA_README.md#api-endpoints)
  * [Configuration API](OTA_README.md#configuration)

* **Troubleshooting**
  * [Common Issues](QUICK_START.md#-troubleshooting)
  * [Service Status](QUICK_START.md#service-status)
  * [Logs](QUICK_START.md#check-logs)

* **Links**
  * [GitHub Repository](https://github.com/jabawack81/posthog_pi)
  * [PostHog](https://posthog.com)
EOF
echo -e "${GREEN}✓ Created _sidebar.md${NC}"

# Create _navbar.md for top navigation
cat > docs/_navbar.md << 'EOF'
<!-- docs/_navbar.md -->

* [Home](/)
* [Quick Start](QUICK_START.md)
* [API](README.md#api-endpoints)
* [GitHub](https://github.com/jabawack81/posthog_pi)
EOF
echo -e "${GREEN}✓ Created _navbar.md${NC}"

# Create _coverpage.md
cat > docs/_coverpage.md << 'EOF'
<!-- _coverpage.md -->

![logo](https://raw.githubusercontent.com/PostHog/posthog.com/main/contents/images/logo/posthog-logo.svg ':size=200')

# PostHog Pi <small>1.0</small>

> IoT Analytics Dashboard for Raspberry Pi

- 🚀 Real-time PostHog analytics on a 480x480 round display
- 🔧 One-command installation and setup
- 📊 Configurable metrics and dashboards
- 🔄 Over-the-air (OTA) updates
- 🌐 Web-based configuration interface
- 📱 Optimized for HyperPixel Round display

[Get Started](QUICK_START.md)
[GitHub](https://github.com/jabawack81/posthog_pi)

<!-- background image -->
![](https://raw.githubusercontent.com/PostHog/posthog.com/main/contents/images/product/product-analytics.png)
EOF
echo -e "${GREEN}✓ Created _coverpage.md${NC}"

# Create .nojekyll file for GitHub Pages
touch docs/.nojekyll
echo -e "${GREEN}✓ Created .nojekyll${NC}"

# Create a custom 404 page
cat > docs/_404.md << 'EOF'
# Page Not Found 🔍

The page you're looking for doesn't exist.

* [Go to Homepage](/)
* [Quick Start Guide](QUICK_START.md)
* [View on GitHub](https://github.com/jabawack81/posthog_pi)
EOF
echo -e "${GREEN}✓ Created _404.md${NC}"

# Add API documentation page
cat > docs/api.md << 'EOF'
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
EOF
echo -e "${GREEN}✓ Created api.md${NC}"

# Update sidebar to include API page
# Using a more portable approach
cp docs/_sidebar.md docs/_sidebar.md.tmp
awk '/\* \*\*API Reference\*\*/ {print; print "  * [Overview](api.md)"; next} 1' docs/_sidebar.md.tmp > docs/_sidebar.md
rm -f docs/_sidebar.md.tmp

echo -e "\n${GREEN}✅ Documentation synced successfully!${NC}"
echo -e "${BLUE}📄 Documentation is ready for Docsify at: docs/${NC}"
echo -e "${BLUE}🌐 To preview locally, run: npx docsify serve docs${NC}"