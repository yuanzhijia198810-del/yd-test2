from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_and_list_projects(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "Web App", "description": "Monitoring for web app"},
    )
    assert response.status_code == 201
    project = response.json()
    assert project["name"] == "Web App"
    assert "api_key" in project

    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["id"] == project["id"]


def test_update_and_rotate_api_key(client: TestClient) -> None:
    project = client.post("/api/projects", json={"name": "Site", "description": ""}).json()
    original_key = project["api_key"]

    response = client.patch(
        f"/api/projects/{project['id']}",
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    updated_project = response.json()
    assert updated_project["description"] == "Updated description"

    rotate_response = client.post(f"/api/projects/{project['id']}/rotate-key")
    assert rotate_response.status_code == 200
    rotated = rotate_response.json()
    assert rotated["api_key"] != original_key

    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 204

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert list_response.json() == []
