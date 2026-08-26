# SETU — Backend API & System Specification Documentation

Comprehensive documentation of the SETU Django REST API, GeoDjango schema, matching engine, AI disruption risk prediction model, and end-to-end integration workflows.

---

## 1. System Architecture

```
React (Frontend)  ──HTTP/JSON──►  Django REST API (backend/)
                                         │
                                         ├──► PostgreSQL + PostGIS (Docker)
                                         │
                                         └──► matching_engine (matching_engine/)
                                                  │ Direct in-process Python import
```

### Key Architectural Decisions
- **Zero-Latency Matching**: Django imports `matching_engine` directly in-process (`from matching_engine.scoring import score_resources`), executing candidate ranking in memory without external HTTP hops.
- **Geo-Aware Compatibility**: Supports GeoJSON Point format `{"type": "Point", "coordinates": [lon, lat]}` as well as direct `{ "latitude": 24.83, "longitude": 92.78 }` payloads across all endpoints.
- **Automated Hazard Cascades**: Ground condition reports (e.g. `road_status='blocked'`) automatically generate system alerts and mark active en-route allocations in affected districts as delayed.

---

## 2. Authentication & User Management

### 2.1 User Registration
- **Endpoint**: `POST /api/auth/register/`
- **Auth**: None (Public)
- **Request Body**:
```json
{
  "username": "officer_ananda",
  "password": "SecurePassword123!",
  "email": "ananda@setu.org",
  "role": "field_officer",
  "phone_number": "+919876543210",
  "preferred_language": "en",
  "district_id": 1
}
```
- **Response** (`201 Created`):
```json
{
  "message": "User successfully registered.",
  "user": {
    "id": 1,
    "username": "officer_ananda",
    "email": "ananda@setu.org",
    "role": "field_officer",
    "phone_number": "+919876543210",
    "preferred_language": "en",
    "district": 1,
    "district_name": "Cachar",
    "is_verified": false
  },
  "access": "<JWT_ACCESS_TOKEN>",
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

### 2.2 User Login
- **Endpoint**: `POST /api/auth/login/`
- **Auth**: None (Public)
- **Request Body**:
```json
{
  "username": "officer_ananda",
  "password": "SecurePassword123!"
}
```
- **Response** (`200 OK`): Returns `access`, `refresh`, and user profile payload.

### 2.3 Current User Profile
- **Endpoint**: `GET /api/auth/me/` | `PATCH /api/auth/me/`
- **Auth**: `Bearer <JWT_ACCESS_TOKEN>`

---

## 3. Core Domain Endpoints

### 3.1 Districts
- **`GET /api/districts/`**: List all districts with open needs count and available resources count.
- **`POST /api/districts/`**: Create new district (`name`, `state`, `population`, `centroid`).
- **`GET /api/districts/{id}/`**: District details.

### 3.2 Needs
- **`GET /api/needs/`**: List needs (filterable by `?status=open&type=medicine&district=1&urgency=critical`).
- **`POST /api/needs/`**: Report a need.
  - **Request Body**:
    ```json
    {
      "type": "medicine",
      "urgency": "critical",
      "quantity": 300,
      "unit": "packets",
      "description": "Urgent IV fluids and anti-venom at flooded relief camp",
      "latitude": 24.8333,
      "longitude": 92.7789,
      "district": 1
    }
    ```
- **`GET /api/needs/{id}/`**: Need detail with attached photos/videos.
- **`POST /api/needs/{id}/attachments/`**: Multipart upload for field photo or video.

### 3.3 Resources
- **`GET /api/resources/`**: List available supplies (filterable by `?type=medicine&available_only=true&verification_status=verified_org`).
- **`POST /api/resources/`**: Register supplies.
  - **Request Body**:
    ```json
    {
      "type": "medicine",
      "quantity_available": 1200,
      "unit": "packets",
      "verification_status": "verified_org",
      "latitude": 24.8400,
      "longitude": 92.7850,
      "district": 1
    }
    ```
- **`GET /api/resources/{id}/`**: Resource detail.

### 3.4 Conditions & Hazard Monitoring
- **`GET /api/conditions/`**: List condition reports (filterable by `?district=1&condition_type=road_status`).
- **`POST /api/conditions/`**: Report road obstruction, heavy rainfall, or landslide risk.
  - **Request Body**:
    ```json
    {
      "condition_type": "road_status",
      "value": "blocked",
      "latitude": 25.1800,
      "longitude": 93.0100,
      "district": 4,
      "source": "field_report"
    }
    ```
- **`POST /api/conditions/{id}/attachments/`**: Attach photo/video evidence.
- **`GET /api/conditions/predict-risk/?lat=24.83&lon=92.78&rainfall=110&slope=32`**:
  - Invokes AI Disruption Risk Classifier.
  - **Response (`200 OK`)**:
    ```json
    {
      "latitude": 24.83,
      "longitude": 92.78,
      "risk_score": 0.8842,
      "risk_level": "critical",
      "is_critical": true,
      "explanation": "Elevated disruption risk due to: Heavy rainfall (110.0 mm), Steep incline (32.0° slope), High soil water saturation.",
      "features": {
        "rainfall_mm": 110.0,
        "slope_degrees": 32.0,
        "elevation_m": 650.0,
        "soil_saturation": 0.85,
        "drainage_quality": 2.5,
        "vegetation_cover": 0.55
      }
    }
    ```

---

## 4. Matching Engine & Allocation

### 4.1 Trigger Matching Engine
- **Endpoint**: `GET /api/needs/{id}/matches/`
- **Action**: Discovers candidate supplies with matching type, evaluates distance decay, verification status, quantity fit, and hazard risk, computes weighted composite scores, saves Match records, and returns ranked results.
- **Response (`200 OK`)**:
```json
{
  "need_id": 1,
  "need_type": "medicine",
  "urgency": "critical",
  "quantity_required": 300,
  "total_candidates_evaluated": 2,
  "matches": [
    {
      "id": 1,
      "need": 1,
      "resource": 1,
      "score": 0.9425,
      "score_breakdown": {
        "urgency": 1.0,
        "proximity": 0.9782,
        "verification": 1.0,
        "quantity_fit": 1.0,
        "delay_risk": 0.82,
        "distance_km": 0.98
      },
      "status": "proposed",
      "created_at": "2026-08-23T06:33:00Z"
    }
  ]
}
```

### 4.2 Confirm Match & Allocate Resource
- **Endpoint**: `POST /api/matches/{id}/confirm/`
- **Request Body**:
```json
{
  "vehicle_id": 1
}
```
- **Response (`200 OK`)**:
```json
{
  "message": "Match confirmed and resource allocated successfully.",
  "allocation": {
    "id": 1,
    "match": 1,
    "match_score": 0.9425,
    "need_type": "medicine",
    "need_quantity": 300,
    "need_unit": "packets",
    "resource_provider": "redcross_assam",
    "vehicle": 1,
    "vehicle_registration": "AS-11-BC-4401",
    "vehicle_type": "5-Ton 4x4 Heavy Relief Truck",
    "delivery_status": "dispatched",
    "route_geojson": {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[92.785, 24.84], [92.78, 24.835], [92.775, 24.83]]
      },
      "properties": {
        "distance_km": 1.45,
        "estimated_duration_minutes": 3,
        "status": "active"
      }
    },
    "estimated_delay_minutes": 0,
    "assigned_at": "2026-08-23T06:33:05Z"
  }
}
```

---

## 5. Logistics & Fleet Tracking

### 5.1 Fleet Directory
- **`GET /api/vehicles/`**: List all registered vehicles and operators.
- **`POST /api/vehicles/`**: Register new transport vehicle.

### 5.2 Live GPS Ping
- **`POST /api/vehicles/{id}/ping/`**:
- **Request Body**:
```json
{
  "latitude": 24.8340,
  "longitude": 92.7795,
  "status": "en_route"
}
```
- **Response (`200 OK`)**: Updates `current_location` and `last_ping_at`.

---

## 6. Command Dashboard Analytics

### 6.1 District Summary & Bottlenecks
- **Endpoint**: `GET /api/dashboard/district-summary/`
- **Response (`200 OK`)**:
```json
{
  "overview": {
    "total_districts_monitored": 5,
    "total_open_needs": 1,
    "total_critical_needs": 1,
    "total_fulfilled_needs": 0,
    "total_available_resources": 4,
    "total_blocked_corridors": 1,
    "total_critical_alerts": 2,
    "system_health_status": "normal_operations"
  },
  "districts": [
    {
      "district_id": 4,
      "name": "Dima Hasao",
      "state": "Assam",
      "population": 214102,
      "needs": {
        "total": 1,
        "open": 1,
        "critical": 0,
        "fulfilled": 0
      },
      "resources": {
        "available_count": 0,
        "verified_org_count": 0
      },
      "hazards": {
        "blocked_roads_count": 1,
        "high_risk_conditions_count": 0,
        "active_alerts_count": 1
      },
      "bottleneck_index": 3.5,
      "connectivity_status": "moderate_stress"
    }
  ]
}
```
