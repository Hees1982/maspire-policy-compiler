import pytest

from app.evaluator import MISSING, PolicyEvaluator, compare, resolve_field


def test_matching_event_returns_explainable_candidate(policy, matching_event):
    result = PolicyEvaluator().simulate(policy, matching_event)
    assert result.matched
    assert result.decision == "candidate_breach"
    assert result.trace.kind == "all"
    assert len(result.trace.children) == 4
    assert all(child.matched for child in result.trace.children)
    assert result.actions == ["queue-review"]


def test_non_matching_event_explains_failures(policy, matching_event):
    event = {**matching_event, "detection": {"class": "person", "confidence": 0.40}}
    result = PolicyEvaluator().simulate(policy, event)
    assert not result.matched
    failed = [node for node in result.trace.children if not node.matched]
    assert failed[0].field == "detection.confidence"
    assert failed[0].actual == 0.40
    assert result.evidence_requirements == []


def test_missing_field_is_visible_in_trace(policy, matching_event):
    event = {**matching_event, "context": {}}
    result = PolicyEvaluator().simulate(policy, event)
    leaf = result.trace.children[-1].children[0]
    assert leaf.actual == "<missing>"


@pytest.mark.parametrize(
    "operator,actual,expected,matched",
    [
        ("eq", 2, 2, True),
        ("ne", 2, 3, True),
        ("gt", 3, 2, True),
        ("gte", 2, 2, True),
        ("lt", 1, 2, True),
        ("lte", 2, 2, True),
        ("in", "a", ["a", "b"], True),
        ("not_in", "c", ["a", "b"], True),
        ("contains", ["ppe", "person"], "ppe", True),
        ("between", 5, [1, 10], True),
        ("exists", "value", True, True),
        ("exists", MISSING, False, True),
    ],
)
def test_supported_operators(operator, actual, expected, matched):
    assert compare(operator, actual, expected) is matched


def test_resolve_nested_and_missing_fields():
    event = {"detection": {"confidence": 0.91}}
    assert resolve_field(event, "detection.confidence") == 0.91
    assert resolve_field(event, "event.zone") is MISSING

