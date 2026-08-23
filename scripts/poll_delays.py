"""
Step 2: Poll VBB's live GTFS-Realtime feed and log scheduled vs. actual times.

NOTE: As of writing, VBB's real-time feed has limited/incomplete data
coverage (a known ongoing issue on their end since June 2026). This script
is written to handle that gracefully -- it logs whatever real delay data IS
available each time it runs, and simply skips trips with no real-time info,
rather than crashing. Over enough polls, you'll still build up a real dataset.

Requires: pip install gtfs-realtime-bindings

Run manually to test:
    python scripts/poll_delays.py
"""

import csv
import datetime
from pathlib import Path

import requests
from google.transit import gtfs_realtime_pb2

FEED_URL = "https://production.gtfsrt.vbb.de/data"
OUT_FILE = Path(__file__).resolve().parent.parent / "data" / "delay_log.csv"

HEADERS = {
    "User-Agent": "student-project-transit-delay-predictor (contact: tirth)"
}


def poll_once():
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    rows = []
    now = datetime.datetime.now()

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update
        route_id = trip.trip.route_id or "unknown"

        for stop_time_update in trip.stop_time_update:
            stop_id = stop_time_update.stop_id

            # A delay in seconds may be attached to arrival or departure.
            delay_seconds = None
            if stop_time_update.HasField("arrival") and stop_time_update.arrival.HasField("delay"):
                delay_seconds = stop_time_update.arrival.delay
            elif stop_time_update.HasField("departure") and stop_time_update.departure.HasField("delay"):
                delay_seconds = stop_time_update.departure.delay

            if delay_seconds is None:
                continue  # no real-time info for this stop right now, skip it

            rows.append({
                "logged_at": now.isoformat(timespec="seconds"),
                "day_of_week": now.strftime("%A"),
                "hour": now.hour,
                "route_id": route_id,
                "stop_id": stop_id,
                "delay_seconds": delay_seconds,
            })

    return rows


def append_to_csv(rows):
    if not rows:
        print("No real-time delay data available in this poll (feed may have limited coverage right now).")
        return

    file_exists = OUT_FILE.exists()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    print(f"Logged {len(rows)} delay records to {OUT_FILE}")


if __name__ == "__main__":
    try:
        rows = poll_once()
        append_to_csv(rows)
    except requests.exceptions.RequestException as e:
        print(f"Could not reach the feed this time: {e}")
