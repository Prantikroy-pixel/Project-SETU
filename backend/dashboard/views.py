"""
Views for analytics and district dashboards in SETU.
Aggregates connectivity, bottleneck indexes, relief demands, and resource readiness per district.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Sum, Q
from core.models import District, Need, Resource, Condition, Alert, Allocation
from logistics.models import Vehicle


class DistrictSummaryView(APIView):
    """
    GET /api/dashboard/district-summary/
    Returns multi-district aggregated metrics for command dashboards,
    highlighting bottlenecks, critical deficits, and active road disruptions.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        districts = District.objects.all()
        district_data = []

        total_open_needs = 0
        total_critical_needs = 0
        total_fulfilled_needs = 0
        total_resources = 0
        total_blocked_roads = 0
        total_active_alerts = 0

        for dist in districts:
            needs_qs = dist.needs.all()
            resources_qs = dist.resources.all()
            conditions_qs = dist.conditions.all()
            alerts_qs = dist.alerts.all()

            open_needs_cnt = needs_qs.filter(status='open').count()
            critical_needs_cnt = needs_qs.filter(status='open', urgency='critical').count()
            fulfilled_needs_cnt = needs_qs.filter(status='fulfilled').count()
            total_needs_cnt = needs_qs.count()

            # Resources breakdown
            avail_res_cnt = resources_qs.filter(quantity_available__gt=0).count()
            verified_res_cnt = resources_qs.filter(verification_status='verified_org').count()

            # Active road hazards & conditions
            blocked_roads_cnt = conditions_qs.filter(
                condition_type='road_status',
                value__in=['blocked', 'flooded', 'landslide', 'closed', 'impassable']
            ).count()
            high_risk_cond_cnt = conditions_qs.filter(risk_score__gte=0.65).count()

            # Active alerts
            crit_alerts_cnt = alerts_qs.filter(severity__in=['critical', 'high']).count()

            # Active allocations in district
            active_allocs_cnt = Allocation.objects.filter(
                match__need__district=dist,
                delivery_status__in=['matched', 'dispatched', 'en_route', 'delayed']
            ).count()
            delayed_allocs_cnt = Allocation.objects.filter(
                match__need__district=dist,
                delivery_status='delayed'
            ).count()

            # Compute Bottleneck Index (0.0 to 10.0 scale)
            # High demand + blocked roads + lack of resources = severe bottleneck
            base_demand_factor = critical_needs_cnt * 2.0 + open_needs_cnt * 0.5
            hazard_factor = blocked_roads_cnt * 3.0 + high_risk_cond_cnt * 1.5
            supply_buffer = max(1, avail_res_cnt)

            raw_index = (base_demand_factor + hazard_factor) / (supply_buffer * 0.8 + 1.0)
            bottleneck_index = round(min(10.0, max(0.0, raw_index)), 2)

            if bottleneck_index >= 7.0 or blocked_roads_cnt > 2:
                connectivity_status = 'severe_bottleneck'
            elif bottleneck_index >= 4.0 or blocked_roads_cnt > 0:
                connectivity_status = 'moderate_stress'
            elif open_needs_cnt > 0:
                connectivity_status = 'stable'
            else:
                connectivity_status = 'optimal'

            # Tally global totals
            total_open_needs += open_needs_cnt
            total_critical_needs += critical_needs_cnt
            total_fulfilled_needs += fulfilled_needs_cnt
            total_resources += avail_res_cnt
            total_blocked_roads += blocked_roads_cnt
            total_active_alerts += crit_alerts_cnt

            district_data.append({
                'district_id': dist.id,
                'name': dist.name,
                'state': dist.state,
                'population': dist.population,
                'centroid': {
                    'latitude': dist.centroid.latitude if dist.centroid and hasattr(dist.centroid, 'latitude') else 24.83,
                    'longitude': dist.centroid.longitude if dist.centroid and hasattr(dist.centroid, 'longitude') else 92.78,
                } if dist.centroid else None,
                'needs': {
                    'total': total_needs_cnt,
                    'open': open_needs_cnt,
                    'critical': critical_needs_cnt,
                    'fulfilled': fulfilled_needs_cnt,
                },
                'resources': {
                    'available_count': avail_res_cnt,
                    'verified_org_count': verified_res_cnt,
                },
                'hazards': {
                    'blocked_roads_count': blocked_roads_cnt,
                    'high_risk_conditions_count': high_risk_cond_cnt,
                    'active_alerts_count': crit_alerts_cnt,
                },
                'logistics': {
                    'active_allocations': active_allocs_cnt,
                    'delayed_allocations': delayed_allocs_cnt,
                },
                'bottleneck_index': bottleneck_index,
                'connectivity_status': connectivity_status,
            })

        # Sort districts by bottleneck index descending so most critical appear first
        district_data.sort(key=lambda d: d['bottleneck_index'], reverse=True)

        return Response({
            'overview': {
                'total_districts_monitored': len(districts),
                'total_open_needs': total_open_needs,
                'total_critical_needs': total_critical_needs,
                'total_fulfilled_needs': total_fulfilled_needs,
                'total_available_resources': total_resources,
                'total_blocked_corridors': total_blocked_roads,
                'total_critical_alerts': total_active_alerts,
                'system_health_status': 'critical_response' if total_critical_needs > 5 or total_blocked_roads > 3 else 'normal_operations',
            },
            'districts': district_data,
        }, status=status.HTTP_200_OK)
