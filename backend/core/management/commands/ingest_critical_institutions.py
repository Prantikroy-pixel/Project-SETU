"""
Management command to ingest critical institutions, hospitals, and government sectors into SETU.
Usage:
    python manage.py ingest_critical_institutions
    python manage.py ingest_critical_institutions --district Cachar --state Assam
    python manage.py ingest_critical_institutions --no-osm
"""

from django.core.management.base import BaseCommand
from core.institution_service import InstitutionIngestionService


class Command(BaseCommand):
    help = "Ingests hospitals, government sectors, disaster hubs, and shelters from live OpenStreetMap and master rosters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-osm",
            action="store_true",
            help="Skip live OpenStreetMap Overpass queries and use master roster only."
        )
        parser.add_argument(
            "--district",
            type=str,
            default=None,
            help="Filter / fetch live institutions for a specific district (e.g. Cachar, Kamrup Metropolitan)"
        )
        parser.add_argument(
            "--state",
            type=str,
            default="Assam",
            help="State name for district scoping (default: Assam)"
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Starting Critical Institutions & Government Sectors Ingestion..."))

        include_osm = not options.get("no_osm", False)
        target_district = options.get("district")
        state_name = options.get("state")

        service = InstitutionIngestionService()
        stats = service.sync_all_institutions_to_db(
            include_live_osm=include_osm,
            target_district=target_district,
            state_name=state_name
        )

        self.stdout.write(self.style.SUCCESS(
            f"[+] Successfully Ingested Critical Institutions:\n"
            f"    - Institutions Created: {stats['institutions_created']}\n"
            f"    - Institutions Updated: {stats['institutions_updated']}\n"
            f"    - Strategic Resources Auto-Generated: {stats['resources_auto_generated']}\n"
            f"    - Total Processed: {stats.get('total_processed', 0)}"
        ))
