"""Minimal Datadog HTTP client using Python's standard library only."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
METRIC_TYPE_CODES = {
    "count": 1,
    "rate": 2,
    "gauge": 3,
}

def load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE lines without replacing exported environment variables."""
    dotenv = Path(path)
    if not dotenv.exists():
        return
    for line in dotenv.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def normalize_site(site: str) -> str:
    site = site.strip().removeprefix("https://").removesuffix("/")
    if not site or "/" in site or any(character.isspace() for character in site):
        raise ValueError("DD_SITE must be a domain such as datadoghq.com")
    return site


class DatadogClient:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.environ.get("DD_API_KEY", "")
        self.app_key = os.environ.get("DD_APP_KEY", "")
        self.site = normalize_site(os.environ.get("DD_SITE", "datadoghq.com"))

    def _headers(self, require_app_key: bool = False) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("DD_API_KEY is missing. Copy .env.example to .env and add it.")
        if require_app_key and not self.app_key:
            raise ValueError("DD_APP_KEY is required for queries. Add it to .env.")
        headers = {"Content-Type": "application/json", "DD-API-KEY": self.api_key}
        if require_app_key:
            headers["DD-APPLICATION-KEY"] = self.app_key
        return headers

    @staticmethod
    def _json_request(url: str, method: str, headers: dict[str, str], body: dict | list | None = None) -> dict:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                content = response.read().decode("utf-8")
                return {} if not content else json.loads(content)
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Datadog returned HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Could not reach Datadog: {error.reason}") from error

    def send_logs(self, events: list[dict]) -> dict:
        return self._json_request(
            f"https://http-intake.logs.{self.site}/api/v2/logs",
            "POST",
            self._headers(),
            events,
        )

    def submit_metrics(self, metric_events: list[dict]) -> dict:
        now = int(time.time())
        series = [{
            "metric": item["metric"],
            "type": METRIC_TYPE_CODES[item["type"]],
            "points": [{"timestamp": now, "value": item["value"]}],
            "resources": [{"name": "demo-user-activity", "type": "host"}],
            "tags": item["tags"],
        } for item in metric_events]
        return self._json_request(
            f"https://api.{self.site}/api/v2/series",
            "POST",
            self._headers(),
            {"series": series},
        )

    def search_logs(self, query: str, minutes: int = 60, limit: int = 20) -> dict:
        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=minutes)
        body = {
            "filter": {"query": query, "from": start.isoformat().replace("+00:00", "Z"), "to": end.isoformat().replace("+00:00", "Z")},
            "sort": "-timestamp",
            "page": {"limit": limit},
        }
        return self._json_request(
            f"https://api.{self.site}/api/v2/logs/events/search",
            "POST",
            self._headers(require_app_key=True),
            body,
        )

    def query_metric_v1(self, metric_query: str, minutes: int = 60) -> dict:
        end = int(time.time())
        params = urlencode({"from": end - minutes * 60, "to": end, "query": metric_query})
        return self._json_request(
            f"https://api.{self.site}/api/v1/query?{params}",
            "GET",
            self._headers(require_app_key=True),
        )
