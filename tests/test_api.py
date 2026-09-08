from fastapi.testclient import TestClient

from app.main import create_app


def test_compile_and_simulate_api(policy, matching_event):
    client = TestClient(create_app())
    compiled = client.post("/v1/policies/compile", json={"policy": policy.model_dump()})
    assert compiled.status_code == 200
    assert len(compiled.json()["checksum_sha256"]) == 64

    simulated = client.post(
        "/v1/policies/simulate",
        json={"policy": policy.model_dump(), "event": matching_event},
    )
    assert simulated.status_code == 200
    assert simulated.json()["matched"] is True


def test_batch_simulation_reports_rate(policy, matching_event):
    client = TestClient(create_app())
    non_match = {**matching_event, "event": {"zone": "staff-room"}}
    response = client.post(
        "/v1/policies/batch-simulate",
        json={"policy": policy.model_dump(), "events": [matching_event, non_match]},
    )
    assert response.status_code == 200
    assert response.json()["events_evaluated"] == 2
    assert response.json()["events_matched"] == 1
    assert response.json()["match_rate"] == 0.5

