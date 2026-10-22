"""Generate fake user activity and optionally send it to Datadog."""
from __future__ import annotations

import argparse
import json
import random
import time

from activity import build_users, generate_activity, metrics_for_event
from datadog_client import DatadogClient


def run_batch(events: int, users: list[dict], dry_run: bool, seed: int) -> None:
    rng = random.Random(seed)
    activities = [generate_activity(users, rng) for _ in range(events)]
    metric_events = [metric for activity in activities for metric in metrics_for_event(activity)]
    print(json.dumps({"events": activities, "metric_points": metric_events}, indent=2))
    if dry_run:
        print("Dry run complete. No data was sent to Datadog.")
        return
    client = DatadogClient()
    client.send_logs(activities)
    client.submit_metrics(metric_events)
    print(f"Sent {len(activities)} logs and {len(metric_events)} metric points to Datadog.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=10, help="Activities per batch")
    parser.add_argument("--users", type=int, default=25, help="Number of fake users")
    parser.add_argument("--seed", type=int, default=42, help="Repeatable random seed")
    parser.add_argument("--dry-run", action="store_true", help="Print data but do not contact Datadog")
    parser.add_argument("--repeat", action="store_true", help="Keep generating batches")
    parser.add_argument("--interval", type=float, default=10, help="Seconds between repeat batches")
    args = parser.parse_args()
    if args.events < 1 or args.users < 1 or args.interval <= 0:
        parser.error("events/users must be positive and interval must be greater than zero")
    users = build_users(args.users, args.seed)
    batch = 0
    while True:
        run_batch(args.events, users, args.dry_run, args.seed + batch)
        batch += 1
        if not args.repeat:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
