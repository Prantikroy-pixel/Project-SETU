import requests

# Test multiple Overpass endpoints and OSM endpoints with proper headers
endpoints = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

query = """[out:json][timeout:15];
(
  node["amenity"="hospital"](26.10,91.70,26.25,91.85);
);
out body 5;"""

headers = {
    "User-Agent": "SETU-Disaster-Management-Platform/1.0 (contact: admin@setu.org)",
    "Accept": "application/json",
}

for ep in endpoints:
    print(f"Testing endpoint: {ep}")
    try:
        r = requests.post(ep, data={"data": query}, headers=headers, timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            elements = data.get("elements", [])
            print(f"  SUCCESS! Found {len(elements)} elements:")
            for el in elements:
                name = el.get("tags", {}).get("name")
                print(f"    - {name} ({el.get('lat')}, {el.get('lon')})")
            break
        else:
            print(f"  Response: {r.text[:150]}")
    except Exception as e:
        print(f"  Failed: {e}")

# Also test Nominatim OpenStreetMap Search API for live NER hospitals & checkposts
print("\nTesting Nominatim OpenStreetMap Search API:")
nom_url = "https://nominatim.openstreetmap.org/search"
nom_params = {
    "q": "hospital in Guwahati",
    "format": "json",
    "limit": 5,
    "addressdetails": 1
}
nom_headers = {
    "User-Agent": "SETU-Logistics-Platform/1.0 (admin@setu.org)"
}
try:
    r_nom = requests.get(nom_url, params=nom_params, headers=nom_headers, timeout=10)
    print(f"Nominatim Status: {r_nom.status_code}")
    if r_nom.status_code == 200:
        results = r_nom.json()
        print(f"Retrieved {len(results)} live real-world hospitals via Nominatim:")
        for res in results:
            print(f"  - {res.get('name') or res.get('display_name')} | Lat: {res.get('lat')}, Lon: {res.get('lon')}")
except Exception as e:
    print(f"Nominatim Failed: {e}")
