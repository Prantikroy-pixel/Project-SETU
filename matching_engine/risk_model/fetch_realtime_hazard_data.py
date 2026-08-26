"""
SETU Live Hazard & Geospatial Data Engine
========================================
CLI and programmatic utility to extract real-time and historical geo-climatic data:
- lat, lon, date
- rainfall_24 (mm)
- slope (degrees)
- drainage (density km/km²)
- vegetation (NDVI)
- disruption (0 or 1)

Usage:
  # 1. Fetch live real-time metrics across all NER key logistics corridors:
  python fetch_realtime_hazard_data.py --mode realtime --output-csv realtime_hazard.csv --output-xlsx realtime_hazard.xlsx

  # 2. Enrich an existing Bhukosh or custom coordinates CSV:
  python fetch_realtime_hazard_data.py --mode enrich --input-csv input_points.csv --output-csv enriched_hazard.csv

  # 3. Query a single coordinate pair:
  python fetch_realtime_hazard_data.py --lat 26.1445 --lon 91.7362
"""

import argparse
import sys
import os

from realtime_pipeline import (
    RealtimeHazardFetcher,
    generate_realtime_dataset,
    convert_bhukosh_to_standard_dataset,
    export_to_csv,
    export_to_excel,
    NER_CORRIDOR_WAYPOINTS,
    HAS_OPENPYXL
)


def main():
    parser = argparse.ArgumentParser(description="SETU Real-Time Hazard Feature Pipeline & Exporter")
    parser.add_argument("--mode", choices=["realtime", "enrich", "single"], default="realtime",
                        help="Operation mode: 'realtime' (NER corridors), 'enrich' (input CSV), or 'single' (lat/lon pair)")
    parser.add_argument("--input-csv", type=str, default=None, help="Path to input CSV file containing lat, lon, date")
    parser.add_argument("--output-csv", type=str, default="hazard_dataset.csv", help="Path to save output CSV")
    parser.add_argument("--output-xlsx", type=str, default="hazard_dataset.xlsx", help="Path to save output Excel (.xlsx)")
    parser.add_argument("--lat", type=float, default=None, help="Latitude for single point query")
    parser.add_argument("--lon", type=float, default=None, help="Longitude for single point query")

    args = parser.parse_args()

    fetcher = RealtimeHazardFetcher()

    if args.lat is not None and args.lon is not None:
        print(f"[*] Querying real-time hazard features for ({args.lat}, {args.lon})...")
        rain = fetcher.fetch_rainfall_24h(args.lat, args.lon)
        elev_slope = fetcher.fetch_elevation_and_slope(args.lat, args.lon)
        drainage = fetcher.estimate_drainage_density(args.lat, args.lon)
        veg = fetcher.estimate_vegetation_ndvi(args.lat, args.lon, rain)
        disruption = fetcher.determine_disruption(rain, elev_slope["slope"], drainage, veg, elev_slope["elevation"])

        print("\n" + "="*50)
        print("SETU REAL-TIME HAZARD EXTRACTION RESULT:")
        print("="*50)
        print(f"Latitude:        {args.lat}")
        print(f"Longitude:       {args.lon}")
        print(f"Rainfall (24h):  {rain} mm")
        print(f"Slope:           {elev_slope['slope']}°")
        print(f"Elevation:       {elev_slope['elevation']} m")
        print(f"Drainage:        {drainage} km/km²")
        print(f"Vegetation NDVI: {veg}")
        print(f"Disruption Flag: {disruption} ({'DISRUPTED / HIGH HAZARD' if disruption == 1 else 'CLEAR / NORMAL'})")
        print("="*50)
        return

    if args.mode == "realtime":
        print(f"[*] Extracting real-time geo-climatic data for {len(NER_CORRIDOR_WAYPOINTS)} NER corridor points...")
        generate_realtime_dataset(
            output_csv_path=args.output_csv,
            output_xlsx_path=args.output_xlsx
        )
    elif args.mode == "enrich":
        if not args.input_csv or not os.path.exists(args.input_csv):
            print(f"[-] Error: --input-csv file not specified or does not exist: {args.input_csv}")
            sys.exit(1)
        print(f"[*] Enriching input CSV: {args.input_csv}...")
        convert_bhukosh_to_standard_dataset(
            bhukosh_input_csv=args.input_csv,
            output_csv_path=args.output_csv,
            output_xlsx_path=args.output_xlsx
        )


if __name__ == "__main__":
    main()
