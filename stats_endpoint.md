the BE has a stats endpoint for each of the dashboards

# Classic

endpoint: `/api/stats/classic`

response:

```json
{
  "top": {
    "label": "Events",
    "value": 1234
  },
  "left": {
    "label": "Users",
    "value": 5678
  },
  "right": {
    "label": "Devices",
    "value": 91011
  },
  "demo_mode": false,
  "device_ip": "192.168.1.1"
}
```

# Modern
endpoint: `/api/stats/modern`

response:
```json
{
  "primary": {
    "label": "Active Users",
    "value": 1500
  },
  "secondaryLeft": {
    "label": "Total Events",
    "value": 3000
  },
  "secondaryRight": {
    "label": "Unique Devices",
    "value": 4500
  },
  miniStat1: {
    "label": "New Signups",
    "value": 200
  },
  miniStat2: {
    "label": "Errors",
    "value": 50
  },
"miniStat3": {
    "label": "API Calls",
    "value": 1200
  },
  "demo_mode": false,
  "device_ip": "192.168.1.1",
  "lastUpdated": "2023-10-01T12:00:00Z"
}
```

# Analytics
endpoint: `/api/stats/analytics`

response:
```json
{
  "center": {
    "label": "Total Events",
    "value": 5000
  },
  "top": {
    "label": "Active Users",
    "value": 2500
  },
  "left": {
    "label": "Unique Devices",
    "value": 3500
  },
  "right": {
    "label": "Errors",
    "value": 100
  },
  "bottom": {
    "label": "API Calls",
    "value": 2000
  },
"stat1": {
    "label": "New Signups",
    "value": 300
  },
  "stat2": {
    "label": "Bounce Rate",
    "value": 5.5
  },
  "stat3": {
    "label": "Session Duration",
    "value": 120
  },
  "demo_mode": false,
  "device_ip": "912.168.1.1",
  "lastUpdated": "2023-10-01T12:00:00Z
}

# Executive
endpoint: `/api/stats/executive`

response:
```json
{
  "north": {
    "label": "Total Revenue",
    "value": 100000
  },
  "east": {
    "label": "Monthly Active Users",
    "value": 20000
  },
  "south": {
    "label": "Churn Rate",
    "value": 2.5
  },
  "west": {
    "label": "New Customers",
    "value": 500
  },
  "northEast": {
    "label": "Customer Satisfaction",
    "value": 95
  },
  "southEast": {
    "label": "Support Tickets",
    "value": 150
  },
  "southWest": {
    "label": "Average Order Value",
    "value": 75
  },
  "northWest": {
    "label": "Conversion Rate",
    "value": 10.5
  },
  "demo_mode": false,
  "device_ip": "192.168.1.1",
  "lastUpdated": "2023-10-01T12:00:00Z
}
```
```
