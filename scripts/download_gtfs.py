"""
Step 1: Download VBB's static GTFS schedule data and take a first look at it.

GTFS data comes as a zip file containing several .txt files (which are just
CSVs), e.g.:
  - stops.txt    -> every bus/train stop, with name + lat/lon
  - routes.txt   -> every route (bus/train line), with its name and type
  - trips.txt    -> individual scheduled trips on each route
  - stop_times.txt -> the scheduled arrival time at each stop for each trip

Run this from the project root:
    python scripts/download_gtfs.py
"""

import zipfile
import io
import requests
import pandas as pd
from pathlib import Path

GTFS_URL = "https://www.vbb.de/fileadmin/user_upload/VBB/Dokumente/API-Datensaetze/gtfs-mastscharf/GTFS.zip"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw_gtfs"


def download_and_extract():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading GTFS feed from {GTFS_URL} ...")
    resp = requests.get(GTFS_URL, timeout=120)
    resp.raise_for_status()

    print("Extracting files...")
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        z.extractall(OUT_DIR)

    print(f"Done. Files saved to {OUT_DIR}")


def peek_at_data():
    routes = pd.read_csv(OUT_DIR / "routes.txt")
    stops = pd.read_csv(OUT_DIR / "stops.txt")

    print("\n--- Sample routes ---")
    print(routes[["route_id", "route_short_name", "route_type"]].head(10))

    print(f"\nTotal routes: {len(routes)}")
    print(f"Total stops: {len(stops)}")


if __name__ == "__main__":
    download_and_extract()
    peek_at_data()
