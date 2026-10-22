# Datadog User Activity Demo

A standard-library Python demo that creates fake users and sends login/page-view data to Datadog as both structured logs and custom metrics.

## What you will see in Datadog

**Logs** record individual events, for example:

```json
{
  "event_type": "page_view",
  "user_id": "user-0007",
  "page": "/dashboard",
  "status_code": 200,
  "duration_ms": 123
}
```

**Metrics** record numeric totals and averages, for example:

- `demo.user_activity.login.count`
- `demo.user_activity.page_view.count`
- `demo.user_activity.login.duration_ms`

## Setup

Requires Python 3.10+. There are no packages to install.

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:

```text
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_application_key
DD_SITE=datadoghq.com
```

`DD_APP_KEY` is needed only for query scripts. Do not put either key in source code or commit `.env`.

For other Datadog sites, set the exact site domain, for example `datadoghq.eu`, `us3.datadoghq.com`, or `ap1.datadoghq.com`.

## Run it

First verify local event generation without sending anything:

```powershell
python generate_activity.py --events 20 --dry-run
```

Send 50 fake activities to Datadog:

```powershell
python generate_activity.py --events 50
```

Continuously send five activities every 10 seconds:

```powershell
python generate_activity.py --events 5 --interval 10 --repeat
```

Query the last hour of logs after they are indexed:

```powershell
python query_datadog.py logs --minutes 60
```

Query a metric with the older, simpler v1 time-series API:

```powershell
python query_datadog.py metric --metric demo.user_activity.login.count --minutes 60
```

## Datadog Log Explorer queries

Use these in Logs Explorer:

```text
service:demo-user-activity env:dev
service:demo-user-activity @event_type:login_success
service:demo-user-activity @event_type:page_view @page:/dashboard
service:demo-user-activity @user_id:user-0001
service:demo-user-activity @status_code:500
```

Facets worth creating: `event_type`, `user_id`, `page`, `status_code`, `plan`, and `region`.

## Metric Explorer queries

```text
sum:demo.user_activity.login.count{service:demo-user-activity,env:dev}.as_count()
sum:demo.user_activity.page_view.count{service:demo-user-activity,env:dev} by {page}.as_count()
avg:demo.user_activity.login.duration_ms{service:demo-user-activity,env:dev}
```

The metrics use low-cardinality tags: `service`, `env`, `region`, `plan`, `page`, and `outcome`. User IDs appear in logs only. Avoid adding `user_id` as a metric tag because it creates one metric time series per user.

## Datadog endpoints used

| Purpose | Endpoint |
|---|---|
| Send logs | `POST https://http-intake.logs.<DD_SITE>/api/v2/logs` |
| Send metrics | `POST https://api.<DD_SITE>/api/v2/series` |
| Search logs | `POST https://api.<DD_SITE>/api/v2/logs/events/search` |
| Query metric points | `GET https://api.<DD_SITE>/api/v1/query` |

The log-intake and metric-submit endpoints use `DD-API-KEY`. Log search and metric query require an app key too. Datadog recommends the v2 `/api/v2/query/timeseries` endpoint for new metric-query work; this demo uses v1 for the first query because it is easier to inspect. See the official API references for [sending logs](https://docs.datadoghq.com/api/latest/logs/send-logs/), [submitting metrics](https://docs.datadoghq.com/api/latest/metrics/submit-metrics/), [searching logs](https://docs.datadoghq.com/api/latest/logs/search-logs-get/), and [querying metrics](https://docs.datadoghq.com/api/latest/metrics/query-timeseries-points/).

## Files

| File | Purpose |
|---|---|
| `activity.py` | Creates fake users and activity events |
| `datadog_client.py` | Sends logs/metrics and queries Datadog with `urllib` |
| `generate_activity.py` | Generates and sends demo traffic |
| `query_datadog.py` | Reads logs and metric points through APIs |
| `tests.py` | Local validation without Datadog credentials |

