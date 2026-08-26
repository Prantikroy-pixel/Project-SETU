"""
Views and ViewSets for core SETU app.
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import (
    District, Need, Resource, Condition, MediaAttachment, Allocation, Alert, Institution
)
from .serializers import (
    DistrictSerializer, NeedSerializer, ResourceSerializer,
    ConditionSerializer, MediaAttachmentSerializer,
    AllocationSerializer, AlertSerializer, InstitutionSerializer
)
from .services import trigger_condition_alerts
from .boundary_service import BorderTrackingService, RealtimeBoundaryFetcher
from .institution_service import InstitutionIngestionService
from .validators import validate_uploaded_media
from matching_engine.risk_model.predict import predict_risk
from accounts.permissions import (
    IsAdminUserOrReadOnly, IsDistrictAdmin, IsOwnerOrAdminOrReadOnly,
    IsFieldOfficerOrAdminOrReadOnly, IsTransportOperatorOrAdminOrReadOnly,
    IsVerifiedProviderOrReadOnly, IsOwnerOrAdmin
)


class DistrictViewSet(viewsets.ModelViewSet):
    """
    CRUD for administrative districts.
    GET /api/districts/ (Public read-only)
    GET /api/districts/{id}/ (Public read-only)
    POST / PUT / PATCH / DELETE /api/districts/{id}/ (Admin only)
    """
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'state']

    @action(detail=True, methods=['get'], url_path='boundary')
    def get_district_boundary(self, request, pk=None):
        """Returns official GeoJSON polygon for this district, fetching live if not yet stored."""
        district = self.get_object()
        if district.boundary:
            return Response({
                'district_id': district.id,
                'name': district.name,
                'state': district.state,
                'geometry': district.boundary,
                'source': 'database'
            })

        fetcher = RealtimeBoundaryFetcher()
        live_boundary = fetcher.fetch_district_geojson_boundary(district.name, district.state)
        if live_boundary and 'geometry' in live_boundary:
            district.boundary = live_boundary['geometry']
            district.save(update_fields=['boundary'])
            return Response({
                'district_id': district.id,
                'name': district.name,
                'state': district.state,
                'geometry': live_boundary['geometry'],
                'source': 'openstreetmap_live'
            })

        return Response({
            'district_id': district.id,
            'name': district.name,
            'state': district.state,
            'geometry': None,
            'message': 'Boundary polygon currently unavailable for this district.'
        }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='sync-boundaries', permission_classes=[IsDistrictAdmin])
    def sync_all_boundaries(self, request):
        """Triggers live synchronization of boundary polygons for all districts."""
        state_filter = request.data.get('state')
        fetcher = RealtimeBoundaryFetcher()
        result = fetcher.sync_district_boundaries_to_db(state_filter=state_filter)
        return Response(result, status=status.HTTP_200_OK)


class NeedViewSet(viewsets.ModelViewSet):
    """
    CRUD for relief and essential resource needs.
    GET /api/needs/ (Public read-only)
    POST /api/needs/ (Authenticated users - citizens, officers, NGOs, admin)
    PUT / PATCH / DELETE /api/needs/{id}/ (Owner or Admin only)
    """
    queryset = Need.objects.all().select_related('reported_by', 'district').prefetch_related('attachments')
    serializer_class = NeedSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['description', 'unit', 'type']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        type_param = self.request.query_params.get('type')
        district_param = self.request.query_params.get('district')
        urgency_param = self.request.query_params.get('urgency')

        if status_param:
            qs = qs.filter(status=status_param)
        if type_param:
            qs = qs.filter(type=type_param)
        if district_param:
            qs = qs.filter(district_id=district_param)
        if urgency_param:
            qs = qs.filter(urgency=urgency_param)

        return qs

    def perform_create(self, serializer):
        if not serializer.validated_data.get('reported_by') and self.request.user.is_authenticated:
            serializer.save(reported_by=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='attachments', permission_classes=[IsOwnerOrAdminOrReadOnly])
    def upload_attachment(self, request, pk=None):
        need = self.get_object()
        file_obj = request.FILES.get('file')
        media_type = request.data.get('media_type', 'photo')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_uploaded_media(file_obj)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        attachment = MediaAttachment.objects.create(
            need=need,
            file=file_obj,
            media_type=media_type
        )
        return Response(MediaAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class ResourceViewSet(viewsets.ModelViewSet):
    """
    CRUD for available supplies and resources.
    GET /api/resources/ (Public read-only)
    POST /api/resources/ (Verified NGOs/providers and Admins)
    PUT / PATCH / DELETE /api/resources/{id}/ (Owner provider or Admin only)
    """
    queryset = Resource.objects.all().select_related('provider', 'district')
    serializer_class = ResourceSerializer
    permission_classes = [IsVerifiedProviderOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        type_param = self.request.query_params.get('type')
        district_param = self.request.query_params.get('district')
        verification = self.request.query_params.get('verification_status')
        available_only = self.request.query_params.get('available_only', 'false').lower() == 'true'

        if type_param:
            qs = qs.filter(type=type_param)
        if district_param:
            qs = qs.filter(district_id=district_param)
        if verification:
            qs = qs.filter(verification_status=verification)
        if available_only:
            qs = qs.filter(quantity_available__gt=0)

        return qs

    def perform_create(self, serializer):
        if not serializer.validated_data.get('provider') and self.request.user.is_authenticated:
            serializer.save(provider=self.request.user)
        else:
            serializer.save()


class ConditionViewSet(viewsets.ModelViewSet):
    """
    CRUD and predictive analytics for ground condition reports.
    GET /api/conditions/ (Public read-only)
    POST /api/conditions/ (Field Officers and Admins)
    PUT / PATCH / DELETE /api/conditions/{id}/ (Reporting Officer or Admin only)
    """
    queryset = Condition.objects.all().select_related('reported_by', 'district').prefetch_related('attachments')
    serializer_class = ConditionSerializer
    permission_classes = [IsFieldOfficerOrAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        district_param = self.request.query_params.get('district')
        type_param = self.request.query_params.get('condition_type')
        source_param = self.request.query_params.get('source')
        bbox_param = self.request.query_params.get('bbox')
        near_lat = self.request.query_params.get('near_lat') or self.request.query_params.get('lat')
        near_lon = self.request.query_params.get('near_lon') or self.request.query_params.get('lon')
        radius_km = self.request.query_params.get('radius_km')

        if district_param:
            qs = qs.filter(district_id=district_param)
        if type_param:
            qs = qs.filter(condition_type=type_param)
        if source_param:
            qs = qs.filter(source=source_param)

        # Spatial Bounding Box Filter: minLon,minLat,maxLon,maxLat
        if bbox_param:
            try:
                min_lon, min_lat, max_lon, max_lat = [float(x.strip()) for x in bbox_param.split(',')]
                qs = qs.filter(
                    latitude__gte=min_lat,
                    latitude__lte=max_lat,
                    longitude__gte=min_lon,
                    longitude__lte=max_lon
                )
            except Exception:
                pass

        # Proximity Range Radius Filter
        if near_lat and near_lon and radius_km:
            try:
                c_lat, c_lon, rad = float(near_lat), float(near_lon), float(radius_km)
                deg_delta = rad / 111.0
                qs = qs.filter(
                    latitude__gte=c_lat - deg_delta,
                    latitude__lte=c_lat + deg_delta,
                    longitude__gte=c_lon - deg_delta,
                    longitude__lte=c_lon + deg_delta
                )
            except Exception:
                pass

        return qs

    def perform_create(self, serializer):
        if not serializer.validated_data.get('reported_by') and self.request.user.is_authenticated:
            condition = serializer.save(reported_by=self.request.user)
        else:
            condition = serializer.save()
        # Auto-trigger alert evaluation
        trigger_condition_alerts(condition)

    @action(detail=True, methods=['post'], url_path='attachments', permission_classes=[IsFieldOfficerOrAdminOrReadOnly])
    def upload_attachment(self, request, pk=None):
        condition = self.get_object()
        file_obj = request.FILES.get('file')
        media_type = request.data.get('media_type', 'photo')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_uploaded_media(file_obj)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        attachment = MediaAttachment.objects.create(
            condition=condition,
            file=file_obj,
            media_type=media_type
        )
        return Response(MediaAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='predict-risk')
    def predict_risk_view(self, request):
        """
        GET /api/conditions/predict-risk/?lat=24.83&lon=92.78&rainfall=80&slope=30&use_realtime=true
        Evaluates disruption hazard score using the trained ML model & live real-time fetcher.
        """
        try:
            lat = float(request.query_params.get('lat', request.query_params.get('latitude', 24.8333)))
            lon = float(request.query_params.get('lon', request.query_params.get('longitude', 92.7789)))

            def _get_float_param(key):
                val = request.query_params.get(key)
                return float(val) if val is not None and val != '' else None

            rainfall_val = _get_float_param('rainfall') or _get_float_param('rainfall_24h')
            slope_val = _get_float_param('slope')
            elevation_val = _get_float_param('elevation') or _get_float_param('elevation_m')
            soil_sat_val = _get_float_param('soil_saturation')
            drainage_val = _get_float_param('drainage') or _get_float_param('drainage_quality')
            veg_val = _get_float_param('vegetation') or _get_float_param('vegetation_cover')

            use_realtime_param = request.query_params.get('use_realtime', 'true').lower()
            use_realtime = use_realtime_param not in ('0', 'false', 'no', 'f')

            result = predict_risk(
                lat=lat,
                lon=lon,
                rainfall=rainfall_val,
                slope=slope_val,
                elevation=elevation_val,
                soil_saturation=soil_sat_val,
                drainage_quality=drainage_val,
                vegetation_cover=veg_val,
                use_realtime=use_realtime
            )
            return Response(result)
        except Exception as e:
            return Response({'error': f'Prediction failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'post'], url_path='predict-route-risk')
    def predict_route_risk_view(self, request):
        """
        POST / GET /api/conditions/predict-route-risk/
        Evaluates disruption risk, threats, anomalies, and status over an ENTIRE CORRIDOR ROUTE RANGE.
        """
        try:
            raw_waypoints = []
            if request.method == 'POST':
                data = request.data or {}
                raw_waypoints = data.get('waypoints', [])
                origin = data.get('origin')
                dest = data.get('destination')
                if not raw_waypoints and origin and dest:
                    raw_waypoints = [origin, dest]
                use_realtime = data.get('use_realtime', True)
                buffer_km = float(data.get('buffer_km', 5.0))
                custom_features = data.get('custom_features')
            else:
                wp_param = request.query_params.get('waypoints')
                if wp_param:
                    sep = ';' if ';' in wp_param else ('|' if '|' in wp_param else '\n')
                    for seg in wp_param.split(sep):
                        parts = seg.split(',')
                        if len(parts) >= 2:
                            raw_waypoints.append([float(parts[0].strip()), float(parts[1].strip())])
                else:
                    o_lat = request.query_params.get('origin_lat')
                    o_lon = request.query_params.get('origin_lon')
                    d_lat = request.query_params.get('dest_lat')
                    d_lon = request.query_params.get('dest_lon')
                    if o_lat and o_lon and d_lat and d_lon:
                        raw_waypoints = [[float(o_lat), float(o_lon)], [float(d_lat), float(d_lon)]]

                use_realtime_param = request.query_params.get('use_realtime', 'true').lower()
                use_realtime = use_realtime_param not in ('0', 'false', 'no', 'f')
                buffer_km = float(request.query_params.get('buffer_km', 5.0))
                custom_features = None

            if not raw_waypoints:
                raw_waypoints = [
                    [25.5788, 91.8933],
                    [25.4500, 92.2000],
                    [25.1812, 93.0175],
                    [24.8333, 92.7789],
                ]

            result = predict_route_risk(
                waypoints=raw_waypoints,
                buffer_km=buffer_km,
                use_realtime=use_realtime,
                custom_features=custom_features
            )
            return Response(result)
        except Exception as e:
            return Response({'error': f'Route risk prediction failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class AllocationViewSet(viewsets.ModelViewSet):
    """
    Tracking and updates for matched allocations.
    GET /api/allocations/ (Public read-only)
    PATCH /api/allocations/{id}/ (Transport Operator or Admin only)
    """
    queryset = Allocation.objects.all().select_related('match__need', 'match__resource', 'vehicle')
    serializer_class = AllocationSerializer
    permission_classes = [IsTransportOperatorOrAdminOrReadOnly]

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.delivery_status == 'delivered' and not instance.delivered_at:
            instance.delivered_at = timezone.now()
            # Also mark need as fulfilled
            instance.match.need.status = 'fulfilled'
            instance.match.need.save(update_fields=['status'])
            instance.save(update_fields=['delivered_at'])


class AlertViewSet(viewsets.ModelViewSet):
    """
    List and filter alerts.
    GET /api/alerts/ (Public read-only)
    POST / PUT / PATCH / DELETE /api/alerts/ (Admin only)
    """
    queryset = Alert.objects.all().select_related('district', 'related_condition', 'related_allocation')
    serializer_class = AlertSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        district = self.request.query_params.get('district')
        severity = self.request.query_params.get('severity')
        alert_type = self.request.query_params.get('alert_type')

        if district:
            qs = qs.filter(district_id=district)
        if severity:
            qs = qs.filter(severity=severity)
        if alert_type:
            qs = qs.filter(alert_type=alert_type)

        return qs


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    CRUD and automated querying for critical public institutions.
    GET /api/institutions/ (Public read-only)
    POST /api/institutions/sync-external/ (Admin only)
    POST / PUT / PATCH / DELETE /api/institutions/{id}/ (Admin only)
    """
    queryset = Institution.objects.all().select_related('district')
    serializer_class = InstitutionSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address', 'facility_type', 'state']

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        district = self.request.query_params.get('district')
        state = self.request.query_params.get('state')
        status_param = self.request.query_params.get('operational_status')
        live_param = self.request.query_params.get('live', 'false').lower() in ('true', '1', 'yes')

        # If live=true is requested and district is specified, sync live OSM data on the fly
        if live_param and district:
            try:
                service = InstitutionIngestionService()
                service.sync_all_institutions_to_db(
                    include_live_osm=True,
                    target_district=district,
                    state_name=state or "Assam"
                )
            except Exception:
                pass

        if category:
            qs = qs.filter(category=category)
        if district:
            # Match by foreign key id or name
            if district.isdigit():
                qs = qs.filter(district_id=int(district))
            else:
                qs = qs.filter(district__name__icontains=district)
        if state:
            qs = qs.filter(state__iexact=state)
        if status_param:
            qs = qs.filter(operational_status=status_param)

        return qs

    @action(detail=False, methods=['post'], url_path='sync-external')
    def sync_external(self, request):
        """
        Synchronizes institutions from OpenStreetMap and verified government master rosters.
        """
        include_osm = request.data.get('include_osm', True)
        district = request.data.get('district')
        state = request.data.get('state')
        service = InstitutionIngestionService()
        stats = service.sync_all_institutions_to_db(
            include_live_osm=include_osm,
            target_district=district,
            state_name=state
        )
        return Response({
            'status': 'success',
            'message': 'Institutions and strategic resources synchronized successfully.',
            'stats': stats
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='fetch-live')
    def fetch_live_institutions(self, request):
        """
        Fetches live institutions for a specified district or bounding box directly from OpenStreetMap.
        Body payload: { "district": "Cachar", "state": "Assam", "category": "hospital" }
        or { "bbox": [min_lat, min_lon, max_lat, max_lon], "category": "hospital" }
        """
        district = request.data.get('district')
        state = request.data.get('state', 'Assam')
        category = request.data.get('category')
        bbox = request.data.get('bbox')

        service = InstitutionIngestionService()
        if bbox and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            live_items = service.fetch_live_osm_institutions(
                bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
                category_filter=category
            )
        elif district:
            live_items = service.fetch_live_institutions_for_district(
                district_name=district,
                state_name=state,
                category_filter=category
            )
        else:
            live_items = service.fetch_live_osm_institutions(category_filter=category)

        return Response({
            'total_fetched': len(live_items),
            'source': 'openstreetmap_overpass_live',
            'results': live_items
        }, status=status.HTTP_200_OK)


class DistrictBoundaryView(APIView):
    """
    Returns official live GeoJSON boundary polygon for a district from OpenStreetMap / Nominatim.
    GET /api/boundaries/district-boundary/?name=Kamrup%20Metropolitan&state=Assam
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        name = request.query_params.get('name') or request.query_params.get('district')
        state = request.query_params.get('state', 'Assam')
        if not name:
            return Response({'error': 'name or district query parameter required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check DB first
        dist_obj = District.objects.filter(name__iexact=name).first()
        if dist_obj and dist_obj.boundary:
            return Response({
                'district_name': dist_obj.name,
                'state': dist_obj.state,
                'geometry': dist_obj.boundary,
                'source': 'database_persisted'
            }, status=status.HTTP_200_OK)

        fetcher = RealtimeBoundaryFetcher()
        boundary_data = fetcher.fetch_district_geojson_boundary(district_name=name, state_name=state)

        if boundary_data:
            # If district exists in DB, persist boundary
            if dist_obj:
                dist_obj.boundary = boundary_data['geometry']
                dist_obj.save(update_fields=['boundary'])
            return Response(boundary_data, status=status.HTTP_200_OK)

        # Reliable spatial fallback if live OSM lookup is unreachable or rate-limited
        if dist_obj:
            c_lon = dist_obj.centroid.longitude if dist_obj.centroid and hasattr(dist_obj.centroid, 'longitude') else 92.78
            c_lat = dist_obj.centroid.latitude if dist_obj.centroid and hasattr(dist_obj.centroid, 'latitude') else 24.83
            fallback_geom = {
                'type': 'Polygon',
                'coordinates': [[
                    [round(c_lon - 0.08, 4), round(c_lat - 0.08, 4)],
                    [round(c_lon + 0.08, 4), round(c_lat - 0.08, 4)],
                    [round(c_lon + 0.08, 4), round(c_lat + 0.08, 4)],
                    [round(c_lon - 0.08, 4), round(c_lat + 0.08, 4)],
                    [round(c_lon - 0.08, 4), round(c_lat - 0.08, 4)],
                ]]
            }
            dist_obj.boundary = fallback_geom
            dist_obj.save(update_fields=['boundary'])
            return Response({
                'district_name': dist_obj.name,
                'state': dist_obj.state,
                'geometry': fallback_geom,
                'source': 'centroid_buffer_generated'
            }, status=status.HTTP_200_OK)

        return Response({
            'error': f'Could not retrieve boundary for district: {name}',
            'district_name': name,
            'state': state
        }, status=status.HTTP_404_NOT_FOUND)


class StateBoundaryView(APIView):
    """
    Returns official live GeoJSON boundary polygon for a State in India.
    GET /api/boundaries/state-boundary/?state=Assam
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        state = request.query_params.get('state') or request.query_params.get('name')
        if not state:
            return Response({'error': 'state query parameter required.'}, status=status.HTTP_400_BAD_REQUEST)

        fetcher = RealtimeBoundaryFetcher()
        boundary_data = fetcher.fetch_state_geojson_boundary(state_name=state)

        if boundary_data:
            return Response(boundary_data, status=status.HTTP_200_OK)

        # Fallback state polygon for NER states
        state_centers = {
            'Assam': (26.2006, 92.9376),
            'Meghalaya': (25.4670, 91.3662),
            'Arunachal Pradesh': (28.2180, 94.7278),
            'Manipur': (24.6637, 93.9063),
            'Mizoram': (23.1645, 92.9376),
            'Nagaland': (26.1584, 94.5624),
            'Tripura': (23.9408, 91.9882),
            'Sikkim': (27.5330, 88.5122)
        }
        c_lat, c_lon = state_centers.get(state, (26.2006, 92.9376))
        return Response({
            'state_name': state,
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[
                    [round(c_lon - 0.5, 4), round(c_lat - 0.5, 4)],
                    [round(c_lon + 0.5, 4), round(c_lat - 0.5, 4)],
                    [round(c_lon + 0.5, 4), round(c_lat + 0.5, 4)],
                    [round(c_lon - 0.5, 4), round(c_lat + 0.5, 4)],
                    [round(c_lon - 0.5, 4), round(c_lat - 0.5, 4)],
                ]]
            },
            'source': 'state_buffer_generated'
        }, status=status.HTTP_200_OK)


