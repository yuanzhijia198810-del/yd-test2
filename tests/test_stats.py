from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post("/api/projects", json={"name": "Stats"})
    response.raise_for_status()
    return response.json()


def record_event(client: TestClient, api_key: str, **payload) -> dict:
    response = client.post("/api/events", json=payload, headers={"X-API-Key": api_key})
    response.raise_for_status()
    return response.json()


def test_summary_and_timeseries(client: TestClient) -> None:
    project = create_project(client)
    api_key = project["api_key"]
    base_time = datetime.utcnow().replace(microsecond=0)

    record_event(
        client,
        api_key,
        event_type="error",
        name="TypeError",
        occurred_at=(base_time - timedelta(hours=1)).isoformat(),
        user_id="user-a",
    )
    record_event(
        client,
        api_key,
        event_type="performance",
        name="Largest Contentful Paint",
        payload={"duration": 2500},
        occurred_at=base_time.isoformat(),
        user_id="user-b",
    )
    record_event(
        client,
        api_key,
        event_type="error",
        name="ReferenceError",
        occurred_at=base_time.isoformat(),
        user_id="user-b",
    )

    summary_response = client.get(f"/api/stats/project/{project['id']}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_events"] == 3
    assert summary["counts_by_type"]["error"] == 2
    assert summary["counts_by_type"]["performance"] == 1
    assert summary["unique_users"] == 2

    timeseries_response = client.get(
        f"/api/stats/project/{project['id']}/timeseries",
        params={"granularity": "hour"},
    )
    assert timeseries_response.status_code == 200
    timeseries = timeseries_response.json()
    assert len(timeseries) >= 1
    totals = sum(bucket["total"] for bucket in timeseries)
    assert totals == 3
