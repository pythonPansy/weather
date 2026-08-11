# Weather App Integration Specification

**For**: Tight Lines Notification Engine Integration  
**Date**: 2026-08-11  
**Version**: 1.0

## Overview

The Tight Lines app requires two REST API endpoints from the weather app to enable tide-based fishing notifications. This document specifies the exact API contract, request/response formats, and implementation requirements.

## Required API Endpoints

### 1. List Tide Locations

**Endpoint**: `GET /api/locations`

**Purpose**: Return all available tide locations that the weather app tracks

**Request**:
- No parameters required
- No authentication required (or specify auth method)

**Response**: HTTP 200 OK

```json
[
  {
    "id": "string",
    "name": "string",
    "region": "string",
    "latitude": number,
    "longitude": number
  },
  ...
]
```

**Field Specifications**:

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | string | Yes | Unique identifier for this location (used in tide API calls) | `"plym-uk-001"` |
| `name` | string | Yes | Human-readable location name | `"Plymouth"` |
| `region` | string | Yes | Geographic region (UK counties or broader areas) | `"South Devon"` |
| `latitude` | number | Yes | Latitude in decimal degrees | `50.3755` |
| `longitude` | number | Yes | Longitude in decimal degrees | `-4.1427` |

**Example Response**:

```json
[
  {
    "id": "plym-uk-001",
    "name": "Plymouth",
    "region": "South Devon",
    "latitude": 50.3755,
    "longitude": -4.1427
  },
  {
    "id": "salc-uk-002",
    "name": "Salcombe",
    "region": "South Devon",
    "latitude": 50.2378,
    "longitude": -3.7698
  },
  {
    "id": "mine-uk-003",
    "name": "Minehead",
    "region": "North Somerset",
    "latitude": 51.2036,
    "longitude": -3.4723
  }
]
```

**Error Responses**:

- `500 Internal Server Error`: If weather app cannot retrieve locations

---

### 2. Get Tide Predictions

**Endpoint**: `GET /api/tides/{location_id}`

