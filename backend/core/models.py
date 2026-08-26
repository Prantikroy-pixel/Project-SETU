"""
Core models for SETU.
Defines District, Need, Resource, Condition, MediaAttachment, Allocation, and Alert.
"""

from django.db import models
from django.conf import settings
from .spatial_compat import SpatialPointField, SpatialPolygonField


# Resource & Need Type Vocabulary
SUPPLY_TYPE_FOOD = 'food'
SUPPLY_TYPE_WATER = 'water'
SUPPLY_TYPE_MEDICINE = 'medicine'
SUPPLY_TYPE_CONSTRUCTION = 'construction_material'
SUPPLY_TYPE_AGRI = 'agricultural_produce'
SUPPLY_TYPE_OTHER = 'other'

SUPPLY_TYPE_CHOICES = [
    (SUPPLY_TYPE_FOOD, 'Food Supplies'),
    (SUPPLY_TYPE_WATER, 'Drinking Water'),
    (SUPPLY_TYPE_MEDICINE, 'Medical Supplies & Medicines'),
    (SUPPLY_TYPE_CONSTRUCTION, 'Construction & Shelter Material'),
    (SUPPLY_TYPE_AGRI, 'Agricultural Produce & Seeds'),
    (SUPPLY_TYPE_OTHER, 'Other Essential Resource'),
]

URGENCY_CRITICAL = 'critical'
URGENCY_HIGH = 'high'
URGENCY_MEDIUM = 'medium'
URGENCY_LOW = 'low'

URGENCY_CHOICES = [
    (URGENCY_CRITICAL, 'Critical (Immediate Action)'),
    (URGENCY_HIGH, 'High (Within 6-12 hours)'),
    (URGENCY_MEDIUM, 'Medium (Within 24-48 hours)'),
    (URGENCY_LOW, 'Low (Routine)'),
]

NEED_STATUS_OPEN = 'open'
NEED_STATUS_MATCHED = 'matched'
NEED_STATUS_FULFILLED = 'fulfilled'
NEED_STATUS_CANCELLED = 'cancelled'

NEED_STATUS_CHOICES = [
    (NEED_STATUS_OPEN, 'Open'),
    (NEED_STATUS_MATCHED, 'Matched'),
    (NEED_STATUS_FULFILLED, 'Fulfilled'),
    (NEED_STATUS_CANCELLED, 'Cancelled'),
]

VERIFICATION_VERIFIED_ORG = 'verified_org'
VERIFICATION_UNVERIFIED = 'unverified'

VERIFICATION_CHOICES = [
    (VERIFICATION_VERIFIED_ORG, 'Verified Organization / Agency'),
    (VERIFICATION_UNVERIFIED, 'Unverified Individual / Provider'),
]

CONDITION_ROAD_STATUS = 'road_status'
CONDITION_RAINFALL = 'rainfall'
CONDITION_TEMPERATURE = 'temperature'
CONDITION_TRAFFIC = 'traffic'
CONDITION_CROWD_LEVEL = 'crowd_level'
CONDITION_BIN_FILL = 'bin_fill'
CONDITION_LANDSLIDE_RISK = 'landslide_risk'

CONDITION_TYPE_CHOICES = [
    (CONDITION_ROAD_STATUS, 'Road Status / Obstruction'),
    (CONDITION_RAINFALL, 'Rainfall (mm)'),
    (CONDITION_TEMPERATURE, 'Temperature (°C)'),
    (CONDITION_TRAFFIC, 'Traffic Bottleneck'),
    (CONDITION_CROWD_LEVEL, 'Crowd / Gathering Level'),
    (CONDITION_BIN_FILL, 'Waste / Bin Fill Level'),
    (CONDITION_LANDSLIDE_RISK, 'Landslide / Flood Risk Score'),
]

SOURCE_FIELD_REPORT = 'field_report'
SOURCE_WEATHER_API = 'weather_api'
SOURCE_PREDICTION_MODEL = 'prediction_model'
SOURCE_SENSOR = 'sensor'

SOURCE_CHOICES = [
    (SOURCE_FIELD_REPORT, 'Field Report'),
    (SOURCE_WEATHER_API, 'Weather API (IMD / OpenWeather)'),
    (SOURCE_PREDICTION_MODEL, 'AI Prediction Model'),
    (SOURCE_SENSOR, 'IoT Sensor / Automated Feed'),
]

MEDIA_TYPE_PHOTO = 'photo'
MEDIA_TYPE_VIDEO = 'video'

