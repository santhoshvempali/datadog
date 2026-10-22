"""Fake user and activity-event generation for the Datadog demo."""
from __future__ import annotations

from datetime import datetime, timezone
import random
import uuid

PAGES = ("/", "/dashboard", "/profile", "/reports", "/settings", "/billing")
REGIONS = ("ap-south-1", "us-east-1", "eu-west-1")
PLANS = ("free", "pro", "enterprise")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_users(count: int = 25, seed: int = 42) -> list[dict]:
    if count < 1:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    return [
        {
            "user_id": f"user-{number:04d}",
            "email": f"demo.user{number:04d}@example.test",
            "plan": rng.choices(PLANS, weights=(65, 28, 7))[0],
            "region": rng.choice(REGIONS),
        }
        for number in range(1, count + 1)
    ]


def generate_activity(users: list[dict], rng: random.Random | None = None) -> dict:
    """Return a structured login or page-view event. No real personal data."""
    if not users:
        raise ValueError("users cannot be empty")
    rng = rng or random.Random()
    user = rng.choice(users)
    event_type = rng.choices(("login_success", "login_failure", "page_view"), weights=(28, 4, 68))[0]
    status_code = 401 if event_type == "login_failure" else (500 if rng.random() < 0.03 else 200)
    event = {
        "timestamp": utc_timestamp(),
        "service": "demo-user-activity",
        "env": "dev",
        "event_type": event_type,
        "event_id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "user_email": user["email"],
        "plan": user["plan"],
        "region": user["region"],
        "page": rng.choice(PAGES) if event_type == "page_view" else "/login",
        "duration_ms": round(rng.lognormvariate(4.5, 0.45), 2),
        "status_code": status_code,
        "message": f"{event_type} for {user['user_id']}",
    }
    return event


def metrics_for_event(event: dict) -> list[dict]:
    """Metrics use low-cardinality tags; user ID intentionally stays in logs."""
    tags = [
        f"service:{event['service']}",
        f"env:{event['env']}",
        f"region:{event['region']}",
        f"plan:{event['plan']}",
        f"outcome:{'success' if event['status_code'] < 400 else 'failure'}",
    ]
    result = []
    if event["event_type"].startswith("login"):
        result.extend([
            {"metric": "demo.user_activity.login.count", "value": 1, "type": "count", "tags": tags},
            {"metric": "demo.user_activity.login.duration_ms", "value": event["duration_ms"], "type": "gauge", "tags": tags},
        ])
    if event["event_type"] == "page_view":
        result.append({
            "metric": "demo.user_activity.page_view.count",
            "value": 1,
            "type": "count",
            "tags": [*tags, f"page:{event['page']}"],
        })
    return result
