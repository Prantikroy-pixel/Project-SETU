"""
Verification test for new Boundaries and Institutions APIs.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from core.views import InstitutionViewSet, BorderBoundaryView, BorderProximityView, RouteBorderAnalysisView

factory = APIRequestFactory()

print("--- 1. Testing Institutions ViewSet ---")
view = InstitutionViewSet.as_view({'get': 'list'})
req = factory.get('/api/institutions/?category=hospital')
res = view(req)
print(f"Status: {res.status_code}, Hospitals found: {len(res.data.get('results', res.data))}")
sample = (res.data.get('results') or res.data)[0]
print(f"Sample Hospital: {sample['name']} ({sample['state']}), Beds: {sample['bed_capacity']}")

print("\n--- 2. Testing NER Borders View ---")
b_view = BorderBoundaryView.as_view()
req2 = factory.get('/api/boundaries/ner-borders/')
res2 = b_view(req2)
print(f"Status: {res2.status_code}, Checkpoints: {res2.data['total_checkpoints']}, International Borders: {len(res2.data['international_borders'])}")

print("\n--- 3. Testing Border Proximity Geofence (Dawki Meghalaya-Bangladesh) ---")
p_view = BorderProximityView.as_view()
req3 = factory.get('/api/boundaries/check-proximity/?lat=25.1842&lon=92.0286&radius_km=15')
res3 = p_view(req3)
print(f"Status: {res3.status_code}")
print(f"Is near border: {res3.data['is_near_border']}, Distance: {res3.data['distance_to_nearest_checkpoint_km']} km")
print(f"Nearest checkpoint: {res3.data['nearest_checkpoint']['name']}")
print(f"Regulatory notes: {res3.data['regulatory_notes']}")

print("\n--- 4. Testing Route Border Analysis (Guwahati to Shillong to Dawki to Silchar) ---")
r_view = RouteBorderAnalysisView.as_view()
route_payload = {
    "route_points": [
        {"lat": 26.1445, "lon": 91.7362}, # Guwahati
        {"lat": 26.0964, "lon": 91.8683}, # Jorabat (Assam-Meghalaya)
        {"lat": 25.5788, "lon": 91.8933}, # Shillong
        {"lat": 25.1842, "lon": 92.0286}, # Dawki (India-Bangladesh)
        {"lat": 24.8333, "lon": 92.7789}  # Silchar
    ]
}
req4 = factory.post('/api/boundaries/analyze-route/', data=route_payload, format='json')
res4 = r_view(req4)
print(f"Status: {res4.status_code}")
print(f"Border Checkpoints on Route: {res4.data['total_border_checkpoints_on_route']}")
print(f"Interstate Crossings: {res4.data['interstate_crossings']}")
print(f"International Buffer Vicinities: {res4.data['international_border_vicinities']}")
for cp in res4.data['checkpoints']:
    print(f" - {cp['checkpoint']['name']} ({cp['checkpoint']['border_with']}): {cp['distance_to_route_km']} km away")

print("\n[+] All new APIs verified and operational!")
