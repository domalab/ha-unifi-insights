# Unifi Network API Documentation

## Overview

The UniFi Network API enables developers to monitor and manage UniFi deployments programmatically. It provides powerful tools to access application data, retrieve detailed device information, monitor performance, and manage infrastructure efficiently.

---

## Getting Started

### Authentication

API requests require an API Key for secure and personalized access. Follow the steps below to obtain an API Key:

1. Open your site in UniFi Site Manager at [unifi.ui.com](https://unifi.ui.com).
2. Navigate to **Control Plane** → **Admins & Users**.
3. Select your Admin.
4. Click **Create API Key**.
5. Provide a name for your API Key and copy it. The key will only be displayed once.
6. Click **Done** to securely store the key.

**Usage**
Include the API Key in the `X-API-Key` header of your API requests:

```bash
curl -k -X GET 'https://192.168.10.1/proxy/network/integration/v1/sites' \  
  -H 'X-API-KEY: YOUR_API_KEY' \  
  -H 'Accept: application/json'
```

---

## API Endpoints

### Sites

#### List Local Sites (Paginated)

Retrieves all sites managed by the Network application.

**Endpoint:**

```http
GET /v1/sites
```

**Query Parameters:**

| Parameter | Type    | Description | Default |
|-----------|---------|-------------|---------|
| offset    | integer | Starting point of the list | 0       |
| limit     | integer | Maximum number of items to return | 25      |

**Response Schema:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 1000,
  "data": [
    {
      "id": "site-uuid",
      "name": "Site Name"
    }
  ]
}
```

---

### Devices

#### Execute an Action on a Specific Device

Perform a specified action (e.g., restart) on a device.

**Endpoint:**

```http
POST /v1/sites/{siteId}/devices/{deviceId}/actions
```

**Path Parameters:**

| Parameter | Type   | Required | Description           |
|-----------|--------|----------|-----------------------|
| siteId    | string | Yes      | Unique ID of the site |
| deviceId  | string | Yes      | Unique ID of the device |

**Request Body Schema:**

```json
{
  "action": "RESTART"
}
```

**Response Example:**

```json
{
  "status": "OK"
}
```

---

#### List Adopted Devices (Paginated)

Fetches a list of devices adopted within a site.

**Endpoint:**

```http
GET /v1/sites/{siteId}/devices
```

**Path Parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| siteId    | string | Yes      | Unique ID of the site |

**Query Parameters:**

| Parameter | Type    | Description | Default |
|-----------|---------|-------------|---------|
| offset    | integer | Starting point of the list | 0       |
| limit     | integer | Maximum number of items to return | 25      |

**Response Schema:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 1000,
  "data": [
    {
      "id": "device-uuid",
      "name": "Device Name",
      "model": "Device Model",
      "state": "ONLINE",
      "macAddress": "00:00:00:00:00:00",
      "ipAddress": "192.168.1.100",
      "features": ["switching", "accessPoint"],
      "interfaces": ["ports", "radios"]
    }
  ]
}
```

---

#### Get Detailed Information About a Device

Retrieve detailed information about a specific device, including uplink and interfaces.

**Endpoint:**

```http
GET /v1/sites/{siteId}/devices/{deviceId}
```

**Path Parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| siteId    | string | Yes      | Unique ID of the site |
| deviceId  | string | Yes      | Unique ID of the device |

**Response Schema:**

```json
{
  "id": "device-uuid",
  "name": "Device Name",
  "model": "Device Model",
  "state": "ONLINE",
  "firmwareVersion": "1.0.0",
  "macAddress": "00:00:00:00:00:00",
  "uplink": {
    "deviceId": "uplink-device-uuid"
  },
  "interfaces": {
    "ports": [
      {
        "idx": 1,
        "state": "UP",
        "connector": "RJ45",
        "maxSpeedMbps": 1000
      }
    ],
    "radios": [
      {
        "wlanStandard": "802.11ac",
        "frequencyGHz": "5",
        "channel": 36
      }
    ]
  }
}
```

---

#### Get Latest Statistics of a Device

Retrieve real-time statistics for a specific device, such as CPU and memory usage.

**Endpoint:**

```http
GET /v1/sites/{siteId}/devices/{deviceId}/statistics/latest
```

**Path Parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| siteId    | string | Yes      | Unique ID of the site |
| deviceId  | string | Yes      | Unique ID of the device |

**Response Schema:**

```json
{
  "uptimeSec": 100000,
  "cpuUtilizationPct": 20.5,
  "memoryUtilizationPct": 45.7,
  "uplink": {
    "txRateBps": 5000000,
    "rxRateBps": 3000000
  }
}
```

---

### Clients

#### List Connected Clients (Paginated)

Retrieve a list of connected clients within a site.

**Endpoint:**

```http
GET /v1/sites/{siteId}/clients
```

**Path Parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| siteId    | string | Yes      | Unique ID of the site |

**Query Parameters:**

| Parameter | Type    | Description | Default |
|-----------|---------|-------------|---------|
| offset    | integer | Starting point of the list | 0       |
| limit     | integer | Maximum number of items to return | 25      |

**Response Schema:**

```json
{
  "offset": 0,
  "limit": 25,
  "count": 10,
  "totalCount": 100,
  "data": [
    {
      "id": "client-uuid",
      "name": "Client Name",
      "ipAddress": "192.168.1.10",
      "type": "WIRELESS",
      "macAddress": "00:00:00:00:00:00",
      "uplinkDeviceId": "device-uuid"
    }
  ]
}
```

---

## Error Responses

API responses include detailed error messages for debugging.

**Example Error Response:**

```json
{
  "statusCode": 400,
  "statusName": "UNAUTHORIZED",
  "message": "Missing credentials",
  "timestamp": "2024-11-27T08:13:46.966Z",
  "requestPath": "/v1/sites/{siteId}",
  "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

---

## About the Application

Retrieve application version and general information.

**Endpoint:**

```http
GET /v1/info
```

**Response Schema:**

```json
{
  "applicationVersion": "9.1.0"
}
```

---

## Notes

- Always secure your API Key and do not share it publicly.
- Refer to the [official documentation](https://unifi.ui.com) for detailed insights.

Happy coding!
