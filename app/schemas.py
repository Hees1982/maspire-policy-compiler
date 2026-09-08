from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PolicyDocument(BaseModel):
    policy_id: str = Field(pattern=r"^[a-z][a-z0-9-]{2,79}$")
    version: str = Field(pattern=r"^[0-9]+(?:\.[0-9]+){0,2}$")
    name: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=3, max_length=1000)
    severity: str = Field(pattern=r"^(low|medium|high|critical)$")
    when: dict[str, Any]
    evidence_requirements: list[str] = Field(default_factory=list, max_length=20)
    actions: list[str] = Field(default_factory=list, max_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompileRequest(BaseModel):
    policy: PolicyDocument


class CompiledPolicy(BaseModel):
    compiler_version: str
    policy: PolicyDocument
    checksum_sha256: str
    fields_referenced: list[str]
    node_count: int
    maximum_depth: int
    warnings: list[str]


class SimulationRequest(BaseModel):
    policy: PolicyDocument
    event: dict[str, Any]


class BatchSimulationRequest(BaseModel):
    policy: PolicyDocument
    events: list[dict[str, Any]] = Field(min_length=1, max_length=500)


class TraceNode(BaseModel):
    path: str
    kind: str
    matched: bool
    summary: str
    field: str | None = None
    operator: str | None = None
    expected: Any = None
    actual: Any = None
    children: list[TraceNode] = Field(default_factory=list)


class SimulationResult(BaseModel):
    policy_id: str
    policy_version: str
    policy_checksum_sha256: str
    matched: bool
    decision: str
    severity: str
    evidence_requirements: list[str]
    actions: list[str]
    trace: TraceNode


class BatchSimulationResult(BaseModel):
    policy_checksum_sha256: str
    events_evaluated: int
    events_matched: int
    match_rate: float
    results: list[SimulationResult]