MEDIA_TYPE_CHOICES = [
    (MEDIA_TYPE_PHOTO, 'Photo'),
    (MEDIA_TYPE_VIDEO, 'Video'),
]

DELIVERY_STATUS_MATCHED = 'matched'
DELIVERY_STATUS_DISPATCHED = 'dispatched'
DELIVERY_STATUS_EN_ROUTE = 'en_route'
DELIVERY_STATUS_DELIVERED = 'delivered'
DELIVERY_STATUS_DELAYED = 'delayed'

DELIVERY_STATUS_CHOICES = [
    (DELIVERY_STATUS_MATCHED, 'Matched / Pending Dispatch'),
    (DELIVERY_STATUS_DISPATCHED, 'Dispatched'),
    (DELIVERY_STATUS_EN_ROUTE, 'En Route'),
    (DELIVERY_STATUS_DELIVERED, 'Delivered & Fulfilled'),
    (DELIVERY_STATUS_DELAYED, 'Delayed / Rerouting'),
]

ALERT_TYPE_ROAD_BLOCKED = 'road_blocked'
ALERT_TYPE_HIGH_RISK_CORRIDOR = 'high_risk_corridor'
ALERT_TYPE_DELIVERY_DELAYED = 'delivery_delayed'
ALERT_TYPE_DISRUPTION_PREDICTED = 'disruption_predicted'

ALERT_TYPE_CHOICES = [
    (ALERT_TYPE_ROAD_BLOCKED, 'Road Blocked / Impassable'),
    (ALERT_TYPE_HIGH_RISK_CORRIDOR, 'High Risk Corridor Alert'),
    (ALERT_TYPE_DELIVERY_DELAYED, 'Delivery Delayed'),
    (ALERT_TYPE_DISRUPTION_PREDICTED, 'Disruption Predicted by AI'),
]

CHANNEL_SMS = 'sms'
CHANNEL_PUSH = 'push'
CHANNEL_APP = 'app'

CHANNEL_CHOICES = [
    (CHANNEL_SMS, 'SMS Text Message'),
    (CHANNEL_PUSH, 'Push Notification'),
    (CHANNEL_APP, 'In-App Alert Banner'),
]


