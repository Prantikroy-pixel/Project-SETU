"""
Management command to fetch and sync live district and state boundaries into SETU.
Usage:
    python manage.py fetch_live_boundaries
    python manage.py fetch_live_boundaries --state Assam
    python manage.py fetch_live_boundaries --district "Kamrup Metropolitan"
"""

from django.core.management.base import BaseCommand
from core.boundary_service import RealtimeBoundaryFetcher
from core.models import District


class Command(BaseCommand):
    help = "Fetch official GeoJSON administrative boundary polygons from live OpenStreetMap/Nominatim sources"

    def add_arguments(self, parser):
        parser.add_argument('--state', type=str, default=None, help="Filter by state (e.g. Assam, Meghalaya)")
        parser.add_argument('--district', type=str, default=None, help="Fetch boundary for a specific district")

    def handle(self, *args, **options):
        state = options.get('state')
        district_name = options.get('district')
        fetcher = RealtimeBoundaryFetcher()

        if district_name:
            self.stdout.write(self.style.NOTICE(f"Fetching live boundary for district: {district_name}..."))
            data = fetcher.fetch_district_geojson_boundary(district_name, state or "Assam")
            if data and "geometry" in data:
                dist_obj = District.objects.filter(name__iexact=district_name).first()
                if dist_obj:
                    dist_obj.boundary = data["geometry"]
                    dist_obj.save(update_fields=['boundary'])
                    self.stdout.write(self.style.SUCCESS(f"[+] Saved live boundary polygon for: {dist_obj.name}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"[+] Fetched boundary for {district_name}: {data['geometry'].get('type')}"))
            else:
                self.stdout.write(self.style.ERROR(f"[-] Could not retrieve live boundary for {district_name}"))
            return

        self.stdout.write(self.style.NOTICE("Syncing live boundary polygons for all districts in database..."))
        result = fetcher.sync_district_boundaries_to_db(state_filter=state)
        self.stdout.write(self.style.SUCCESS(
            f"Boundary sync complete! Total: {result['total_districts_evaluated']}, "
            f"Synced: {result['boundaries_synced']}, Failed: {result['boundaries_failed']}"
        ))
