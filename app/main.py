from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.compiler import PolicyCompileError, PolicyCompiler
from app.evaluator import PolicyEvaluator
from app.schemas import (
    BatchSimulationRequest,
    BatchSimulationResult,
    CompiledPolicy,
    CompileRequest,
    SimulationRequest,
    SimulationResult,
)


def create_app() -> FastAPI:
    compiler = PolicyCompiler()
    evaluator = PolicyEvaluator(compiler)
    api = FastAPI(
        title="Maspire Compliance Policy Compiler",
        version="0.1.0",
        description=(
            "Compiles structured compliance policies and produces explainable simulation "
            "traces for operational events. Technical demonstrator only."
        ),
        license_info={"name": "Apache 2.0"},
    )

    @api.get("/health", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @api.post("/v1/policies/compile", response_model=CompiledPolicy, tags=["compiler"])
    def compile_policy(request: CompileRequest) -> CompiledPolicy:
        try:
            return compiler.compile(request.policy)
        except PolicyCompileError as exc:
            raise HTTPException(status_code=422, detail=exc.errors) from exc

    @api.post("/v1/policies/simulate", response_model=SimulationResult, tags=["simulation"])
    def simulate(request: SimulationRequest) -> SimulationResult:
        try:
            return evaluator.simulate(request.policy, request.event)
        except PolicyCompileError as exc:
            raise HTTPException(status_code=422, detail=exc.errors) from exc

    @api.post(
        "/v1/policies/batch-simulate",
        response_model=BatchSimulationResult,
        tags=["simulation"],
    )
    def batch_simulate(request: BatchSimulationRequest) -> BatchSimulationResult:
        try:
            results = [evaluator.simulate(request.policy, event) for event in request.events]
        except PolicyCompileError as exc:
            raise HTTPException(status_code=422, detail=exc.errors) from exc
        matched = sum(result.matched for result in results)
        return BatchSimulationResult(
            policy_checksum_sha256=results[0].policy_checksum_sha256,
            events_evaluated=len(results),
            events_matched=matched,
            match_rate=matched / len(results),
            results=results,
        )

    return api


app = create_app()

