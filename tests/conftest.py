import pytest

from app.schemas import PolicyDocument


@pytest.fixture
def policy():
    return PolicyDocument(
        policy_id="restricted-zone-entry",
        version="1.0",
        name="Restricted zone entry",
        description="Detect a person entering the loading zone.",
        severity="high",
        when={
            "all": [
                {"field": "detection.class", "operator": "eq", "value": "person"},
                {"field": "event.zone", "operator": "eq", "value": "loading-zone"},
                {"field": "detection.confidence", "operator": "gte", "value": 0.85},
                {"not": {"field": "context.exception", "operator": "eq", "value": True}},
            ]
        },
        evidence_requirements=["two frames", "reviewer decision"],
        actions=["queue-review"],
    )


@pytest.fixture
def matching_event():
    return {
        "event": {"zone": "loading-zone"},
        "detection": {"class": "person", "confidence": 0.93},
        "context": {"exception": False},
    }

