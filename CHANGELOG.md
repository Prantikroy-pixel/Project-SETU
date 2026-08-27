# SETU Changelog

## [2026-08-27] - Vercel Cloud Deployment, Complete DRF Test Suite & Advanced Risk Visualization

### Overview
Configured Vercel multi-service deployment for Django backend and Vite frontend SPA, engineered comprehensive automated unit test suites for all DRF backend modules (`accounts`, `core`, `logistics`, `matching`) and ML risk model engines, refined object-level RBAC security permissions, and expanded interactive geospatial hazard corridor overlays.

### Detailed Changes

#### 1. Vercel Multi-Service Cloud Deployment (`vercel.json`)
- **Multi-Service Declarations**: Configured Vercel configuration for simultaneous serverless orchestration of Vite React Frontend SPA and Django WSGI Backend Service.
- **Service Entrypoints**:
  - `frontend`: Vite framework single-page application setup (`root: "frontend"`).
  - `backend`: Django WSGI entrypoint (`root: "backend"`, `entrypoint: "config.wsgi:application"`).
- **API Proxy & Route Rewrites**: Configured transparent URL rewriting, routing all `/api/*` endpoints to the Django backend service and remaining routes (`/*`) to the React frontend application.

#### 2. DRF & ML Risk Engine Automated Test Suites (`backend/*/tests.py` & `matching_engine/tests/`)
- **Accounts Authentication Suite (`backend/accounts/tests.py`)**:
  - `test_user_registration`: Verified public citizen/NGO registration (`POST /api/auth/register/`) returning JWT token pairs (`access`, `refresh`) and proper role/district binding.
  - `test_user_login_jwt`: Validated JWT token retrieval (`POST /api/auth/login/`) for administrative users.
  - `test_me_endpoint_authenticated`: Confirmed authenticated user identity retrieval (`GET /api/auth/me/`).
- **Core Spatial & Security Suite (`backend/core/tests.py`)**:
  - `test_district_unauthenticated_http_methods_security`: Enforced `401 Unauthorized` for anonymous write attempts (`POST`, `PUT`, `PATCH`, `DELETE`) on `/api/districts/{id}/`, preserving public `200 OK` read access for emergency coordination.
  - `test_district_non_admin_forbidden`: Verified `403 Forbidden` response when non-admin authenticated roles (e.g. `citizen`) attempt administrative modifications.
  - `test_district_admin_authorized`: Confirmed successful `200 OK` updates when `district_admin` users execute authorized changes.
- **Logistics & Fleet Telemetry Suite (`backend/logistics/tests.py`)**:
  - `test_vehicle_list`: Verified public/authenticated fleet vehicle registry access (`GET /api/vehicles/`).
  - `test_vehicle_gps_ping`: Tested live GPS ping telemetry updates (`POST /api/vehicles/{id}/ping/`) for transport operators, verifying real-time status transitions and timestamping.
- **Matching Engine & Risk Model Suite (`backend/matching/tests.py` & `matching_engine/tests/test_risk_model.py`)**:
  - Validated demand-supply matching engine algorithms and match confirmation workflows (`POST /api/matches/{id}/confirm/`).
  - Tested flood risk ML predictor scoring routines, edge-case hazard factor calculations, and output bounds.

#### 3. Granular Object-Level RBAC Permissions (`backend/accounts/permissions.py`)
- **`IsAdminUserOrReadOnly`**: Added `has_object_permission` override enforcing that object-level modification operations (`PUT`, `PATCH`, `DELETE`) are restricted strictly to authenticated superusers, `district_admin` users, or staff accounts.
- **`IsDistrictAdmin`**: Added object-level authorization checks ensuring administrative domain isolation across relief resources, stockpiles, and district metadata.

#### 4. Geospatial Risk Corridor & Field Officer Portal (`frontend/src/components/RiskCorridorMapLayer.jsx` & `FieldOfficerPortal.jsx`)
- **Interactive Risk Corridor GIS Overlay**: Developed dynamic Leaflet polygon visualization rendering real-time flood risk corridors with color-graded risk severity indices and warning popups.
- **Field Officer Portal Upgrades**: Enhanced rapid condition reporting, live geolocation ping integration, and attachment handling for field operations.