class SyncDistrictBoundariesView(APIView):
    """
    Triggers live synchronization of boundary polygons for all registered districts in DB.
    POST /api/boundaries/sync-districts/ (District and Super Administrators only)
    """
    permission_classes = [IsDistrictAdmin]

    def post(self, request):
        state_filter = request.data.get('state')
        fetcher = RealtimeBoundaryFetcher()
        result = fetcher.sync_district_boundaries_to_db(state_filter=state_filter)
        return Response(result, status=status.HTTP_200_OK)


class BorderBoundaryView(APIView):
    """
    Returns all registered NER interstate and international border checkpoints,
    customs stations, and boundary metadata.
    GET /api/boundaries/ner-borders/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        border_type = request.query_params.get('type')
        state = request.query_params.get('state')
        service = BorderTrackingService()
        checkpoints = service.get_all_checkpoints()

        if border_type:
            checkpoints = [c for c in checkpoints if c['type'] == border_type]
        if state:
            checkpoints = [c for c in checkpoints if state.lower() in c.get('state', '').lower()]

        return Response({
            'total_checkpoints': len(checkpoints),
            'checkpoints': checkpoints,
            'international_borders': [
                {'country': 'Bangladesh', 'states_touching': ['Assam', 'Meghalaya', 'Tripura', 'Mizoram'], 'length_km': 1880},
                {'country': 'Bhutan', 'states_touching': ['Assam', 'Arunachal Pradesh', 'Sikkim', 'West Bengal'], 'length_km': 699},
                {'country': 'Myanmar', 'states_touching': ['Arunachal Pradesh', 'Nagaland', 'Manipur', 'Mizoram'], 'length_km': 1643},
                {'country': 'China (LAC)', 'states_touching': ['Arunachal Pradesh', 'Sikkim'], 'length_km': 1346},
                {'country': 'Nepal', 'states_touching': ['Sikkim', 'West Bengal'], 'length_km': 98}
            ]
        }, status=status.HTTP_200_OK)


class BorderProximityView(APIView):
    """
    Evaluates real-time geofence proximity of a coordinate to the nearest international
    or interstate border and flags regulatory permit requirements.
    GET /api/boundaries/check-proximity/?lat=25.184&lon=92.028&radius_km=20
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = float(request.query_params.get('lat', 26.1445))
            lon = float(request.query_params.get('lon', 91.7362))
            radius_km = float(request.query_params.get('radius_km', 20.0))
        except (ValueError, TypeError):
            return Response({'error': 'Invalid latitude, longitude, or radius_km parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        service = BorderTrackingService()
        result = service.check_point_border_proximity(lat=lat, lon=lon, threshold_km=radius_km)
        return Response(result, status=status.HTTP_200_OK)


class RouteBorderAnalysisView(APIView):
    """
    Analyzes an entire delivery convoy route (array of coordinates) for
    interstate border crossings, international buffer proximity, and ILP requirements.
    POST /api/boundaries/analyze-route/
    Payload: { "route_points": [ {"lat": 26.14, "lon": 91.73}, ... ] }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        route_points = request.data.get('route_points', [])
        if not route_points or not isinstance(route_points, list):
            return Response({'error': 'route_points array required with lat/lon coordinates.'}, status=status.HTTP_400_BAD_REQUEST)

        service = BorderTrackingService()
        analysis = service.analyze_route_crossings(route_points)
        return Response(analysis, status=status.HTTP_200_OK)