**Purpose**: Return tide predictions for a specific location and date range

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location_id` | string | Yes | Location ID from `/api/locations` endpoint |

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `start` | string (ISO 8601) | Yes | Start date/time for predictions | `"2026-08-11T00:00:00Z"` |
| `end` | string (ISO 8601) | Yes | End date/time for predictions | `"2026-08-18T23:59:59Z"` |

**Response**: HTTP 200 OK

```json
{
  "tides": [
    {
      "time": "string (ISO 8601)",
      "type": "string",
      "height": number,
      "phase": "string | null"
    },
    ...
  ]
}
```

**Field Specifications**:

| Field | Type | Required | Description | Example | Validation |
|-------|------|----------|-------------|---------|------------|
| `time` | string | Yes | Date/time of tide event in ISO 8601 format with timezone | `"2026-08-11T05:23:00Z"` | Valid ISO 8601 |
| `type` | string | Yes | Tide type | `"high"` or `"low"` | Must be `"high"` or `"low"` |
| `height` | number | Yes | Tide height in metres | `4.8` | Positive number |
| `phase` | string or null | **Yes** | Tide phase classification | `"spring"`, `"neap"`, `"medium"`, or `null` | See phase classification below |

**Tide Phase Classification** (Critical for Notifications):

The `phase` field is **required** for the notification engine to work. It must be one of:

- `"spring"`: Spring tide (high tidal range, around new/full moon)
- `"neap"`: Neap tide (low tidal range, around quarter moons)
- `"medium"`: Mid-range tide (between spring and neap)
- `null`: Phase classification unavailable or not applicable

**Classification Algorithm** (Recommendation):

If the weather app doesn't already classify spring/neap tides, here's a recommended approach:

1. **Spring tide**: High tide height > Mean High Water Springs (MHWS) threshold
2. **Neap tide**: High tide height < Mean High Water Neaps (MHWN) threshold
3. **Medium**: Between MHWS and MHWN
4. Alternatively: Use astronomical data (moon phase) to determine spring/neap cycle

**Example Request**:

```
GET /api/tides/plym-uk-001?start=2026-08-11T00:00:00Z&end=2026-08-18T23:59:59Z
```

**Example Response**:

```json
{
  "tides": [
    {
      "time": "2026-08-11T05:23:00Z",
      "type": "high",
      "height": 4.8,
      "phase": "spring"
    },
    {
      "time": "2026-08-11T11:42:00Z",
      "type": "low",
      "height": 1.2,
      "phase": "spring"
    },
    {
      "time": "2026-08-11T17:55:00Z",
      "type": "high",
      "height": 4.9,
      "phase": "spring"
    },
    {
      "time": "2026-08-12T00:08:00Z",
      "type": "low",
      "height": 1.1,
      "phase": "spring"
    }
  ]
}
```

**Error Responses**:

- `404 Not Found`: Location ID not found
- `400 Bad Request`: Invalid date format or date range too large
- `500 Internal Server Error`: Weather app cannot retrieve tide data

---

## Implementation Requirements

### 1. Data Freshness

- Tide predictions should cover at least **14 days** into the future
- Weather app should refresh tide data from external sources (Admiralty API, etc.) at least once per day
- Tight Lines will query the API on-demand (no caching required from weather app's perspective)

### 2. Performance

- `/api/locations` response time: < 500ms
- `/api/tides/{location_id}` response time: < 2 seconds
- Support for concurrent requests from multiple Tight Lines instances

### 3. Reliability

- **Uptime SLA**: 99.5% availability during peak hours (06:00-22:00 UK time)
- **Error Handling**: Return proper HTTP status codes and error messages
- **Rate Limiting**: If implementing rate limits, minimum 100 requests/minute per client

### 4. CORS (if browser access needed)

- Not required for server-to-server communication
- If Tight Lines frontend calls weather app directly, enable CORS for Tight Lines domain

### 5. Authentication (Optional)

**Recommendation**: Start without authentication for simplicity

If authentication is required:
- Use API key in `Authorization` header: `Authorization: Bearer <api-key>`
- OR Basic Auth: `Authorization: Basic <base64(username:password)>`
- Provide API key/credentials to Tight Lines team

### 6. Versioning

- Recommend versioned API: `/api/v1/locations`, `/api/v1/tides/{location_id}`
- This allows breaking changes in future without disrupting Tight Lines

---

## Example Integration Flow

### Startup: Location Sync

When Tight Lines app starts:

1. Call `GET /api/locations`
2. Store locations in Tight Lines database (cache)
3. Use cached locations for user preference forms
4. Re-sync locations periodically (e.g., daily)

### Daily: Notification Generation

Every morning at 06:00:

1. For each user with notifications enabled:
   - For each user's preferred location:
     - Call `GET /api/tides/{location_id}?start={today}&end={today+7days}`
     - Filter tides where `phase == "spring"` or `phase == "neap"`
     - Match phase against user's target species (bass/mullet on spring, smoothhound/rays on neap)
     - Generate notification if match found
2. Queue notifications for email delivery

### On-Demand: Tide Display Page

When user visits `/tides/{location_id}` on Tight Lines:

1. Fetch location from local database
2. Call `GET /api/tides/{weather_app_location_id}?start={today}&end={today+7days}`
3. Render tide table for user

---

## Testing Checklist

### Unit Tests (Weather App)

- [ ] `/api/locations` returns valid JSON array
- [ ] `/api/locations` includes all required fields
- [ ] `/api/tides/{location_id}` returns valid JSON
- [ ] `/api/tides/{location_id}` handles invalid location ID (404)
- [ ] `/api/tides/{location_id}` handles invalid date format (400)
- [ ] `/api/tides/{location_id}` correctly classifies spring/neap/medium phases

### Integration Tests (Tight Lines + Weather App)

- [ ] Tight Lines can fetch locations from weather app
- [ ] Tight Lines can fetch tide predictions for a known location
- [ ] Tight Lines correctly parses tide phase field
- [ ] Tight Lines handles weather app downtime gracefully (retries, error messages)
- [ ] End-to-end notification generation works with real weather app data

### Manual Testing

1. **Start weather app** on port 8001 (or configured port)
2. **Test locations endpoint**:
   ```bash
   curl http://localhost:8001/api/locations | jq
   ```
3. **Test tides endpoint** (replace with actual location ID):
   ```bash
   curl "http://localhost:8001/api/tides/plym-uk-001?start=2026-08-11T00:00:00Z&end=2026-08-18T00:00:00Z" | jq
   ```
4. **Verify phase classification**: Check that `phase` field is present and valid (`"spring"`, `"neap"`, `"medium"`, or `null`)

---

## Sample UK Tide Locations

Here are suggested initial locations for the weather app to support:

| Name | Region | Latitude | Longitude | Admiralty Station ID (if applicable) |
|------|--------|----------|-----------|--------------------------------------|
| Plymouth | South Devon | 50.3755 | -4.1427 | 0001A |
| Salcombe | South Devon | 50.2378 | -3.7698 | 0002B |
| Dartmouth | South Devon | 50.3521 | -3.5805 | 0003C |
| Torbay | South Devon | 50.4619 | -3.5253 | 0004D |
| Minehead | North Somerset | 51.2036 | -3.4723 | 0005E |
| Lynmouth | North Devon | 51.2289 | -3.8311 | 0006F |
| Ilfracombe | North Devon | 51.2089 | -4.1177 | 0007G |
| Bideford | North Devon | 51.0167 | -4.2083 | 0008H |

---

## Deployment Coordination

### Development Environment

- **Weather App**: `http://localhost:8001`
- **Tight Lines**: `http://localhost:8000`
- Test locally before deploying to staging/production