---

## [2026-08-25] - Security Remediation Audit, Full Backend DRF Integration & Admin Credentials Verification

### Overview
Executed the automated security audit test suite (`security_audit_test.py`) to verify all backend security patches (SEC-001, SEC-004, SEC-005, SEC-007, SEC-008, SEC-009), verified complete DRF REST backend integration with the Vite React frontend SPA, and updated/seeded active admin credentials.

### Detailed Changes

#### 1. Security Patches & Compliance Matrix Verification (`backend/security_audit_test.py`)
- **SEC-001 (Privilege Escalation via Registration Mass Assignment)**: `[PASS]` Public registration to `/api/auth/register/` strictly permits `citizen` and `ngo` roles. Administrative, Field Officer, and Transport Operator roles are blocked with `400 Bad Request`.
- **SEC-004 (Broken Function Level Authorization)**: `[PASS]` Unauthenticated and citizen match confirmation requests to `/api/matches/<id>/confirm/` are rejected with `401 Unauthorized` / `403 Forbidden`.
- **SEC-005 (Unrestricted File Upload Whitelist & Size Limit)**: `[PASS]` Malicious script uploads (`.html`, `.py`, `.svg`, `.sh`) and oversized files (>10MB) to `/api/needs/<id>/attachments/` and `/api/conditions/<id>/attachments/` are blocked with `403 Forbidden`.
- **SEC-007 / SEC-008 / SEC-009 (HTTP Security Response Headers & CORS)**: `[PASS]` HTTP response headers validated (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`). CORS wildcard origin removed.

#### 2. Backend DRF Endpoint Integration & Verification (`backend/verify_endpoints.py`)
- **District Command Summary & Analytics**: `GET /api/dashboard/district-summary/` (Aggregated ORM query returning bottleneck indices and district status).
- **Relief Needs & Match Engine**: `GET /api/needs/`, `POST /api/needs/`, `GET /api/needs/<id>/matches/`, `POST /api/matches/<id>/confirm/`.
- **Stockpiles & Logistics**: `GET /api/resources/`, `POST /api/resources/`, `GET /api/vehicles/`, `POST /api/vehicles/<id>/ping/`.
- **Boundaries & Institutions**: `GET /api/institutions/`, `GET /api/boundaries/ner-borders/`, `GET /api/boundaries/check-proximity/`, `POST /api/boundaries/analyze-route/`.

#### 3. Active System Admin Credentials (`backend/db.sqlite3`)
- **Central Superuser Administrator**:
  - **Username**: `admin_setu`
  - **Password**: `Password123!`
  - **Role**: `Admin` (`admin` / `is_superuser=True`)
- **District Command Administrator**:
  - **Username**: `admin_aryan`
  - **Password**: `Password123!`
  - **Role**: `District Admin` (`district_admin` / `is_staff=True`)
- **Field Officer Account**:
  - **Username**: `officer_ananda`
  - **Password**: `Password123!`
  - **Role**: `Field Officer` (`field_officer`)
- **Transport Operator Account**:
  - **Username**: `operator_rajesh`
  - **Password**: `Password123!`
  - **Role**: `Transport Operator` (`transport_operator`)
- **Relief NGO Account**:
  - **Username**: `redcross_assam`
  - **Password**: `Password123!`
  - **Role**: `NGO` (`ngo`)
- **Citizen Account**:
  - **Username**: `citizen_priya` / `citizen_test_user_2`
  - **Password**: `Password123!` / `CitizenPassword123!`
  - **Role**: `Citizen` (`citizen`)

---

## [2026-08-25] - Admin Dashboard Navigation, Sleek UI Redesign & AI Matcher Priority System

### Overview
Restored the clean light navbar design, introduced a top sub-navbar with complete operational tab views for District Command Administrators (`Overview`, `NGOs`, `Transporters`, `Fleet Vehicles`, `Field Officers`, `Govt Stockpiles`), fixed role switching in `AuthContext`, implemented custom premium popover dropdown menus, and categorized the AI Demand-Supply Matcher queue with priority ordering and distinct color-coded badges.

### Detailed Changes

#### 1. District Administrator Sub-Navbar & Operational Views (`frontend/src/pages/DistrictDashboard.jsx`)
- **Top Sub-Navbar**: Added a top horizontal segmented controller sub-navbar allowing administrators to switch between:
  - **Command Overview**: Stat cards, Leaflet GIS Map, AI Demand-Supply Matcher, Stress Index, Live Operational Log, and Border Corridor Geofence Analyzer.
  - **Registered NGOs**: Organization roster & verification queue with Approve / Revoke approval controls.
  - **Transporters**: Transporter roster + inline **Add Transporter** account provisioning form.
  - **Fleet Vehicles**: Vehicle registry + inline **Add Vehicle** form for Admin direct fleet additions.
  - **Field Officers**: Field Officer directory + inline **Add Field Officer** form & clearance management.
  - **Govt Stockpiles**: Government emergency stockpile inventory registry (Relief Category, Quantity, Unit, District, Warehouse Location).
- **De-duplication**: Removed duplicate RBAC management section from the bottom of the overview page.

#### 2. Priority Categorization & Color-Coding for AI Demand Matcher (`frontend/src/pages/DistrictDashboard.jsx`)
- **Urgency Priority Queue Sorting**: Automatically sorts all open relief demands in strict priority sequence:
  - `Critical / Urgent SOS` → `High Priority` → `Medium Priority` → `Low Priority`.
- **Color-Coded Priority Badges**:
  - 🔴 **Critical / Urgent SOS**: Red styling (`bg-red-50 text-red-800 border-red-300`) with an animated pulsing `[CRITICAL]` tag.
  - 🟠 **High Priority**: Amber styling (`bg-amber-50 text-amber-900 border-amber-300`) with `[HIGH]` tag.
  - 🔵 **Medium Priority**: Blue styling (`bg-blue-50 text-blue-800 border-blue-200`) with `[MED]` tag.
  - ⚪ **Low Priority**: Slate styling (`bg-slate-100 text-slate-700 border-slate-200`) with `[LOW]` tag.
- **Priority Legend Bar**: Added a color-coded priority legend strip directly above the queue.

#### 3. Role Switching Fix & Custom Premium Dropdown Menus (`frontend/src/context/AuthContext.jsx` & `frontend/src/components/Navbar.jsx`)
- **`AuthContext.jsx`**: Added `switchRole(newRole)` implementation to update `user.role` in React state and persist to `localStorage`.
- **`Navbar.jsx`**:
  - Replaced native browser `<select>` controls with custom interactive popover dropdown menus for **Role Switching** and **Language Selection**.
  - Popovers feature backdrop blur (`backdrop-blur-md`), checkmark indicators, click-outside auto-closing, and automatic navigation to target role portals (`/dashboard`, `/officer`, `/ngo`, `/operator`, `/citizen`).

#### 4. Ultra-Sleek & Premium UI Layout (`frontend/src/components/Navbar.jsx`, `frontend/src/pages/DistrictDashboard.jsx`, `frontend/src/App.jsx`)
- **Navbar Header**: Sleek glassmorphic header (`bg-white/90 backdrop-blur-md border-b border-slate-200/80 h-14`) with dark slate logo badge.
- **App Layout Padding**: Adjusted `<main>` top padding in `App.jsx` (`pt-6`) for tight, seamless alignment below the single sticky navbar.
- **Compact Geometry**: Reduced card heights, padded slate containers, and crisp label typography (`text-[11px] font-bold uppercase tracking-wider text-slate-500`).

#### 5. Production Build Verification
- **Status**: PASSED (`npm run build` completed in 8.38s)
- **Bundle Output**:
  - `dist/index.html` (1.26 kB)
  - `dist/assets/index-DnfQfExf.css` (32.16 kB)
  - `dist/assets/index-CNXp2TSh.js` (527.29 kB)