class District(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Cachar, East Khasi Hills")
    state = models.CharField(max_length=50, help_text="e.g. Assam, Meghalaya")
    boundary = SpatialPolygonField(geography=True, null=True, blank=True, help_text="District boundary polygon for choropleths")
    centroid = SpatialPointField(geography=True, null=True, blank=True, help_text="Center coordinate for quick zoom/centering")
    population = models.IntegerField(null=True, blank=True, help_text="District population for impact analysis")

    class Meta:
        ordering = ['state', 'name']

    def __str__(self):
        return f"{self.name}, {self.state}"


class Need(models.Model):
    type = models.CharField(max_length=50, choices=SUPPLY_TYPE_CHOICES)
    location = SpatialPointField(geography=True, spatial_index=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='needs')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default=URGENCY_MEDIUM)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=20, help_text="e.g. kg, units, packets, litres")
    description = models.TextField(blank=True, default='')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_needs')
    status = models.CharField(max_length=20, choices=NEED_STATUS_CHOICES, default=NEED_STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Need #{self.pk}: {self.get_type_display()} ({self.quantity} {self.unit}) [{self.urgency}]"


class Resource(models.Model):
    type = models.CharField(max_length=50, choices=SUPPLY_TYPE_CHOICES)
    location = SpatialPointField(geography=True, spatial_index=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    quantity_available = models.PositiveIntegerField()
    unit = models.CharField(max_length=20)
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provided_resources')
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_CHOICES, default=VERIFICATION_UNVERIFIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Resource #{self.pk}: {self.get_type_display()} ({self.quantity_available} {self.unit})"


class Condition(models.Model):
    location = SpatialPointField(geography=True, spatial_index=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='conditions')
    condition_type = models.CharField(max_length=50, choices=CONDITION_TYPE_CHOICES)
    value = models.CharField(max_length=50, help_text="e.g. 'blocked', '42mm', 'high', 'clear'")
    risk_score = models.FloatField(null=True, blank=True, help_text="0.0 to 1.0 risk score calculated by AI model")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_conditions')
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default=SOURCE_FIELD_REPORT)
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"Condition #{self.pk}: {self.get_condition_type_display()} = {self.value} ({self.source})"


class MediaAttachment(models.Model):
    need = models.ForeignKey(Need, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    condition = models.ForeignKey(Condition, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    file = models.FileField(upload_to='reports/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default=MEDIA_TYPE_PHOTO)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment #{self.pk} ({self.media_type}) uploaded at {self.uploaded_at}"


class Allocation(models.Model):
    match = models.OneToOneField('matching.Match', on_delete=models.CASCADE, related_name='allocation')
    vehicle = models.ForeignKey('logistics.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='allocations')
    route_geojson = models.JSONField(null=True, blank=True, help_text="OSRM route geometry GeoJSON")
    estimated_delay_minutes = models.IntegerField(null=True, blank=True, default=0)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default=DELIVERY_STATUS_MATCHED)
    assigned_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_at']

    def __str__(self):
        return f"Allocation #{self.pk} for Match #{self.match_id} [{self.delivery_status}]"


class Alert(models.Model):
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    related_condition = models.ForeignKey(Condition, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    related_allocation = models.ForeignKey(Allocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=URGENCY_CHOICES, default=URGENCY_MEDIUM)
    language = models.CharField(max_length=10, default='en')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=CHANNEL_APP)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Alert #{self.pk} [{self.severity.upper()}]: {self.message[:40]}"


# Critical Institutions & Government Sectors Ingestion Model
INSTITUTION_CATEGORY_HOSPITAL = 'hospital'
INSTITUTION_CATEGORY_GOVT = 'govt_office'
INSTITUTION_CATEGORY_EMERGENCY = 'emergency_station'
INSTITUTION_CATEGORY_SHELTER = 'relief_shelter'
INSTITUTION_CATEGORY_LOGISTICS = 'logistics_hub'

INSTITUTION_CATEGORY_CHOICES = [
    (INSTITUTION_CATEGORY_HOSPITAL, 'Hospital & Medical Center'),
    (INSTITUTION_CATEGORY_GOVT, 'Government Sector & DC Office'),
    (INSTITUTION_CATEGORY_EMERGENCY, 'Emergency & Disaster Response Hub (SDRF/NDRF/Fire)'),
    (INSTITUTION_CATEGORY_SHELTER, 'High-Ground Flood / Disaster Relief Shelter'),
    (INSTITUTION_CATEGORY_LOGISTICS, 'Strategic Logistics Hub / FCI Food Storage Depot'),
]

OPERATIONAL_STATUS_OPERATIONAL = 'operational'
OPERATIONAL_STATUS_PARTIAL = 'partially_functional'
OPERATIONAL_STATUS_FLOODED = 'flooded_impaired'
OPERATIONAL_STATUS_OFFLINE = 'offline'

OPERATIONAL_STATUS_CHOICES = [
    (OPERATIONAL_STATUS_OPERATIONAL, 'Operational / Active'),
    (OPERATIONAL_STATUS_PARTIAL, 'Partially Functional'),
    (OPERATIONAL_STATUS_FLOODED, 'Flooded / Impaired Access'),
    (OPERATIONAL_STATUS_OFFLINE, 'Offline / Evacuated'),
]


class Institution(models.Model):
    name = models.CharField(max_length=200, help_text="e.g. Gauhati Medical College & Hospital (GMCH)")
    category = models.CharField(max_length=50, choices=INSTITUTION_CATEGORY_CHOICES, default=INSTITUTION_CATEGORY_HOSPITAL)
    facility_type = models.CharField(max_length=100, blank=True, default='', help_text="e.g. Tertiary Care Medical College, DC Office, 1st Bn NDRF")
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='institutions')
    state = models.CharField(max_length=50, help_text="e.g. Assam, Meghalaya")
    location = SpatialPointField(geography=True, spatial_index=True)
    address = models.TextField(blank=True, default='')
    contact_number = models.CharField(max_length=50, blank=True, default='')
    emergency_helpline = models.CharField(max_length=50, blank=True, default='')
    bed_capacity = models.IntegerField(null=True, blank=True, default=0, help_text="Hospital bed count or shelter capacity")
    is_auto_ingested = models.BooleanField(default=True, help_text="True if automatically ingested from public APIs (OSM / Govt Registry)")
    source_api = models.CharField(max_length=50, default='osm_overpass', help_text="e.g. osm_overpass, nhm_registry, sdma_feed")
    operational_status = models.CharField(max_length=30, choices=OPERATIONAL_STATUS_CHOICES, default=OPERATIONAL_STATUS_OPERATIONAL)
    metadata = models.JSONField(blank=True, default=dict, help_text="Additional JSON metadata (oxygen plant, ICU beds, emergency power, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['state', 'category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()}) - {self.district.name if self.district else self.state}"