### Staging Environment

- **Weather App**: `https://weather-staging.example.com`
- **Tight Lines**: `https://tightlines-staging.example.com`
- Configure `WEATHER_APP_BASE_URL=https://weather-staging.example.com` in Tight Lines `.env`

### Production Environment

- **Weather App**: `https://weather.example.com`
- **Tight Lines**: `https://tightlines.app`
- Configure `WEATHER_APP_BASE_URL=https://weather.example.com` in Tight Lines `.env`

### Deployment Order

1. Deploy weather app first with new API endpoints
2. Verify endpoints are accessible and returning correct data
3. Deploy Tight Lines with `WEATHER_APP_BASE_URL` configured
4. Monitor Tight Lines logs for API errors
5. Test notification generation manually before enabling for all users

---

## OpenAPI Specification (Optional)

For automatic client generation and better documentation, consider providing an OpenAPI 3.0 spec:

```yaml
openapi: 3.0.0
info:
  title: Weather App API
  version: 1.0.0
  description: Tide predictions and location data
servers:
  - url: http://localhost:8001
    description: Development
paths:
  /api/locations:
    get:
      summary: List all tide locations
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  required: [id, name, region, latitude, longitude]
                  properties:
                    id: {type: string}
                    name: {type: string}
                    region: {type: string}
                    latitude: {type: number}
                    longitude: {type: number}
  /api/tides/{location_id}:
    get:
      summary: Get tide predictions for a location
      parameters:
        - name: location_id
          in: path
          required: true
          schema: {type: string}
        - name: start
          in: query
          required: true
          schema: {type: string, format: date-time}
        - name: end
          in: query
          required: true
          schema: {type: string, format: date-time}
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                required: [tides]
                properties:
                  tides:
                    type: array
                    items:
                      type: object
                      required: [time, type, height, phase]
                      properties:
                        time: {type: string, format: date-time}
                        type: {type: string, enum: [high, low]}
                        height: {type: number}
                        phase: {type: string, enum: [spring, neap, medium], nullable: true}
```

---

## Questions / Support

**Tight Lines Contact**: 
- Repository: https://github.com/pythonPansy/tight_lines_app
- Issues: Create GitHub issue with `weather-integration` label

**Key Decisions Needed**:
1. Authentication method (API key, Basic Auth, or none)?
2. Rate limiting requirements?
3. Tide phase classification algorithm (how does weather app determine spring/neap)?
4. Expected response times and SLA commitments?

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-11 | Initial specification |
