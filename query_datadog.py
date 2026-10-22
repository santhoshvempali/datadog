"""Query logs or v1 time-series metrics from Datadog."""
from __future__ import annotations

import argparse
import json

from datadog_client import DatadogClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    logs = subcommands.add_parser("logs")
    logs.add_argument("--query", default="service:demo-user-activity env:dev")
    logs.add_argument("--minutes", type=int, default=60)
    logs.add_argument("--limit", type=int, default=20)
    metric = subcommands.add_parser("metric")
    metric.add_argument("--metric", default="demo.user_activity.login.count")
    metric.add_argument("--minutes", type=int, default=60)
    args = parser.parse_args()
    if args.minutes < 1:
        parser.error("minutes must be positive")
    client = DatadogClient()
    if args.command == "logs":
        result = client.search_logs(args.query, args.minutes, args.limit)
    else:
        query = f"sum:{args.metric}{{service:demo-user-activity,env:dev}}.as_count()"
        result = client.query_metric_v1(query, args.minutes)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
