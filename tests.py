"""Run locally: python tests.py. No keys or network requests required."""
from __future__ import annotations

import unittest

from activity import build_users, generate_activity, metrics_for_event
from datadog_client import normalize_site


class ActivityTests(unittest.TestCase):
    def test_repeatable_users(self) -> None:
        self.assertEqual(build_users(3, 9), build_users(3, 9))
        self.assertEqual(len({u["user_id"] for u in build_users(25)}), 25)

    def test_event_has_queryable_fields(self) -> None:
        event = generate_activity(build_users(2))
        for field in ("timestamp", "service", "env", "event_type", "user_id", "page", "duration_ms", "status_code"):
            self.assertIn(field, event)
        self.assertEqual(event["service"], "demo-user-activity")

    def test_metrics_never_tag_user_id(self) -> None:
        for event in (generate_activity(build_users(2)) for _ in range(20)):
            for metric in metrics_for_event(event):
                self.assertFalse(any(tag.startswith("user_id:") for tag in metric["tags"]))

    def test_metric_rules(self) -> None:
        login = {"event_type": "login_success", "service": "demo-user-activity", "env": "dev", "region": "ap-south-1", "plan": "pro", "status_code": 200, "duration_ms": 55}
        self.assertEqual(len(metrics_for_event(login)), 2)
        page = {**login, "event_type": "page_view", "page": "/dashboard"}
        self.assertEqual(metrics_for_event(page)[0]["metric"], "demo.user_activity.page_view.count")

    def test_invalid_site_is_rejected(self) -> None:
        self.assertEqual(normalize_site("https://datadoghq.eu/"), "datadoghq.eu")
        with self.assertRaises(ValueError):
            normalize_site("https://api.example.com/a-path")


if __name__ == "__main__":
    unittest.main(verbosity=2)
