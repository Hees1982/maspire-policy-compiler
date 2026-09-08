from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.canonical import policy_checksum
from app.schemas import CompiledPolicy, PolicyDocument

COMPILER_VERSION = "0.1.0"
GROUP_KEYS = {"all", "any", "not"}
LEAF_KEYS = {"field", "operator", "value"}
OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "exists", "between"}
ALLOWED_FIELD_PREFIXES = ("event.", "detection.", "site.", "camera.", "context.")


class PolicyCompileError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class Inspection:
    fields: set[str] = field(default_factory=set)
    node_count: int = 0
    maximum_depth: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PolicyCompiler:
    def __init__(self, max_depth: int = 8):
        self.max_depth = max_depth

    def compile(self, policy: PolicyDocument) -> CompiledPolicy:
        inspection = Inspection()
        self._inspect(policy.when, "$when", 1, inspection)
        if not policy.evidence_requirements:
            inspection.warnings.append("policy has no evidence requirements")
        if not policy.actions:
            inspection.warnings.append("policy has no resulting actions")
        if inspection.errors:
            raise PolicyCompileError(inspection.errors)
        normalized = policy.model_dump(mode="json", exclude_none=True)
        return CompiledPolicy(
            compiler_version=COMPILER_VERSION,
            policy=policy,
            checksum_sha256=policy_checksum(normalized),
            fields_referenced=sorted(inspection.fields),
            node_count=inspection.node_count,
            maximum_depth=inspection.maximum_depth,
            warnings=inspection.warnings,
        )

    def _inspect(self, node: Any, path: str, depth: int, inspection: Inspection) -> None:
        inspection.node_count += 1
        inspection.maximum_depth = max(inspection.maximum_depth, depth)
        if depth > self.max_depth:
            inspection.errors.append(f"{path}: nesting exceeds maximum depth {self.max_depth}")
            return
        if not isinstance(node, dict):
            inspection.errors.append(f"{path}: condition must be an object")
            return
        group_keys = GROUP_KEYS.intersection(node)
        if group_keys:
            if len(group_keys) != 1 or set(node) != group_keys:
                inspection.errors.append(f"{path}: group must contain exactly one of all, any or not")
                return
            key = next(iter(group_keys))
            children = node[key]
            if key == "not":
                self._inspect(children, f"{path}.not", depth + 1, inspection)
                return
            if not isinstance(children, list) or not children:
                inspection.errors.append(f"{path}.{key}: must be a non-empty list")
                return
            for index, child in enumerate(children):
                self._inspect(child, f"{path}.{key}[{index}]", depth + 1, inspection)
            return
        if not {"field", "operator"}.issubset(node) or not set(node).issubset(LEAF_KEYS):
            inspection.errors.append(
                f"{path}: leaf requires field/operator and optional value; unknown keys are forbidden"
            )
            return
        field_name = node["field"]
        operator = node["operator"]
        if not isinstance(field_name, str) or not field_name.startswith(ALLOWED_FIELD_PREFIXES):
            inspection.errors.append(f"{path}.field: unsupported field namespace")
        else:
            inspection.fields.add(field_name)
        if operator not in OPERATORS:
            inspection.errors.append(f"{path}.operator: unsupported operator {operator!r}")
        if operator != "exists" and "value" not in node:
            inspection.errors.append(f"{path}: operator {operator!r} requires value")
        if operator == "between":
            value = node.get("value")
            if not isinstance(value, list) or len(value) != 2:
                inspection.errors.append(f"{path}.value: between requires [minimum, maximum]")
        if operator in {"in", "not_in"} and not isinstance(node.get("value"), list):
            inspection.errors.append(f"{path}.value: {operator} requires a list")

