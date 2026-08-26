# SETU Platform: Database Management & Authentication Security Architecture

This document provides a comprehensive technical breakdown of how data is stored, structured, and managed across the SETU backend, and how authentication, authorization, and network security are enforced across all APIs.

---

## 1. Database Architecture & Management

### 1.1 Dual-Engine Strategy (PostgreSQL + PostGIS with Transparent SQLite3 Fallback)
The SETU backend implements a zero-downtime, resilient database connection strategy configured in [`backend/config/settings.py`](file:///e:/SETU/SETU/backend/config/settings.py):

```
                       ┌──────────────────────────────────────┐
                       │       Application Startup            │
                       └──────────────────┬───────────────────┘
                                          │
                        Is DATABASE_URL or DB_NAME configured?
                                         / \
                                   YES  /   \  NO
                                       /     \
                ┌─────────────────────▼─┐   ┌─▼──────────────────────┐
                │ Test PostgreSQL Ping  │   │ Use local db.sqlite3   │
                └──────────┬────────────┘   └────────────────────────┘
                          / \
                  ALIVE  /   \  OFFLINE / ERROR
                        /     \
    ┌──────────────────▼─┐   ┌─▼──────────────────────┐
    │ Connect PostgreSQL │   │ Graceful Fallback to   │
    │  (or PostGIS)      │   │ local db.sqlite3       │
    └────────────────────┘   └────────────────────────┘
```

1. **Production Engine (PostgreSQL 15+ / PostGIS)**:
   - Primary database used for multi-node deployments, concurrent read/write workloads, and high-precision geospatial operations.
   - Supported via `psycopg2-binary` and GeoDjango GIS adapter (`django.contrib.gis.db.backends.postgis`).
   - Auto-detected when valid credentials exist and live connectivity check `_is_postgres_available(...)` passes.
2. **Development / Offline Engine (SQLite 3.x)**:
   - Zero-dependency local file database (`backend/db.sqlite3`).
   - Automatically activates if PostgreSQL is unreachable or when `USE_SQLITE=True` is defined in `.env`.
   - Maintains full schema compatibility with PostgreSQL migrations.

---

### 1.2 Database Schema & Domain Models

The database models are separated into modular Django applications:

```
                          ┌────────────────────────┐
                          │   accounts.User        │
                          │ (Custom Auth & RBAC)   │
                          └───────────┬────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌──────────────────┐        ┌───────────────────┐        ┌──────────────────┐
│   core Models    │        │ logistics Models  │        │ matching Models  │
├──────────────────┤        ├───────────────────┤        ├──────────────────┤
│ - District       │◄───────┤ - Stockpile       │◄───────┤ - MatchProposal  │
│ - Disaster       │        │ - StockpileItem   │        │ - AllocationItem │
│ - HazardAlert    │        │ - TransportVehicle│        │ - RouteLeg       │
│ - Infrastructure │        │ - TelemetryPing   │        │ - Notification   │
│ - Institution    │        │ - ReliefNeed      │        │                  │
└──────────────────┘        │ - NeedItem        │        └──────────────────┘
                            │ - NeedAttachment  │
                            └───────────────────┘
```

#### Core Data Entities:
- **`accounts.User`**: Custom user model extending `AbstractUser`. Stores `role` (`admin`, `district_admin`, `field_officer`, `transport_operator`, `ngo`, `citizen`), `phone_number`, `district` FK, `is_verified` badge, `preferred_language` (`en`, `as`, `bn`, `hi`), and timestamps.
- **`core.District` & `core.Disaster`**: Jurisdictional boundary mapping with population statistics, active disaster events, severity levels, and casualty tracking.
- **`core.HazardAlert` & `core.InfrastructureStatus`**: Real-time road blockages, bridge collapses, flood inundation zones, helipad accessibility, and hospital emergency capacities.
- **`logistics.ReliefNeed` & `logistics.NeedItem`**: Citizen/depot distress requests categorized by supply type (food, drinking water, medicine, shelter kits), urgency score (1-5), GPS geolocation, and fulfillment status.
- **`logistics.Stockpile` & `logistics.StockpileItem`**: Verified warehouse relief inventory with expiration dates, quantities, and depot manager associations.
- **`logistics.TransportVehicle` & `logistics.VehicleTelemetryPing`**: Fleet asset records (trucks, boats, helicopters, 4x4s), payload capacity (kg), operational status, and real-time GPS telemetry audit logs.
- **`matching.MatchProposal` & `matching.MatchNeedItemAllocation`**: AI matching engine dispatch recommendations coupling high-urgency demands to optimal stockpiles and transport routes.

---

### 1.3 Migrations & Schema Maintenance
- All database state transitions are managed declaratively through Django migrations.
- To apply migrations cleanly:
  ```powershell
  python manage.py migrate --run-syncdb
  ```
- **SQLite Schema Auto-Repair Tool ([`fix_sqlite_schema.py`](file:///e:/SETU/SETU/backend/fix_sqlite_schema.py))**: Handles schema divergence or missing columns when migrating between SQLite snapshots.

---

## 2. Authentication & Authorization Security

SETU implements a multi-tier defense-in-depth security model designed specifically for disaster management operations where integrity, privacy, and prevention of privilege escalation are paramount.

```
Incoming Request
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Network / Transport Layer                            │
│    - CORS Whitelist (Origin checking)                   │
│    - Security Headers (X-Frame-Options, No-Sniff, HSTS) │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Authentication Layer                                 │
│    - JWT Bearer Token validation (SimpleJWT)            │
│    - Token Expiration & Cryptographic Signature check   │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Broken Access Control / RBAC Layer                   │
│    - Role Hierarchy Validation (Admin / Officer / NGO)  │
│    - Endpoint Permissions (IsDistrictAdmin, etc.)       │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Broken Object-Level Authorization (BOLA) Layer       │
│    - Object ownership verification                      │
│    - (reported_by == user / operator == user)           │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Input Sanitization & File Whitelist                  │
│    - Serializer field validation & MIME-type checks     │
│    - 10MB upload limit                                  │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
                       Controller / DB Execution
```

---

### 2.1 JSON Web Token (JWT) Authentication
- Handled by `djangorestframework-simplejwt` with `Bearer` scheme.
- Configured in `settings.py`:
  - **Access Token Lifetime**: 60 minutes (configurable via `JWT_ACCESS_TOKEN_LIFETIME_MIN`).
  - **Refresh Token Lifetime**: 7 days.
  - **Token Rotation**: `ROTATE_REFRESH_TOKENS = True` (new refresh token issued on every refresh to prevent replay attacks).
- **Embedded Token Claims**:
  Tokens contain standard JWT claims plus custom application claims:
  ```json
  {
    "token_type": "access",
    "exp": 1787671097,
    "jti": "d6a2f8b...",
    "user_id": 4,
    "username": "dist_admin_guwahati",
    "role": "district_admin",
    "district_id": 1,
    "is_verified": true
  }
  ```

---

### 2.2 Role-Based Access Control (RBAC) & Hierarchy

| Role | Access Scope & Allowed Actions |
| :--- | :--- |
| **`admin` / `district_admin`** | Full command center authority; create officers/operators; verify NGOs; confirm dispatch matches; edit infrastructure statuses. |
| **`field_officer`** | Report and update road blockages, bridge collapses, flood hazard alerts, and ground distress assessments. |
| **`ngo`** | Register and manage depot stockpile inventories, relief supplies, and accept matched delivery dispatches once verified. |
| **`transport_operator`** | Register fleet vehicles, submit GPS telemetry coordinates, and update delivery convoy transit milestones. |
| **`citizen`** | Submit emergency relief distress needs, attach photo evidence, view public disaster maps and official alerts. |

---

### 2.3 Broken Access Control (BAC) & Mass Assignment Mitigation (SEC-001)
- **Vulnerability Prevented**: Unauthenticated or low-privilege users attempting to register as `admin`, `district_admin`, or `field_officer` by injecting `"role": "admin"` into registration payloads.
- **Enforcement**:
  1. [`UserRegisterSerializer`](file:///e:/SETU/SETU/backend/accounts/serializers.py) restricts public self-registration strictly to `citizen` and `ngo` roles. Any attempted injection of `admin`, `district_admin`, `field_officer`, or `transport_operator` is rejected with `HTTP 400 Bad Request`.
  2. Elevated accounts can only be provisioned through the dedicated, admin-protected endpoint:
     `POST /api/auth/admin/create-user/` guarded by `IsDistrictAdmin`.

---

### 2.4 Broken Object-Level Authorization (BOLA) Protection
- Custom permission classes in [`backend/accounts/permissions.py`](file:///e:/SETU/SETU/backend/accounts/permissions.py):
  - **`IsOwnerOrAdmin`**: Prevents User A from modifying or deleting distress needs or stockpiles submitted by User B.
  - **`IsAssignedOperatorOrAdmin`**: Strictly restricts vehicle telemetry ping submissions and operational status changes to the specific assigned driver or an Administrator.
  - **`IsVerifiedProviderOrReadOnly`**: Disallows unverified NGO accounts from listing relief goods in the operational matching pool until officially vetted.

---

### 2.5 Broken Function Level Authorization (BFLA) Protection (SEC-004)
- Critical disaster management functions (such as `/api/matches/<id>/confirm/` to dispatch relief inventory and deploy government transport) are guarded with `IsDistrictAdminOrNodalAgency`.
- Citizens and general operators are blocked (`HTTP 403 Forbidden`).

---

### 2.6 File Upload & Payload Security (SEC-005)
- **Extension Whitelist**: Only safe static extensions (`.jpg`, `.jpeg`, `.png`, `.pdf`, `.webp`) are accepted. Executables (`.exe`, `.sh`, `.py`, `.html`, `.svg`) are rejected to prevent Remote Code Execution and Stored XSS.
- **File Size Cap**: Strict 10MB limit enforced on all incoming attachments to prevent Denial of Service (DoS) memory exhaustion.

---

### 2.7 Transport & Network Security Headers (SEC-007 / SEC-008 / SEC-009)
Configured in `settings.py` and `SecurityMiddleware`:
- `X_FRAME_OPTIONS = 'DENY'` (Mitigates Clickjacking attacks).
- `SECURE_CONTENT_TYPE_NOSNIFF = True` (Prevents MIME-sniffing exploits).
- `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'` (Protects sensitive URLs).
- `CORS_ALLOW_ALL_ORIGINS = False` (Strict whitelist of trusted frontend development and production origins).
- `SESSION_COOKIE_HTTPONLY = True` and `CSRF_COOKIE_HTTPONLY = True` (Protects session identifiers from client-side script access).
- When `DEBUG=False` (Production mode):
  - `SECURE_SSL_REDIRECT = True`
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SECURE_HSTS_SECONDS = 31536000` (1 Year Strict Transport Security)

---

## 3. Verification & Security Audit Commands

To verify database integrity and execute automated security tests:

1. **Validate Django System & Database Configuration**:
   ```powershell
   python manage.py check
   ```

2. **Run Automated Security Audit Test Suite**:
   ```powershell
   python security_audit_test.py
   ```
   *Validates SEC-001 (privilege escalation), SEC-004 (BFLA match confirmation), SEC-005 (file upload restrictions), and SEC-009 (HTTP security headers).*
