from __future__ import annotations

from typing import Any

from app.compiler import PolicyCompiler
from app.schemas import PolicyDocument, SimulationResult, TraceNode

MISSING = object()


def resolve_field(event: dict[str, Any], dotted_path: str) -> Any:
    current: Any = event
    for segment in dotted_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return MISSING
        current = current[segment]
    return current


def compare(operator: str, actual: Any, expected: Any) -> bool:
    if operator == "exists":
        return (actual is not MISSING) is bool(expected)
    if actual is MISSING:
        return False
    operations = {
        "eq": lambda: actual == expected,
        "ne": lambda: actual != expected,
        "gt": lambda: actual > expected,
        "gte": lambda: actual >= expected,
        "lt": lambda: actual < expected,
        "lte": lambda: actual <= expected,
        "in": lambda: actual in expected,
        "not_in": lambda: actual not in expected,
        "contains": lambda: expected in actual,
        "between": lambda: expected[0] <= actual <= expected[1],
    }
    try:
        return bool(operations[operator]())
    except (TypeError, KeyError):
        return False


class PolicyEvaluator:
    def __init__(self, compiler: PolicyCompiler | None = None):
        self.compiler = compiler or PolicyCompiler()

    def simulate(self, policy: PolicyDocument, event: dict[str, Any]) -> SimulationResult:
        compiled = self.compiler.compile(policy)
        trace = self._evaluate(policy.when, event, "$when")
        return SimulationResult(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            policy_checksum_sha256=compiled.checksum_sha256,
            matched=trace.matched,
            decision="candidate_breach" if trace.matched else "no_match",
            severity=policy.severity,
            evidence_requirements=policy.evidence_requirements if trace.matched else [],
            actions=policy.actions if trace.matched else [],
            trace=trace,
        )

    def _evaluate(self, node: dict[str, Any], event: dict[str, Any], path: str) -> TraceNode:
        if "all" in node:
            children = [
                self._evaluate(child, event, f"{path}.all[{i}]")
                for i, child in enumerate(node["all"])
            ]
            matched = all(child.matched for child in children)
            return TraceNode(
                path=path,
                kind="all",
                matched=matched,
                summary=f"{sum(c.matched for c in children)}/{len(children)} conditions matched",
                children=children,
            )
        if "any" in node:
            children = [
                self._evaluate(child, event, f"{path}.any[{i}]")
                for i, child in enumerate(node["any"])
            ]
            matched = any(child.matched for child in children)
            return TraceNode(
                path=path,
                kind="any",
                matched=matched,
                summary=f"{sum(c.matched for c in children)}/{len(children)} alternatives matched",
                children=children,
            )
        if "not" in node:
            child = self._evaluate(node["not"], event, f"{path}.not")
            return TraceNode(
                path=path,
                kind="not",
                matched=not child.matched,
                summary=f"negated child result from {child.matched} to {not child.matched}",
                children=[child],
            )
        field_name = node["field"]
        operator = node["operator"]
        expected = node.get("value", True)
        actual = resolve_field(event, field_name)
        matched = compare(operator, actual, expected)
        display_actual = "<missing>" if actual is MISSING else actual
        return TraceNode(
            path=path,
            kind="condition",
            matched=matched,
            summary=f"{field_name} {operator} {expected!r} -> {matched}",
            field=field_name,
            operator=operator,
            expected=expected,
            actual=display_actual,
        )

