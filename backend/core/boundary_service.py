"""
SETU Interstate & International Boundary Tracking Engine
========================================================
Integrates public geospatial APIs (Nominatim OpenStreetMap, Overpass API, Bhuvan)
to fetch and track real-time international borders, interstate boundaries, and
district polygon geometries across the North Eastern Region (NER) and India.

Key Capabilities:
1. Real-Time District Boundary Fetching:
   - Queries live OpenStreetMap & Nominatim for official district GeoJSON polygons.
   - Populates and updates District.boundary with high-fidelity MultiPolygon geometries.

2. State & Regional Boundary Ingestion:
   - Extracts complete GeoJSON boundaries for all 8 NER states.

3. International & Interstate Border Checkpoints:
   - Live border proximity geofencing, regulatory ILP validation, and convoy route analysis.
"""

import math
import time
import json
import requests
from typing import List, Dict, Any, Optional, Tuple

# In-memory TTL cache for live boundary geometries to optimize throughput
_BOUNDARY_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache per boundary


# Major Strategic Border Checkpoints & Integrated Check Posts (ICPs) across NER
NER_BORDER_CHECKPOINTS = [
    # International Checkpoints (ICPs / Land Customs Stations)
    {
        "id": "ICP-DAWKI",
        "name": "Dawki Integrated Check Post (ICP)",
        "type": "international_border",
        "border_with": "Bangladesh",
        "state": "Meghalaya",
        "lat": 25.1842,
        "lon": 92.0286,
        "regulatory_clearance": "International Land Port / Customs & Immigration",
        "description": "Primary trade and transit gateway between Meghalaya (India) and Tamabil (Bangladesh)."
    },
    {
        "id": "ICP-MOREH",
        "name": "Moreh Integrated Check Post (ICP)",
        "type": "international_border",
        "border_with": "Myanmar",
        "state": "Manipur",
        "lat": 24.2494,
        "lon": 94.3039,
        "regulatory_clearance": "India-Myanmar Asian Highway 1 (AH-1) Gateway",
        "description": "Crucial India-Myanmar border trade and humanitarian transit hub."
    },
    {
        "id": "ICP-SUTARKANDI",
        "name": "Sutarkandi Land Customs Station (LCS)",
        "type": "international_border",
        "border_with": "Bangladesh",
        "state": "Assam",
        "lat": 24.8711,
        "lon": 92.2472,
        "regulatory_clearance": "Assam-Bangladesh Border Customs Gate (Karimganj)",
        "description": "Barak Valley international trade link with Sheola (Bangladesh)."
    },
    {
        "id": "ICP-SRIMANTAPUR",
        "name": "Srimantapur ICP (Sonamura)",
        "type": "international_border",
        "border_with": "Bangladesh",
        "state": "Tripura",
        "lat": 23.4758,
        "lon": 91.2656,
        "regulatory_clearance": "Tripura-Bangladesh Land Port (Comilla axis)",
        "description": "Second largest ICP in Tripura after Agartala-Akhaura."
    },
    {
        "id": "ICP-AKHAURA",
        "name": "Agartala-Akhaura Integrated Check Post",
        "type": "international_border",
        "border_with": "Bangladesh",
        "state": "Tripura",
        "lat": 23.8569,
        "lon": 91.2581,
        "regulatory_clearance": "Tripura International Rail & Road Gateway",
        "description": "High-capacity transit port connecting Agartala directly to Dhaka."
    },
    {
        "id": "ICP-JAIGAON",
        "name": "Jaigaon-Phuentsholing Gateway",
        "type": "international_border",
        "border_with": "Bhutan",
        "state": "West Bengal / Assam Border",
        "lat": 26.8583,
        "lon": 89.3789,
        "regulatory_clearance": "India-Bhutan Primary Commercial Lifeline",
        "description": "Main overland commercial and transit portal into Bhutan."
    },
    {
        "id": "ICP-DARANGA",
        "name": "Daranga Land Customs Station (Baksa)",
        "type": "international_border",
        "border_with": "Bhutan",
        "state": "Assam",
        "lat": 26.8042,
        "lon": 91.5303,
        "regulatory_clearance": "Assam-Bhutan Border Port (Samdrup Jongkhar axis)",
        "description": "Direct overland road connector between Bodoland (Assam) and Eastern Bhutan."
    },
    {
        "id": "ICP-ZOKHAWTHAR",
        "name": "Zokhawthar Border Trade Centre (Champhai)",
        "type": "international_border",
        "border_with": "Myanmar",
        "state": "Mizoram",
        "lat": 23.3644,
        "lon": 93.3325,
        "regulatory_clearance": "India-Myanmar Border Trade Post (Rih Dil axis)",
        "description": "Eastern Mizoram border crossing over the Harhva/Tiau river."
    },

    # Major Strategic Interstate Checkposts & Gateways
    {
        "id": "CHK-JORABAT",
        "name": "Jorabat Inter-State Gateway (NH-6)",
        "type": "interstate_border",
        "border_with": "Assam-Meghalaya",
        "state": "Assam / Meghalaya",
        "lat": 26.0964,
        "lon": 91.8683,
        "regulatory_clearance": "Inter-State Heavy Vehicle & Relief Corridor Gate",
        "description": "Primary mountain road gateway connecting Guwahati (Assam) to Shillong and Barak Valley."
    },
    {
        "id": "CHK-BANDARDEWA",
        "name": "Banderdewa Checkpost (NH-415)",
        "type": "interstate_border",
        "border_with": "Assam-Arunachal Pradesh",
        "state": "Assam / Arunachal Pradesh",
        "lat": 27.1264,
        "lon": 93.8189,
        "regulatory_clearance": "Inner Line Permit (ILP) & State Entry Checkpoint",
        "description": "Major arterial transit gate connecting Lakhimpur (Assam) with Itanagar (Capital of Arunachal)."
    },
    {
        "id": "CHK-DIMAPUR",
        "name": "New Field Checkpost / Dimapur Gate (NH-29)",
        "type": "interstate_border",
        "border_with": "Assam-Nagaland",
        "state": "Assam / Nagaland",
        "lat": 25.9231,
        "lon": 93.7153,
        "regulatory_clearance": "Inner Line Permit (ILP) & Commercial Freight Gate",
        "description": "Vital lifeline connecting Karbi Anglong / Golaghat (Assam) to Dimapur and Kohima."
    },
    {
        "id": "CHK-VAIRENGTE",
        "name": "Vairengte Inter-State Checkpoint (NH-306)",
        "type": "interstate_border",
        "border_with": "Assam-Mizoram",
        "state": "Assam / Mizoram",
        "lat": 24.5061,
        "lon": 92.7667,
        "regulatory_clearance": "Inner Line Permit (ILP) & Essential Supplies Gate",
        "description": "The sole national highway supply corridor into Mizoram from Cachar (Assam)."
    },
    {
        "id": "CHK-CHURAIBARI",
        "name": "Churaibari Inter-State Checkpost (NH-8)",
        "type": "interstate_border",
        "border_with": "Assam-Tripura",
        "state": "Assam / Tripura",
        "lat": 24.5264,
        "lon": 92.2464,
        "regulatory_clearance": "State Revenue, Tax & Logistics Clearance Gate",
        "description": "Single national highway road connector joining Tripura to mainland Assam."
    },
    {
        "id": "CHK-JIRIBAM",
        "name": "Jiribam Inter-State Checkpost (NH-37)",
        "type": "interstate_border",
        "border_with": "Assam-Manipur",
        "state": "Assam / Manipur",
        "lat": 24.8028,
        "lon": 93.1231,
        "regulatory_clearance": "Inner Line Permit (ILP) & Western Highway Gate",
        "description": "Western lifeline linking Cachar (Assam) across the Jiri River into Imphal Valley."
    },
    {
        "id": "CHK-RANGPO",
        "name": "Rangpo Border Checkpost (NH-10)",
        "type": "interstate_border",
        "border_with": "West Bengal-Sikkim",
        "state": "West Bengal / Sikkim",
        "lat": 27.1764,
        "lon": 88.5283,
        "regulatory_clearance": "Sikkim State Entry, Tourist & Logistics Permitted Gate",
        "description": "Strategic entry into Sikkim across the Teesta River from Siliguri/Kalimpong."
    },
    {
        "id": "CHK-SRIRAMPUR",
        "name": "Srirampur Inter-State Gateway (NH-27)",
        "type": "interstate_border",
        "border_with": "West Bengal-Assam",
        "state": "West Bengal / Assam",
        "lat": 26.4789,
        "lon": 89.8986,
        "regulatory_clearance": "Gateway to Entire North East (Siliguri Corridor / Chicken's Neck)",
        "description": "The critical overland neck connecting all 8 North Eastern states with the rest of India."
    }
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class RealtimeBoundaryFetcher:
    """
    Direct Real-Time Administrative Boundary Ingestion Engine.
    Queries Nominatim and OpenStreetMap Overpass APIs for official District and State
    GeoJSON polygon boundaries.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter"
    ]

    def __init__(self, timeout_sec: int = 10):
        self.timeout = timeout_sec
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SETU-Boundary-Fetcher/2.0 (NER-Disaster-Platform)"
        })

    def fetch_district_geojson_boundary(
        self,
        district_name: str,
        state_name: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches the official GeoJSON boundary polygon for a district from live OpenStreetMap/Nominatim.
        Returns:
            Dict containing geometry (Polygon/MultiPolygon GeoJSON), bbox, and metadata.
        """
        cache_key = f"dist_{district_name.lower().strip()}_{state_name.lower().strip()}"
        now = time.time()
        if cache_key in _BOUNDARY_CACHE:
            ts, data = _BOUNDARY_CACHE[cache_key]
            if now - ts < CACHE_TTL_SECONDS:
                return data

        query_terms = [
            f"{district_name} District, {state_name}, India" if state_name else f"{district_name} District, India",
            f"{district_name}, {state_name}, India" if state_name else f"{district_name}, India",
            f"{district_name}, Assam, India"
        ]

        for query_str in query_terms:
            try:
                params = {
                    "q": query_str,
                    "format": "geojson",
                    "polygon_geojson": 1,
                    "limit": 1
                }
                resp = self.session.get(self.NOMINATIM_URL, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    geojson_data = resp.json()
                    features = geojson_data.get("features", [])
                    if features:
                        feature = features[0]
                        geometry = feature.get("geometry", {})
                        geom_type = geometry.get("type", "")

                        if geom_type in ["Polygon", "MultiPolygon"]:
                            result = {
                                "district_name": district_name,
                                "state": state_name,
                                "display_name": feature.get("properties", {}).get("display_name", query_str),
                                "geometry_type": geom_type,
                                "geometry": geometry,
                                "bbox": feature.get("bbox", []),
                                "source": "openstreetmap_nominatim_live",
                                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            }
                            _BOUNDARY_CACHE[cache_key] = (now, result)
                            return result
            except Exception:
                continue

        # Overpass fallback query for boundary relation
        try:
            overpass_query = f"""
            [out:json][timeout:{self.timeout}];
            relation["boundary"="administrative"]["admin_level"="5"]["name"~"{district_name}",i];
            out geom;
            """
            for op_url in self.OVERPASS_URLS:
                try:
                    op_resp = self.session.post(op_url, data={"data": overpass_query}, timeout=self.timeout)
                    if op_resp.status_code == 200:
                        elements = op_resp.json().get("elements", [])
                        if elements:
                            rel = elements[0]
                            # Extract coordinates from member ways
                            coords = []
                            for member in rel.get("members", []):
                                if member.get("type") == "way" and "geometry" in member:
                                    for pt in member["geometry"]:
                                        coords.append([pt["lon"], pt["lat"]])
                            if len(coords) >= 4:
                                polygon_geom = {
                                    "type": "Polygon",
                                    "coordinates": [coords]
                                }
                                result = {
                                    "district_name": district_name,
                                    "state": state_name,
                                    "display_name": f"{district_name} District",
                                    "geometry_type": "Polygon",
                                    "geometry": polygon_geom,
                                    "source": "openstreetmap_overpass_live",
                                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                                }
                                _BOUNDARY_CACHE[cache_key] = (now, result)
                                return result
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def fetch_state_geojson_boundary(self, state_name: str) -> Optional[Dict[str, Any]]:
        """Fetches the official GeoJSON boundary polygon for a State in India."""
        cache_key = f"state_{state_name.lower().strip()}"
        now = time.time()
        if cache_key in _BOUNDARY_CACHE:
            ts, data = _BOUNDARY_CACHE[cache_key]
            if now - ts < CACHE_TTL_SECONDS:
                return data

        try:
            params = {
                "q": f"{state_name}, India",
                "format": "geojson",
                "polygon_geojson": 1,
                "limit": 1
            }
            resp = self.session.get(self.NOMINATIM_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                features = resp.json().get("features", [])
                if features:
                    feat = features[0]
                    geom = feat.get("geometry", {})
                    if geom.get("type") in ["Polygon", "MultiPolygon"]:
                        result = {
                            "state_name": state_name,
                            "display_name": feat.get("properties", {}).get("display_name", f"{state_name}, India"),
                            "geometry": geom,
                            "bbox": feat.get("bbox", []),
                            "source": "openstreetmap_nominatim_live"
                        }
                        _BOUNDARY_CACHE[cache_key] = (now, result)
                        return result
        except Exception:
            pass
        return None

    def sync_district_boundaries_to_db(self, state_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Queries all District models in the database and updates their `boundary` field
        with live GeoJSON polygons fetched from OpenStreetMap / Nominatim.
        """
        # Lazy import of models
        from .models import District

        qs = District.objects.all()
        if state_filter:
            qs = qs.filter(state__iexact=state_filter)

        synced_count = 0
        failed_count = 0
        results = []

        for dist in qs:
            print(f"[*] Fetching live boundary polygon for: {dist.name} ({dist.state})...")
            boundary_data = self.fetch_district_geojson_boundary(dist.name, dist.state)

            if boundary_data and "geometry" in boundary_data:
                geom = boundary_data["geometry"]
                dist.boundary = geom
                dist.save(update_fields=['boundary'])
                synced_count += 1
                results.append({
                    "district_id": dist.id,
                    "district_name": dist.name,
                    "state": dist.state,
                    "status": "synced",
                    "geometry_type": geom.get("type", "Polygon")
                })
                print(f"[+] Successfully populated boundary for {dist.name} ({geom.get('type')})")
            else:
                failed_count += 1
                results.append({
                    "district_id": dist.id,
                    "district_name": dist.name,
                    "state": dist.state,
                    "status": "failed_to_fetch"
                })
            time.sleep(0.2)  # Respect open API rate limits

        return {
            "total_districts_evaluated": qs.count(),
            "boundaries_synced": synced_count,
            "boundaries_failed": failed_count,
            "details": results
        }


class BorderTrackingService:
    """
    Service for live OpenStreetMap administrative boundary relations and
    interstate/international border geofencing & convoy corridor analysis.
    """

    def __init__(self, timeout_sec: int = 8):
        self.timeout = timeout_sec
        self.boundary_fetcher = RealtimeBoundaryFetcher(timeout_sec=timeout_sec)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SETU-Border-Tracking-Engine/2.0 (NER-Disaster-Logistics)"
        })

    def fetch_live_osm_boundaries(self, bbox: Tuple[float, float, float, float], admin_level: int = 4) -> List[Dict[str, Any]]:
        """
        Queries live OpenStreetMap Overpass API for administrative boundary relations.
        admin_level=2: International borders
        admin_level=4: Interstate boundaries (Indian State borders)
        admin_level=5: District boundaries
        """
        min_lat, min_lon, max_lat, max_lon = bbox
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          relation["boundary"="administrative"]["admin_level"="{admin_level}"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out tags;
        """
        for url in RealtimeBoundaryFetcher.OVERPASS_URLS:
            try:
                resp = self.session.post(url, data={"data": query}, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    elements = data.get("elements", [])
                    boundaries = []
                    for el in elements:
                        tags = el.get("tags", {})
                        boundaries.append({
                            "osm_id": el.get("id"),
                            "name": tags.get("name", tags.get("name:en", "Unnamed Boundary")),
                            "admin_level": admin_level,
                            "border_type": "international" if admin_level == 2 else "interstate",
                            "state_or_country": tags.get("is_in:state", tags.get("is_in:country", tags.get("name", "")))
                        })
                    return boundaries
            except Exception:
                continue

        return []

    def check_point_border_proximity(self, lat: float, lon: float, threshold_km: float = 20.0) -> Dict[str, Any]:
        """
        Determines if a location is near an international border or interstate boundary,
        identifying the closest strategic checkpost and special regulatory requirements.
        """
        closest_checkpoint = None
        min_dist = float("inf")

        for cp in NER_BORDER_CHECKPOINTS:
            dist = haversine_distance_km(lat, lon, cp["lat"], cp["lon"])
            if dist < min_dist:
                min_dist = dist
                closest_checkpoint = cp

        is_near_border = min_dist <= threshold_km
        is_international = closest_checkpoint["type"] == "international_border" if closest_checkpoint else False

        regulatory_notes = []
        if is_near_border and closest_checkpoint:
            regulatory_notes.append(f"Located {min_dist:.1f} km from {closest_checkpoint['name']}.")
            if "Inner Line Permit" in closest_checkpoint.get("regulatory_clearance", ""):
                regulatory_notes.append("ILP (Inner Line Permit) / State Travel Pass check required for commercial fleet.")
            if is_international:
                regulatory_notes.append("International Border Security Buffer (BSF / Assam Rifles jurisdiction).")

        return {
            "latitude": lat,
            "longitude": lon,
            "is_near_border": is_near_border,
            "border_type": closest_checkpoint["type"] if closest_checkpoint else "none",
            "distance_to_nearest_checkpoint_km": round(min_dist, 2),
            "nearest_checkpoint": closest_checkpoint,
            "requires_interstate_clearance": is_near_border,
            "requires_international_clearance": is_near_border and is_international,
            "regulatory_notes": regulatory_notes
        }

    def analyze_route_crossings(self, route_points: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Analyzes a multi-waypoint logistics route to detect interstate border crossings,
        international border proximities, and security checkpoints along the way.
        """
        flagged_checkpoints = []
        seen_cp_ids = set()

        for pt in route_points:
            lat = pt.get("lat") or pt.get("latitude")
            lon = pt.get("lon") or pt.get("longitude")
            if lat is None or lon is None:
                continue

            for cp in NER_BORDER_CHECKPOINTS:
                if cp["id"] in seen_cp_ids:
                    continue
                dist = haversine_distance_km(lat, lon, cp["lat"], cp["lon"])
                if dist <= 12.0:
                    seen_cp_ids.add(cp["id"])
                    flagged_checkpoints.append({
                        "checkpoint": cp,
                        "distance_to_route_km": round(dist, 2)
                    })

        interstate_count = sum(1 for c in flagged_checkpoints if c["checkpoint"]["type"] == "interstate_border")
        intl_count = sum(1 for c in flagged_checkpoints if c["checkpoint"]["type"] == "international_border")

        return {
            "total_border_checkpoints_on_route": len(flagged_checkpoints),
            "interstate_crossings": interstate_count,
            "international_border_vicinities": intl_count,
            "checkpoints": flagged_checkpoints,
            "route_has_permits_required": any("Inner Line Permit" in c["checkpoint"].get("regulatory_clearance", "") for c in flagged_checkpoints)
        }

    def get_all_checkpoints(self) -> List[Dict[str, Any]]:
        """Returns all registered NER interstate and international checkpoints."""
        return NER_BORDER_CHECKPOINTS
