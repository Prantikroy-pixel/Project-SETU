"""
Script to generate a comprehensive, publication-quality PDF audit report
for the SETU Backend and Matching Engine codebase.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that enables multi-pass 'Page X of Y' numbering and running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header on pages after the cover / first page
        if self._pageNumber > 1:
            self.drawString(45, 750, "SETU (Problem Statement 26002) — Backend Codebase Audit & Shortcomings Report")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(45, 742, 567, 742)

        # Footer on all pages
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(567, 30, page_text)
        self.drawString(45, 30, "SETU Technical Audit | MDoNER Problem Statement 26002")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(45, 42, 567, 42)
        self.restoreState()


def build_pdf(filename="SETU_Backend_Shortcomings_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1e293b")   # Slate 800
    accent_color = colors.HexColor("#0284c7")    # Sky 600
    danger_color = colors.HexColor("#b91c1c")    # Red 700
    warning_color = colors.HexColor("#b45309")   # Amber 700
    text_dark = colors.HexColor("#0f172a")       # Slate 900
    text_muted = colors.HexColor("#475569")      # Slate 600

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=accent_color,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=text_dark,
        spaceAfter=4,
    )

    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold',
    )

    meta_style = ParagraphStyle(
        'Meta_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=text_muted,
    )

    tbl_header = ParagraphStyle(
        'TblHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    tbl_cell = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=text_dark,
    )

    tbl_cell_bold = ParagraphStyle(
        'TblCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=text_dark,
    )

    tbl_cell_danger = ParagraphStyle(
        'TblCellDanger',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=danger_color,
    )

    file_title_style = ParagraphStyle(
        'FileTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=primary_color,
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("SETU Platform — Backend Codebase Audit & Shortcomings Report", title_style))
    story.append(Paragraph("Technical Gap Analysis, Requirement Reconciliation (PS 26002), & File-by-File Defect Log", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=8, spaceBefore=0))

    meta_text = """
    <b>Platform:</b> SETU (Socio-Economic Transport & Utility Engine) &nbsp;|&nbsp; 
    <b>Problem Statement:</b> SIH 26002 (MDoNER) &nbsp;|&nbsp; 
    <b>Tech Stack:</b> Django 5.1, DRF, PostGIS / Spatial Compat, Scikit-Learn Risk Model &nbsp;|&nbsp; 
    <b>Scope:</b> Backend & Matching Engine Codebase
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Assessment Overview", h1_style))
    exec_summary_text = (
        "This audit report presents a rigorous examination of all backend services, spatial layers, API endpoints, "
        "and machine learning modules comprising the <b>SETU</b> platform. While the repository provides a solid architectural "
        "foundation that addresses the functional breadth of <b>SIH Problem Statement 26002</b> (MDoNER), critical gaps and "
        "shortcomings exist between the stated specifications in <code>description.md</code> and the live Python implementation. "
        "Key vulnerabilities include <b>disabled authorization on ViewSets</b> (<code>AllowAny</code>), a <b>critical resource "
        "inventory non-decrement bug</b> leading to phantom supply over-allocation, <b>synthetic straight-line routing</b> substituting "
        "for actual OSRM server computation, <b>N+1 SQL query bottlenecks</b> in command dashboard analytics (1,300+ queries per request), "
        "and the <b>absence of real-time SMS/Push gateway dispatchers</b>."
    )
    story.append(Paragraph(exec_summary_text, body_style))
    story.append(Spacer(1, 8))

    # Section 2: Problem Statement 26002 Requirement Tally Table
    story.append(Paragraph("2. Problem Statement 26002 Requirement-by-Requirement Tally", h1_style))
    tally_intro = (
        "Comparison of mandated requirements from the Ministry of Development of North Eastern Region (MDoNER) "
        "checklist (Items a–h) against the active backend implementation:"
    )
    story.append(Paragraph(tally_intro, body_style))
    story.append(Spacer(1, 6))

    tally_data = [
        [
            Paragraph("PS 26002 Requirement", tbl_header),
            Paragraph("Description Specification", tbl_header),
            Paragraph("Backend Implementation", tbl_header),
            Paragraph("Identified Shortcomings & Gaps", tbl_header),
            Paragraph("Status", tbl_header)
        ],
        [
            Paragraph("<b>(a) Road / Bridge Accessibility</b>", tbl_cell_bold),
            Paragraph("Condition entity logging road status (blocked, flooded, landslide), GPS, district.", tbl_cell),
            Paragraph("<code>core/models.py</code><br/><code>core/views.py</code>", tbl_cell),
            Paragraph("Unauthenticated users can post fake road closures (AllowAny). No external automated sensor ingestion.", tbl_cell),
            Paragraph("<font color='#b45309'><b>Partial</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(b) Disruption Prediction (AI/ML)</b>", tbl_cell_bold),
            Paragraph("Gradient Boosting Classifier evaluating slope, rain, soil, elevation, drainage.", tbl_cell),
            Paragraph("<code>matching_engine/risk_model/predict.py</code>", tbl_cell),
            Paragraph("Evaluates single coordinate point rather than road corridor polyline. Uses synthetic data and heuristic fallbacks for missing GIS layers.", tbl_cell),
            Paragraph("<font color='#b45309'><b>Partial</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(c) Alternate Routes & Delays</b>", tbl_cell_bold),
            Paragraph("OSRM route GeoJSON generation; dynamic delay penalty; +45 min cascade.", tbl_cell),
            Paragraph("<code>core/services.py</code><br/><code>matching/services.py</code>", tbl_cell),
            Paragraph("<b>No actual OSRM integration</b>: generates synthetic 3-point straight line with arbitrary offset. Delay is hardcoded to static +45 min.", tbl_cell_danger),
            Paragraph("<font color='#b91c1c'><b>Deficient</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(d) GPS Fleet Tracking</b>", tbl_cell_bold),
            Paragraph("Vehicle tracking live GPS pings (/api/vehicles/{id}/ping/), status, and missions.", tbl_cell),
            Paragraph("<code>logistics/models.py</code><br/><code>logistics/views.py</code>", tbl_cell),
            Paragraph("<b>No telemetry history log</b>: overwrites current_location. No speed, heading, or breadcrumbs. Ping endpoint lacks operator auth check.", tbl_cell),
            Paragraph("<font color='#b45309'><b>Partial</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(e) Automated Hazard Alerts</b>", tbl_cell_bold),
            Paragraph("Alert cascading engine broadcasting across SMS, Push, and In-App channels.", tbl_cell),
            Paragraph("<code>core/services.py</code> (trigger_condition_alerts)", tbl_cell),
            Paragraph("<b>No SMS/Push gateway integration</b>: only creates passive DB rows. No WebSockets for live push to dashboards.", tbl_cell_danger),
            Paragraph("<font color='#b45309'><b>Partial</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(f) Geo-Tagged Photo Uploads</b>", tbl_cell_bold),
            Paragraph("MediaAttachment entity for multipart photo/video evidence linked to Needs/Conditions.", tbl_cell),
            Paragraph("<code>core/models.py</code><br/><code>core/views.py</code>", tbl_cell),
            Paragraph("No file MIME/extension validation (security risk), no upload file size limit. Static media Docker routing path mismatch.", tbl_cell),
            Paragraph("<font color='#15803d'><b>Substantial</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(g) District Command Dashboard</b>", tbl_cell_bold),
            Paragraph("District Bottleneck Index analytics endpoint (/api/dashboard/district-summary/).", tbl_cell),
            Paragraph("<code>dashboard/views.py</code>", tbl_cell),
            Paragraph("<b>N+1 SQL query explosion</b>: runs 11 SQL queries per district in a Python loop (1,320+ queries across 120 NER districts).", tbl_cell_danger),
            Paragraph("<font color='#b45309'><b>Slow</b></font>", tbl_cell)
        ],
        [
            Paragraph("<b>(h) Multilingual & Low-Net Sync</b>", tbl_cell_bold),
            Paragraph("User language preferences (en, as, bn, hi), localized alert payloads, offline sync.", tbl_cell),
            Paragraph("<code>accounts/models.py</code><br/><code>core/models.py</code>", tbl_cell),
            Paragraph("<b>Alert messages are hardcoded in English</b>; no translation engine. No client UUID idempotency keys for offline retry handling.", tbl_cell_danger),
            Paragraph("<font color='#b91c1c'><b>Deficient</b></font>", tbl_cell)
        ],
    ]

    tally_table = Table(tally_data, colWidths=[95, 110, 100, 162, 55])
    tally_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tally_table)
    story.append(Spacer(1, 12))

    story.append(PageBreak())

    # Section 3: File-by-File Audit and Technical Problems Log
    story.append(Paragraph("3. Exhaustive File-by-File Audit & Defect Log", h1_style))
    story.append(Paragraph("Detailed analysis of every source file in the backend and matching engine:", body_style))
    story.append(Spacer(1, 6))

    files_audit = [
        {
            "category": "Authentication & Authorization (backend/accounts/)",
            "files": [
                (
                    "backend/accounts/permissions.py",
                    "Defines role-based permission classes (IsFieldOfficerOrAdmin, IsTransportOperatorOrAdmin, IsDistrictAdmin, IsVerifiedProvider).",
                    [
                        "Shortcoming: Permission classes are fully defined but completely bypassed across the entire codebase because ViewSets override them with AllowAny.",
                        "Shortcoming: Missing object-level permission hooks (e.g. ensuring a driver can only modify their assigned vehicle, or an NGO can only edit their own resources)."
                    ]
                ),
                (
                    "backend/accounts/views.py",
                    "Provides endpoints for user registration, JWT login (CustomTokenObtainPairView), profile inspection (MeView), and user directory listing.",
                    [
                        "Shortcoming: RegisterView allows unrestricted role self-assignment — any caller can register themselves as 'district_admin' or 'admin' and automatically obtain is_staff privileges.",
                        "Shortcoming: UserListView allows any authenticated user to view the full user directory, exposing phone numbers and assigned districts."
                    ]
                ),
                (
                    "backend/accounts/serializers.py",
                    "Handles user serialization, registration validation, and JWT token payload augmentation.",
                    [
                        "Shortcoming: Missing phone number format validation (E.164 regex) and district existence/state consistency checks."
                    ]
                ),
            ]
        },
        {
            "category": "Core Disaster & Resource Domain (backend/core/)",
            "files": [
                (
                    "backend/core/views.py",
                    "Exposes CRUD endpoints for Districts, Needs, Resources, Conditions, Allocations, Alerts, and AI Risk Prediction.",
                    [
                        "Critical Vulnerability: All ViewSets (NeedViewSet, ResourceViewSet, ConditionViewSet, AllocationViewSet, AlertViewSet) set permission_classes = [AllowAny]. Any unauthenticated caller can alter relief records or post fake emergency conditions.",
                        "Crash Bug: In NeedViewSet, ResourceViewSet, and ConditionViewSet, unauthenticated creation triggers an unhandled IntegrityError (NOT NULL constraint failed on reported_by / provider) causing 500 Internal Server Errors.",
                        "Security Deficit: upload_attachment actions accept any file without validating MIME type/extension or enforcing maximum file size limits (DoS vector).",
                        "Security Deficit: AllocationViewSet allows any user to transition allocations to 'delivered', prematurely marking open relief needs as 'fulfilled'."
                    ]
                ),
                (
                    "backend/core/services.py",
                    "Contains trigger_condition_alerts() for event-driven hazard reactions and generate_route_geojson() for routing.",
                    [
                        "Critical Routing Gap: generate_route_geojson() does not call any OSRM server or routing engine. It generates a synthetic 3-point straight line with an arbitrary offset (+0.01 lat), which cannot represent real mountain road topography.",
                        "Heuristic Deficit: Blockage reactions apply a flat hardcoded +45 min delay regardless of actual detour length or road segment classification.",
                        "Localization Gap: Alert messages are hardcoded English strings ('CRITICAL: Road obstruction reported...'), ignoring the recipient's preferred_language.",
                        "Channel Incompleteness: Alerts are only saved to the database with channel='app'. No external SMS (Twilio/Fast2SMS) or WebPush dispatches occur."
                    ]
                ),
                (
                    "backend/core/models.py",
                    "Defines District, Need, Resource, Condition, MediaAttachment, Allocation, and Alert.",
                    [
                        "Data Model Deficit: Allocation lacks an allocated_quantity field, preventing partial fulfillments or multi-depot relief splits.",
                        "Serialization Deficit: District.boundary is a SpatialPolygonField, but DistrictSerializer lacks GeoJSON polygon formatting/validation logic."
                    ]
                ),
                (
                    "backend/core/spatial_compat.py",
                    "Fallback compatibility layer providing MockPoint and FallbackSpatialField when PostGIS/GDAL is unavailable.",
                    [
                        "Performance Bottleneck: FallbackSpatialField stores coordinates in JSONField. Without PostGIS spatial indexing (R-Tree/GiST), bounding-box spatial queries cannot run at the database level, forcing in-memory Python calculations."
                    ]
                ),
            ]
        },
        {
            "category": "Matching Engine & Inventory Orchestration (backend/matching/ & matching_engine/)",
            "files": [
                (
                    "backend/matching/services.py",
                    "Orchestrates resource discovery, candidate scoring via matching_engine, and allocation confirmation.",
                    [
                        "Critical Inventory Bug: confirm_match_and_allocate() marks Need as 'matched' and creates an Allocation, but NEVER decrements Resource.quantity_available. Multiple needs can allocate the same stockpile simultaneously (phantom inventory).",
                        "Concurrency Deficit: Does not use select_for_update() on candidate resources, risking race conditions and duplicate allocations during concurrent dispatches.",
                        "Hazard Scoring Blindspot: Corridor hazard evaluation only inspects the candidate depot's home district (cand.district). If the transport corridor traverses intermediate blocked districts, the hazard is completely ignored."
                    ]
                ),
                (
                    "matching_engine/scoring.py",
                    "Multi-criteria weighted scoring algorithm evaluating Urgency, Proximity (exponential decay), Verification, Quantity Fit, and Delay Risk.",
                    [
                        "Logic Deficit: Proximity decay assumes a fixed 25 km half-life without adjusting for mountainous terrain non-linear travel times.",
                        "Logic Deficit: Quantity fit score penalizes partial fulfillment linearly without multi-depot bundling options."
                    ]
                ),
                (
                    "matching_engine/risk_model/predict.py & train.py",
                    "GradientBoostingClassifier pipeline trained to predict disruption probability based on geo-climatic indicators.",
                    [
                        "Point vs. Corridor Deficit: predict_risk() only evaluates a single coordinate pair rather than an entire route polyline.",
                        "Synthetic Data Deficit: Model is trained on synthetic approximations. When missing features (elevation, soil, drainage), it relies on hardcoded heuristics rather than querying live GIS/DEM rasters."
                    ]
                ),
            ]
        },
        {
            "category": "Logistics, Telemetry & Analytics (backend/logistics/ & backend/dashboard/)",
            "files": [
                (
                    "backend/logistics/models.py & views.py",
                    "Vehicle fleet registry and real-time GPS coordinate ingestion endpoint (/api/vehicles/{id}/ping/).",
                    [
                        "Telemetry Gap: Vehicle only stores current_location and last_ping_at. There is no telemetry history/breadcrumb log to reconstruct historical routes or calculate off-route deviations.",
                        "Security Deficit: VehicleViewSet.ping() allows any caller to update any vehicle's location without verifying that the authenticated user is the assigned operator.",
                        "Validation Deficit: VehiclePingSerializer lacks coordinate bounding box checks (allowing invalid lat/lon values)."
                    ]
                ),
                (
                    "backend/dashboard/views.py",
                    "DistrictSummaryView (/api/dashboard/district-summary/) calculating District Bottleneck Indices and regional health.",
                    [
                        "Severe Performance Issue (N+1 Queries): Iterates over all districts in Python and executes 11 distinct SQL queries per district. For 120 NER districts, this fires 1,320+ SQL queries per GET request.",
                        "Remediation Needed: Must refactor to use Django ORM annotations (.annotate(Count('needs', filter=...))) into a single aggregated SQL query."
                    ]
                ),
            ]
        },
        {
            "category": "Infrastructure, Configuration & DevOps (backend/config/, Docker, Nginx)",
            "files": [
                (
                    "docker-compose.yml & backend/Dockerfile",
                    "Production container orchestration declaring PostGIS, Gunicorn Django backend, Frontend, and Nginx reverse proxy.",
                    [
                        "Missing Command: Backend container does not run 'python manage.py collectstatic --noinput' on startup.",
                        "Path Mismatch: Backend sets MEDIA_ROOT=/app/backend/media, while infra/nginx.conf maps /media/ to /app/media/, causing media file 404s under Nginx."
                    ]
                ),
                (
                    "backend/config/settings.py",
                    "Django central settings (REST framework, JWT, database connection, CORS).",
                    [
                        "Missing Rate Limiting: REST_FRAMEWORK lacks DEFAULT_THROTTLE_CLASSES / DEFAULT_THROTTLE_RATES.",
                        "Missing WebSockets: Settings and ASGI configuration lack Django Channels routing and Redis channel layers for real-time live pushing."
                    ]
                ),
            ]
        }
    ]

    for cat_idx, cat in enumerate(files_audit, 1):
        story.append(Paragraph(f"3.{cat_idx} {cat['category']}", h2_style))
        for filename, desc, problems in cat['files']:
            f_box_data = [
                [Paragraph(f"<b>File:</b> <code>{filename}</code>", file_title_style)],
                [Paragraph(f"<b>Purpose:</b> {desc}", meta_style)],
                [Paragraph("<b>Identified Technical Problems:</b>", body_bold)],
            ]
            for p in problems:
                f_box_data.append([Paragraph(f"• {p}", body_style)])

            f_table = Table(f_box_data, colWidths=[522])
            f_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(f_table)
            story.append(Spacer(1, 6))

    story.append(PageBreak())

    # Section 4: Categorized Core Deficit Deep-Dive
    story.append(Paragraph("4. Core Architecture Deficits Deep-Dive", h1_style))
    story.append(Paragraph("Categorization of the systemic architectural shortcomings discovered during the audit:", body_style))
    story.append(Spacer(1, 6))

    deficit_categories = [
        (
            "1. Access Control & Security Posture",
            danger_color,
            "• Public Read/Write on All Endpoints: Overriding ViewSet permissions with AllowAny exposes critical disaster infrastructure to malicious tampering.\n"
            "• Unauthenticated 500 Server Crashes: Serializers assume authenticated users and fail with raw IntegrityError exceptions when unauthenticated requests are received.\n"
            "• File Upload Exploitation: Unrestricted multipart upload endpoints allow arbitrary file extensions and unbounded upload sizes."
        ),
        (
            "2. Inventory Integrity & Transactional Consistency",
            danger_color,
            "• Phantom Inventory Bug: Confirming an allocation does not decrement available stock, allowing double-allocation of finite medical/food supplies.\n"
            "• Missing Concurrency Protection: Lack of row-level locks (select_for_update) exposes concurrent dispatch operations to race conditions.\n"
            "• Single-Depot Constraint: Allocation model lacks support for partial fulfillments and multi-source supply aggregation."
        ),
        (
            "3. AI Disruption Modeling & Routing Reality",
            warning_color,
            "• Mock OSRM Geometry: The route generator produces a synthetic 3-point straight line with an arbitrary offset rather than real topological road geometries.\n"
            "• Intermediate Transit Blindspots: Hazard scoring inspects only the origin district and misses active landslides in intermediate transit corridors (e.g. NH-6).\n"
            "• Single-Point Inference: AI risk prediction evaluates single coordinates rather than continuous road corridors."
        ),
        (
            "4. Real-Time Telemetry & Communication Gaps",
            warning_color,
            "• Volatile Telemetry: Overwriting vehicle coordinates without a historical breadcrumb log prevents route reconstruction and off-route detection.\n"
            "• Passive Alerting: Alerts exist only as database records; no external SMS, WebPush, or WebSocket push notifications are dispatched.\n"
            "• Unlocalized Alerting: Generated alert strings are hardcoded in English, ignoring Assamese, Bengali, and Hindi user preferences."
        ),
        (
            "5. Scalability & Database Performance",
            primary_color,
            "• Dashboard N+1 Query Explosion: 11 SQL queries executed per district in a Python loop creates severe latency on regional dashboards.\n"
            "• Spatial Indexing in Fallback Mode: JSON-based coordinate storage prevents native spatial indexing when running in fallback SQLite environments."
        ),
    ]

    for d_title, d_color, d_desc in deficit_categories:
        d_box = [
            [Paragraph(f"<b>{d_title}</b>", ParagraphStyle('DTitle', parent=body_bold, textColor=d_color))],
            [Paragraph(d_desc.replace('\n', '<br/>'), body_style)],
        ]
        t = Table(d_box, colWidths=[522])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, d_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 8))

    # Section 5: Prioritized Remediation Roadmap
    story.append(Paragraph("5. Prioritized Remediation Roadmap", h1_style))
    roadmap_data = [
        [
            Paragraph("Priority", tbl_header),
            Paragraph("Action Item", tbl_header),
            Paragraph("Target File(s)", tbl_header),
            Paragraph("Expected Impact", tbl_header)
        ],
        [
            Paragraph("<font color='#b91c1c'><b>P0 (Immediate)</b></font>", tbl_cell),
            Paragraph("<b>Enforce RBAC Permissions:</b> Replace AllowAny with IsAuthenticated and specific role permissions across all ViewSets. Add user fallback checks.", tbl_cell),
            Paragraph("<code>core/views.py</code><br/><code>matching/views.py</code><br/><code>logistics/views.py</code>", tbl_cell),
            Paragraph("Prevents unauthorized tampering and resolves unhandled 500 server crash exceptions.", tbl_cell)
        ],
        [
            Paragraph("<font color='#b91c1c'><b>P0 (Immediate)</b></font>", tbl_cell),
            Paragraph("<b>Fix Resource Inventory Bug:</b> Wrap confirmation in select_for_update() and decrement quantity_available. Add allocated_quantity to Allocation.", tbl_cell),
            Paragraph("<code>matching/services.py</code><br/><code>core/models.py</code>", tbl_cell),
            Paragraph("Eliminates phantom inventory double-allocations and ensures stock consistency.", tbl_cell)
        ],
        [
            Paragraph("<font color='#b45309'><b>P1 (High)</b></font>", tbl_cell),
            Paragraph("<b>Optimize Dashboard Analytics:</b> Replace Python loop queries with single aggregated ORM query using .annotate() and Count(filter=Q(...)).", tbl_cell),
            Paragraph("<code>dashboard/views.py</code>", tbl_cell),
            Paragraph("Reduces database queries from 1,320+ to 1, providing sub-50ms dashboard response times.", tbl_cell)
        ],
        [
            Paragraph("<font color='#b45309'><b>P1 (High)</b></font>", tbl_cell),
            Paragraph("<b>Integrate Real Routing Engine:</b> Connect actual OSRM / OpenRouteService client for authentic driving geometry and corridor hazard intersections.", tbl_cell),
            Paragraph("<code>core/services.py</code><br/><code>matching/services.py</code>", tbl_cell),
            Paragraph("Enables realistic mountain travel times, detour delay calculations, and cross-district hazard detection.", tbl_cell)
        ],
        [
            Paragraph("<font color='#b45309'><b>P1 (High)</b></font>", tbl_cell),
            Paragraph("<b>Implement Telemetry Breadcrumb History:</b> Create VehicleLocationPing model to store full GPS history, speed, and heading.", tbl_cell),
            Paragraph("<code>logistics/models.py</code><br/><code>logistics/views.py</code>", tbl_cell),
            Paragraph("Enables live breadcrumbs on maps and off-route deviation tracking for relief fleets.", tbl_cell)
        ],
        [
            Paragraph("<font color='#1e293b'><b>P2 (Medium)</b></font>", tbl_cell),
            Paragraph("<b>Multilingual Alerting & Notification Gateways:</b> Implement translation dictionaries (as, bn, hi) and integrate external SMS/WebPush dispatchers.", tbl_cell),
            Paragraph("<code>core/services.py</code><br/><code>config/settings.py</code>", tbl_cell),
            Paragraph("Delivers localized disaster notifications across SMS, Push, and Web channels.", tbl_cell)
        ],
        [
            Paragraph("<font color='#1e293b'><b>P2 (Medium)</b></font>", tbl_cell),
            Paragraph("<b>DevOps & File Upload Security:</b> Fix Nginx media routing paths, add collectstatic to Docker startup, and add MIME/size validation on uploads.", tbl_cell),
            Paragraph("<code>docker-compose.yml</code><br/><code>infra/nginx.conf</code><br/><code>core/serializers.py</code>", tbl_cell),
            Paragraph("Ensures smooth production asset serving and prevents file upload exploits.", tbl_cell)
        ],
    ]

    roadmap_table = Table(roadmap_data, colWidths=[75, 175, 120, 152])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(roadmap_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF audit report: {filename}")


if __name__ == '__main__':
    output_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SETU_Backend_Shortcomings_Report.pdf")
    build_pdf(output_filename)
