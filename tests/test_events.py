from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post("/api/projects", json={"name": "Demo"})
    response.raise_for_status()
    return response.json()


def test_ingest_event_requires_valid_api_key(client: TestClient) -> None:
    project = create_project(client)
    payload = {
        "event_type": "error",
        "name": "TypeError",
        "message": "Cannot read property of undefined",
        "page_url": "https://app.example.com/dashboard",
        "user_id": "user-123",
    }

    missing_key_response = client.post("/api/events", json=payload)
    assert missing_key_response.status_code == 422  # missing header

    invalid_key_response = client.post(
        "/api/events",
        json=payload,
        headers={"X-API-Key": "invalid"},
    )
    assert invalid_key_response.status_code == 404

    valid_response = client.post(
        "/api/events",
        json=payload,
        headers={"X-API-Key": project["api_key"]},
    )
    assert valid_response.status_code == 201
    stored_event = valid_response.json()
    assert stored_event["project_id"] == project["id"]
    assert stored_event["event_type"] == "error"


def test_list_events_supports_filters(client: TestClient) -> None:
    project = create_project(client)
    now = datetime.utcnow()
    events = [
        {
            "event_type": "error",
            "name": "TypeError",
            "message": "Cannot read property of undefined",
            "user_id": "alpha",
            "session_id": "s1",
            "occurred_at": (now - timedelta(minutes=5)).isoformat(),
        },
        {
            "event_type": "performance",
            "name": "TTFB",
            "payload": {"duration": 1200},
            "user_id": "beta",
            "session_id": "s2",
            "occurred_at": (now - timedelta(minutes=2)).isoformat(),
        },
    ]
    for event in events:
        response = client.post(
            "/api/events",
            json=event,
            headers={"X-API-Key": project["api_key"]},
        )
        assert response.status_code == 201

    list_response = client.get(f"/api/events/project/{project['id']}")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    filter_response = client.get(
        f"/api/events/project/{project['id']}",
        params={"event_type": "error", "user_id": "alpha"},
    )
    assert filter_response.status_code == 200
    filtered = filter_response.json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["event_type"] == "error"
