import pytest

from app.compiler import PolicyCompileError, PolicyCompiler


def test_compiler_reports_fields_and_complexity(policy):
    result = PolicyCompiler().compile(policy)
    assert result.node_count == 6
    assert result.maximum_depth == 3
    assert result.fields_referenced == [
        "context.exception",
        "detection.class",
        "detection.confidence",
        "event.zone",
    ]
    assert len(result.checksum_sha256) == 64


@pytest.mark.parametrize(
    "condition, expected",
    [
        ({"field": "unknown.value", "operator": "eq", "value": 1}, "namespace"),
        ({"field": "event.zone", "operator": "execute", "value": 1}, "unsupported operator"),
        ({"field": "event.zone", "operator": "eq"}, "requires value"),
        ({"any": []}, "non-empty list"),
        ({"all": [], "any": []}, "exactly one"),
        ({"field": "event.x", "operator": "between", "value": [1]}, "between requires"),
        ({"field": "event.x", "operator": "in", "value": "x"}, "requires a list"),
    ],
)
def test_invalid_policy_is_rejected(policy, condition, expected):
    broken = policy.model_copy(update={"when": condition})
    with pytest.raises(PolicyCompileError, match=expected):
        PolicyCompiler().compile(broken)


def test_warns_when_outputs_are_missing(policy):
    sparse = policy.model_copy(update={"actions": [], "evidence_requirements": []})
    result = PolicyCompiler().compile(sparse)
    assert len(result.warnings) == 2

