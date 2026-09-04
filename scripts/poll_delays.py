"""
Step 2 (v2): Poll VBB's live GTFS-Realtime feed and update a rolling delay
SUMMARY -- not a raw ever-growing log.

Why the change: logging every single stop update, every 10 minutes, forever,
eventually produces a file too large for GitHub (100MB limit) and isn't
actually what we need. What we actually want for training is: "for this
route, on this day of week, at this hour, what's the typical delay?" So
instead of appending forever, we keep ONE row per (route_id, day_of_week,
hour) and update its running average + count each time we poll. The file
size stays roughly constant no matter how many weeks this runs for.

Requires: pip install gtfs-realtime-bindings

Run manually to test:
    python scripts/poll_delays.py
"""

import csv
import datetime
from pathlib import Path

import requests
from google.transit import gtfs_realtime_pb2
from zoneinfo import ZoneInfo

FEED_URL = "https://production.gtfsrt.vbb.de/data"
SUMMARY_FILE = Path(__file__).resolve().parent.parent / "data" / "delay_summary.csv"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

HEADERS = {
    "User-Agent": "student-project-transit-delay-predictor (contact: tirth)"
}

FIELDNAMES = ["route_id", "day_of_week", "hour", "sample_count", "avg_delay_seconds", "max_delay_seconds"]


def poll_once():
    resp = requests.get(FEED_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    now = datetime.datetime.now(BERLIN_TZ)
    day_of_week = now.strftime("%A")
    hour = now.hour

    observations = []  # (route_id, delay_seconds)

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update
        route_id = trip.trip.route_id or "unknown"

        for stop_time_update in trip.stop_time_update:
            delay_seconds = None
            if stop_time_update.HasField("arrival") and stop_time_update.arrival.HasField("delay"):
                delay_seconds = stop_time_update.arrival.delay
            elif stop_time_update.HasField("departure") and stop_time_update.departure.HasField("delay"):
                delay_seconds = stop_time_update.departure.delay

            if delay_seconds is None:
                continue

            observations.append((route_id, delay_seconds))

    return day_of_week, hour, observations


def load_summary():
    """Load existing summary into a dict keyed by (route_id, day_of_week, hour)."""
    summary = {}
    if SUMMARY_FILE.exists():
        with open(SUMMARY_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["route_id"], row["day_of_week"], int(row["hour"]))
                summary[key] = {
                    "sample_count": int(row["sample_count"]),
                    "avg_delay_seconds": float(row["avg_delay_seconds"]),
                    "max_delay_seconds": float(row["max_delay_seconds"]),
                }
    return summary


def update_summary(summary, day_of_week, hour, observations):
    for route_id, delay_seconds in observations:
        key = (route_id, day_of_week, hour)
        if key not in summary:
            summary[key] = {"sample_count": 0, "avg_delay_seconds": 0.0, "max_delay_seconds": delay_seconds}

        entry = summary[key]
        n = entry["sample_count"]
        entry["avg_delay_seconds"] = (entry["avg_delay_seconds"] * n + delay_seconds) / (n + 1)
        entry["sample_count"] = n + 1
        entry["max_delay_seconds"] = max(entry["max_delay_seconds"], delay_seconds)

    return summary


def save_summary(summary):
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for (route_id, day_of_week, hour), stats in summary.items():
            writer.writerow({
                "route_id": route_id,
                "day_of_week": day_of_week,
                "hour": hour,
                "sample_count": stats["sample_count"],
                "avg_delay_seconds": round(stats["avg_delay_seconds"], 1),
                "max_delay_seconds": stats["max_delay_seconds"],
            })


if __name__ == "__main__":
    try:
        day_of_week, hour, observations = poll_once()
        if not observations:
            print("No real-time delay data available in this poll (feed may have limited coverage right now).")
        else:
            summary = load_summary()
            summary = update_summary(summary, day_of_week, hour, observations)
            save_summary(summary)
            print(f"Updated summary with {len(observations)} new observations. "
                  f"Summary now has {len(summary)} route/day/hour combinations.")
    except requests.exceptions.RequestException as e:
        print(f"Could not reach the feed this time: {e}")
