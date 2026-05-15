from __future__ import annotations

from typing import Any, TypedDict


class WorkflowInputs(TypedDict):
    mode: str
    topic: str
    format_type: str
    character_count: str
    character_relationship: str
    audience_feeling: str
    constraints: str
    existing_draft: str
    team_concern: str
    team_priority: str
    generate: bool


class PremiseOption(TypedDict):
    title: str
    premise: str
    core_conflict: str
    character_dynamic: str
    why_it_might_work: str
    biggest_risk: str
    escalation_path: str


class SelectedDirection(TypedDict):
    title: str
    summary: str
    format: str
    character_setup: str
    audience_feeling: str


class RoleCritiqueBlock(TypedDict):
    what_works: list[str]
    what_feels_weak: list[str]
    most_important_fix: list[str]


class CritiqueSynthesis(TypedDict):
    alignments: list[str]
    differences: list[str]
    next_discussion: list[str]


class ThreeRoleCritique(TypedDict):
    writer: RoleCritiqueBlock
    performer: RoleCritiqueBlock
    director: RoleCritiqueBlock
    synthesis: CritiqueSynthesis


class FreshnessCheck(TypedDict):
    overall: str
    diagnosis: str
    fresh_points: list[str]
    generic_risks: list[str]
    why_risk: list[str]
    improvements: list[str]


class IterationMove(TypedDict):
    move: str
    why: str
    better_version: str


class FreshnessRemediationItem(TypedDict):
    what_to_change: str
    why_its_cliche: str
    fresh_alternative: str
    example_twist: str


class ConsensusAlert(TypedDict):
    consensus_level: str
    shared_conclusions: list[str]
    skip_recommendation: bool
    recommended_focus: str
    reasoning: str


class AgentStepPayload(TypedDict):
    thought: str
    action: str
    observation: str
    timestamp: float


class AgentTracePayload(TypedDict):
    steps: list[AgentStepPayload]
    final_decision: str
    total_retries: int
    total_duration_seconds: float


class AgentTraceRecord(AgentTracePayload):
    agent: str


class AgentError(TypedDict):
    agent: str
    stage: str
    error: str


PremiseQualityEvaluation = TypedDict(
    "PremiseQualityEvaluation",
    {
        "scores": dict[str, Any],
        "average": float,
        "pass": bool,
        "retry_guidance": str,
        "weakest_dimension": str,
        "strongest_dimension": str,
    },
)


class RuntimeUsage(TypedDict, total=False):
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int


class LLMResponseMeta(TypedDict):
    requested_model: str
    actual_model: str | None
    stop_reason: str | None
    usage: RuntimeUsage
    duration_seconds: float


class RuntimeStageMeta(LLMResponseMeta):
    stage: str


class RuntimeSummary(TypedDict):
    stages: list[RuntimeStageMeta]


class LLMJSONResponse(TypedDict):
    data: dict[str, Any]
    meta: LLMResponseMeta


class PremiseGenerationResult(TypedDict):
    premises: list[PremiseOption]
    quality_scores: dict[str, Any]
    agent_trace: AgentTracePayload
    passed: bool


class FeedbackBundle(TypedDict):
    selected_direction: SelectedDirection
    critique: ThreeRoleCritique
    freshness: FreshnessCheck
    next_iteration_plan: list[IterationMove]
    human_judgment_gate: list[str]
    consensus_alert: ConsensusAlert | None
    freshness_remediation: list[FreshnessRemediationItem] | None
    agent_traces: list[AgentTraceRecord]
    agent_actions: list[str]
    agent_errors: list[AgentError]
    runtime_summary: RuntimeSummary


OutlineDiagnosisBundle = FeedbackBundle


class DemoScenario(TypedDict):
    label: str
    description: str
    mode: str
    inputs: dict[str, str]
    variant: str


class VersionSnapshot(TypedDict):
    version_id: str
    created_at: str
    mode: str
    title: str
    inputs: WorkflowInputs
    selected_direction: SelectedDirection | None
    critique: ThreeRoleCritique | None
    freshness: FreshnessCheck | None
    next_iteration_plan: list[IterationMove]
    human_judgment_gate: list[str]
    consensus_alert: ConsensusAlert | None
    freshness_remediation: list[FreshnessRemediationItem]
    runtime_summary: RuntimeSummary | None
