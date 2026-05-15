import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypedDict

from contracts import (
    AgentError,
    AgentTraceRecord,
    ConsensusAlert,
    FeedbackBundle,
    FreshnessCheck,
    FreshnessRemediationItem,
    IterationMove,
    OutlineDiagnosisBundle,
    PremiseGenerationResult,
    PremiseOption,
    RoleCritiqueBlock,
    RuntimeStageMeta,
    RuntimeSummary,
    SelectedDirection,
    ThreeRoleCritique,
    WorkflowInputs,
)
from llm_client import ClaudeClient
from prompt_loader import JSON_ONLY_RULE, load_all_prompts
from react_agent import (
    run_consensus_detection,
    run_freshness_remediation,
    run_premise_quality_loop,
)


class StageResult(TypedDict):
    data: Any
    meta: RuntimeStageMeta


PROMPTS = load_all_prompts()

_FALLBACK_HUMAN_JUDGMENT: list[str] = [
    "最终笑点是否真正成立，仍需要创作者自己判断。",
    "角色语感和表演节奏是否自然，必须通过人来确认。",
    "哪些修改方向更符合团队的创作取向，不能由 AI 最终决定。",
]

PREMISE_SCHEMA = {
    "premises": [
        {
            "title": "方向标题",
            "premise": "一句话设定",
            "core_conflict": "核心冲突",
            "character_dynamic": "角色关系或搭档动态",
            "why_it_might_work": "为什么可能成立",
            "biggest_risk": "最大风险",
            "escalation_path": "升级路径",
        }
    ]
}

THREE_ROLE_CRITIQUE_SCHEMA = {
    "writer": {
        "what_works": [""],
        "what_feels_weak": [""],
        "most_important_fix": [""],
    },
    "performer": {
        "what_works": [""],
        "what_feels_weak": [""],
        "most_important_fix": [""],
    },
    "director": {
        "what_works": [""],
        "what_feels_weak": [""],
        "most_important_fix": [""],
    },
    "synthesis": {
        "alignments": [""],
        "differences": [""],
        "next_discussion": [""],
    },
}

FRESHNESS_SCHEMA = {
    "overall": "Strong / Medium / Weak",
    "diagnosis": "一句话诊断",
    "fresh_points": [""],
    "generic_risks": [""],
    "why_risk": [""],
    "improvements": [""],
}

NEXT_ITERATION_SCHEMA = {
    "moves": [
        {
            "move": "下一步动作",
            "why": "为什么重要",
            "better_version": "更好版本可能是什么样",
        }
    ]
}

HUMAN_JUDGMENT_SCHEMA = {
    "items": ["具体判断提醒 1", "具体判断提醒 2", "具体判断提醒 3"]
}


def _raw_generate_premises(client: ClaudeClient, inputs: dict[str, Any]) -> list[PremiseOption]:
    """Raw premise generation without quality evaluation (used by ReAct loop)."""
    retry_guidance = inputs.get("_retry_guidance", "")
    payload = {
        "topic": inputs.get("topic", ""),
        "format_type": inputs.get("format_type", ""),
        "character_count": inputs.get("character_count", ""),
        "character_relationship": inputs.get("character_relationship", ""),
        "audience_feeling": inputs.get("audience_feeling", ""),
        "constraints": inputs.get("constraints", ""),
        "anything_to_avoid": inputs.get("constraints", ""),
    }
    if retry_guidance:
        payload["quality_improvement_guidance"] = retry_guidance

    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["premise_divergence"],
        input_payload=payload,
        schema=PREMISE_SCHEMA,
        temperature=0.85,
        stage_name="premise_divergence",
    )
    premises = response["data"].get("premises") or response["data"].get("directions") or []
    normalized = [_normalize_premise(item) for item in premises if isinstance(item, dict)]
    if len(normalized) < 3:
        raise ValueError("模型没有返回 3 个清晰可比的设定方向。")
    return normalized[:3]


def generate_premise_options(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    on_progress: Callable[[str, str], None] | None = None,
) -> PremiseGenerationResult:
    """Generate premise options with ReAct quality self-evaluation loop."""
    result = run_premise_quality_loop(
        client=client,
        generate_fn=_raw_generate_premises,
        generate_args=(client,),
        generate_kwargs={"inputs": inputs},
        on_progress=on_progress,
    )
    return {
        "premises": result.premises,
        "quality_scores": result.quality_scores,
        "agent_trace": result.trace.to_dict(),
        "passed": result.passed,
    }


def build_selected_direction_from_premise(premise: PremiseOption, inputs: WorkflowInputs) -> SelectedDirection:
    return {
        "title": _to_text(premise.get("title"), "已选方向"),
        "summary": _to_text(premise.get("premise"), ""),
        "format": _to_text(inputs.get("format_type"), "未填写"),
        "character_setup": _to_text(
            premise.get("character_dynamic") or inputs.get("character_relationship"),
            f"{_to_text(inputs.get('character_count'), '未填写')} 个角色",
        ),
        "audience_feeling": _to_text(inputs.get("audience_feeling"), "未填写"),
    }


def build_selected_direction_from_outline(inputs: WorkflowInputs) -> SelectedDirection:
    draft = _to_text(inputs.get("existing_draft"), "")
    short_summary = draft if len(draft) <= 140 else f"{draft[:140].rstrip()}…"
    return {
        "title": _to_text(inputs.get("topic"), "当前大纲 / 现有想法"),
        "summary": short_summary,
        "format": _to_text(inputs.get("format_type"), "未填写"),
        "character_setup": _to_text(
            inputs.get("character_relationship"),
            f"{_to_text(inputs.get('character_count'), '未填写')} 个角色",
        ),
        "audience_feeling": _to_text(inputs.get("audience_feeling"), "未填写"),
    }


def generate_feedback_bundle(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
    on_progress: Callable[[str, str], None] | None = None,
) -> FeedbackBundle:
    critique_result, freshness_result = _run_parallel_feedback_stages(
        client=client,
        inputs=inputs,
        selected_direction=selected_direction,
        critique_fn=generate_three_role_critique,
        freshness_fn=generate_freshness_check,
        on_progress=on_progress,
    )

    if on_progress:
        on_progress("next_iteration", "正在基于前两项结果生成下一轮修改建议…")
    next_iteration_result = generate_next_iteration_plan(
        client,
        inputs,
        selected_direction,
        critique_result["data"],
        freshness_result["data"],
    )
    return _assemble_feedback_bundle(
        client=client,
        inputs=inputs,
        selected_direction=selected_direction,
        critique_result=critique_result,
        freshness_result=freshness_result,
        next_iteration_result=next_iteration_result,
        on_progress=on_progress,
    )


def generate_outline_diagnosis_bundle(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    on_progress: Callable[[str, str], None] | None = None,
) -> OutlineDiagnosisBundle:
    selected_direction = build_selected_direction_from_outline(inputs)
    critique_result, freshness_result = _run_parallel_feedback_stages(
        client=client,
        inputs=inputs,
        selected_direction=selected_direction,
        critique_fn=generate_outline_three_role_critique,
        freshness_fn=generate_outline_freshness_check,
        on_progress=on_progress,
    )

    if on_progress:
        on_progress("next_iteration", "正在基于大纲诊断结果生成下一轮修改建议…")
    next_iteration_result = generate_outline_iteration_plan(
        client,
        inputs,
        selected_direction,
        critique_result["data"],
        freshness_result["data"],
    )
    return _assemble_feedback_bundle(
        client=client,
        inputs=inputs,
        selected_direction=selected_direction,
        critique_result=critique_result,
        freshness_result=freshness_result,
        next_iteration_result=next_iteration_result,
        on_progress=on_progress,
    )


def _run_parallel_feedback_stages(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
    critique_fn: Callable[[ClaudeClient, WorkflowInputs, SelectedDirection], StageResult],
    freshness_fn: Callable[[ClaudeClient, WorkflowInputs, SelectedDirection], StageResult],
    on_progress: Callable[[str, str], None] | None = None,
) -> tuple[StageResult, StageResult]:
    if on_progress:
        on_progress("parallel", "正在并行生成三角色反馈与新鲜度检查…")
    with ThreadPoolExecutor(max_workers=2) as executor:
        critique_future = executor.submit(critique_fn, client, inputs, selected_direction)
        freshness_future = executor.submit(freshness_fn, client, inputs, selected_direction)
        critique_result = critique_future.result()
        freshness_result = freshness_future.result()
    return critique_result, freshness_result


def _assemble_feedback_bundle(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
    critique_result: StageResult,
    freshness_result: StageResult,
    next_iteration_result: StageResult,
    on_progress: Callable[[str, str], None] | None = None,
) -> FeedbackBundle:
    agent_traces: list[AgentTraceRecord] = []
    agent_actions: list[str] = []
    agent_errors: list[AgentError] = []
    consensus_alert: ConsensusAlert | None = None
    freshness_remediation: list[FreshnessRemediationItem] | None = None

    if on_progress:
        on_progress("consensus", "正在检测三角色共识…")
    try:
        consensus_result = run_consensus_detection(client, critique_result["data"])
        agent_traces.append({"agent": "consensus_detector", **consensus_result.trace.to_dict()})
        if consensus_result.consensus_level == "high":
            consensus_alert = {
                "consensus_level": consensus_result.consensus_level,
                "shared_conclusions": consensus_result.shared_conclusions,
                "skip_recommendation": consensus_result.skip_recommendation,
                "recommended_focus": consensus_result.recommended_focus,
                "reasoning": consensus_result.reasoning,
            }
            agent_actions.append("consensus_skip_recommendation")
    except Exception as exc:  # pragma: no cover - defensive capture for UI diagnostics
        agent_errors.append(
            {
                "agent": "consensus_detector",
                "stage": "consensus",
                "error": str(exc),
            }
        )

    freshness_overall = _to_text(freshness_result["data"].get("overall"), "").lower()
    if freshness_overall in ("weak", "弱"):
        if on_progress:
            on_progress("remediation", "新鲜度偏弱，正在生成去套路化建议…")
        try:
            remediation_result = run_freshness_remediation(
                client, inputs, selected_direction, freshness_result["data"]
            )
            agent_traces.append({"agent": "freshness_guard", **remediation_result.trace.to_dict()})
            if remediation_result.remediation:
                freshness_remediation = remediation_result.remediation
                agent_actions.append("freshness_weak_auto_remediation")
        except Exception as exc:  # pragma: no cover - defensive capture for UI diagnostics
            agent_errors.append(
                {
                    "agent": "freshness_guard",
                    "stage": "remediation",
                    "error": str(exc),
                }
            )

    if on_progress:
        on_progress("human_judgment", "正在生成本轮人类判断清单…")
    try:
        human_judgment_gate = generate_human_judgment_gate(
            client=client,
            selected_direction=selected_direction,
            critique=critique_result["data"],
            freshness=freshness_result["data"],
            next_iteration_plan=next_iteration_result["data"],
        )
    except Exception:
        human_judgment_gate = _FALLBACK_HUMAN_JUDGMENT

    return {
        "selected_direction": selected_direction,
        "critique": critique_result["data"],
        "freshness": freshness_result["data"],
        "next_iteration_plan": next_iteration_result["data"],
        "human_judgment_gate": human_judgment_gate,
        "consensus_alert": consensus_alert,
        "freshness_remediation": freshness_remediation,
        "agent_traces": agent_traces,
        "agent_actions": agent_actions,
        "agent_errors": agent_errors,
        "runtime_summary": _build_runtime_summary(
            critique_result["meta"],
            freshness_result["meta"],
            next_iteration_result["meta"],
        ),
    }


def generate_three_role_critique(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
) -> StageResult:
    payload = {
        "format_type": inputs.get("format_type", ""),
        "topic_or_premise": selected_direction.get("summary", ""),
        "characters": selected_direction.get("character_setup", ""),
        "existing_outline_or_draft": inputs.get("existing_draft", ""),
        "intended_audience_feeling": inputs.get("audience_feeling", ""),
        "specific_team_concern": inputs.get("team_concern", ""),
        "selected_direction": selected_direction,
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["three_role_critique"],
        input_payload=payload,
        schema=THREE_ROLE_CRITIQUE_SCHEMA,
        temperature=0.7,
        stage_name="three_role_critique",
    )
    return {
        "data": _normalize_critique(response["data"]),
        "meta": response["meta"],
    }


def generate_outline_three_role_critique(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
) -> StageResult:
    payload = {
        "topic": inputs.get("topic", ""),
        "existing_draft": inputs.get("existing_draft", ""),
        "format_type": inputs.get("format_type", ""),
        "character_relationship": inputs.get("character_relationship", ""),
        "intended_audience_feeling": inputs.get("audience_feeling", ""),
        "team_concern": inputs.get("team_concern", ""),
        "team_priority": inputs.get("team_priority", ""),
        "outline_summary": selected_direction,
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["outline_diagnosis"],
        input_payload=payload,
        schema=THREE_ROLE_CRITIQUE_SCHEMA,
        temperature=0.65,
        stage_name="outline_diagnosis",
    )
    return {
        "data": _normalize_critique(response["data"]),
        "meta": response["meta"],
    }


def generate_freshness_check(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
) -> StageResult:
    payload = {
        "topic_or_premise": selected_direction.get("summary", ""),
        "format_type": inputs.get("format_type", ""),
        "existing_outline_or_sketch_idea": inputs.get("existing_draft", "") or selected_direction.get("summary", ""),
        "intended_audience": inputs.get("audience_feeling", ""),
        "references": inputs.get("team_concern", ""),
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["freshness_check"],
        input_payload=payload,
        schema=FRESHNESS_SCHEMA,
        temperature=0.55,
        stage_name="freshness_check",
    )
    return {
        "data": _normalize_freshness(response["data"]),
        "meta": response["meta"],
    }


def generate_outline_freshness_check(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
) -> StageResult:
    payload = {
        "topic_or_premise": inputs.get("topic", "") or selected_direction.get("summary", ""),
        "format_type": inputs.get("format_type", ""),
        "existing_outline_or_draft": inputs.get("existing_draft", "") or selected_direction.get("summary", ""),
        "intended_audience_feeling": inputs.get("audience_feeling", ""),
        "team_concern": inputs.get("team_concern", ""),
        "outline_summary": selected_direction,
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["outline_freshness_check"],
        input_payload=payload,
        schema=FRESHNESS_SCHEMA,
        temperature=0.55,
        stage_name="outline_freshness_check",
    )
    return {
        "data": _normalize_freshness(response["data"]),
        "meta": response["meta"],
    }


def generate_next_iteration_plan(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
    critique: ThreeRoleCritique,
    freshness: FreshnessCheck,
) -> StageResult:
    payload = {
        "current_premise_or_outline": selected_direction,
        "known_problems": {
            "writer": critique["writer"]["what_feels_weak"],
            "performer": critique["performer"]["what_feels_weak"],
            "director": critique["director"]["what_feels_weak"],
            "freshness": freshness["generic_risks"],
        },
        "feedback_already_received": critique,
        "team_priority": _resolve_team_priority(inputs),
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["next_iteration_plan"],
        input_payload=payload,
        schema=NEXT_ITERATION_SCHEMA,
        temperature=0.6,
        stage_name="next_iteration_plan",
    )
    return {
        "data": _normalize_moves(response["data"]),
        "meta": response["meta"],
    }


def generate_outline_iteration_plan(
    client: ClaudeClient,
    inputs: WorkflowInputs,
    selected_direction: SelectedDirection,
    critique: ThreeRoleCritique,
    freshness: FreshnessCheck,
) -> StageResult:
    payload = {
        "current_outline_or_draft": {
            **selected_direction,
            "existing_draft": inputs.get("existing_draft", ""),
        },
        "known_structural_problems": {
            "writer": critique["writer"]["what_feels_weak"],
            "performer": critique["performer"]["what_feels_weak"],
            "director": critique["director"]["what_feels_weak"],
            "freshness_risks": freshness["generic_risks"],
        },
        "team_priority": _resolve_team_priority(inputs),
        "team_concern": inputs.get("team_concern", ""),
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["outline_iteration_plan"],
        input_payload=payload,
        schema=NEXT_ITERATION_SCHEMA,
        temperature=0.6,
        stage_name="outline_iteration_plan",
    )
    return {
        "data": _normalize_moves(response["data"]),
        "meta": response["meta"],
    }


def generate_human_judgment_gate(
    client: ClaudeClient,
    selected_direction: SelectedDirection,
    critique: ThreeRoleCritique,
    freshness: FreshnessCheck,
    next_iteration_plan: list[IterationMove],
) -> list[str]:
    payload = {
        "selected_direction": selected_direction,
        "critique_synthesis": critique.get("synthesis", {}),
        "writer_weak_points": critique.get("writer", {}).get("what_feels_weak", []),
        "performer_weak_points": critique.get("performer", {}).get("what_feels_weak", []),
        "freshness_overall": freshness.get("overall", ""),
        "freshness_diagnosis": freshness.get("diagnosis", ""),
        "next_moves": [m.get("move", "") for m in next_iteration_plan if isinstance(m, dict)],
    }
    response = _call_stage(
        client=client,
        stage_prompt=PROMPTS["human_judgment_gate"],
        input_payload=payload,
        schema=HUMAN_JUDGMENT_SCHEMA,
        temperature=0.5,
        stage_name="human_judgment_gate",
    )
    items = [_to_text(item) for item in (response["data"].get("items") or []) if item]
    return items[:4] if items else _FALLBACK_HUMAN_JUDGMENT


def _call_stage(
    client: ClaudeClient,
    stage_prompt: str,
    input_payload: dict[str, Any],
    schema: dict[str, Any],
    temperature: float,
    stage_name: str,
) -> StageResult:
    system_prompt = "\n\n".join([PROMPTS["shared_principles"], JSON_ONLY_RULE])
    user_prompt = "\n\n".join(
        [
            stage_prompt,
            "请忽略上面 prompt 中任何面向 Markdown 的输出格式说明，只按下面 JSON schema 返回。",
            "## Input Payload",
            json.dumps(input_payload, ensure_ascii=False, indent=2),
            "## JSON Schema",
            json.dumps(schema, ensure_ascii=False, indent=2),
        ]
    )
    response = client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)
    meta: RuntimeStageMeta = dict(response.get("meta") or {})
    meta["stage"] = stage_name
    return {
        "data": response["data"],
        "meta": meta,
    }


def _build_runtime_summary(*stages: RuntimeStageMeta) -> RuntimeSummary:
    return {"stages": list(stages)}


def _normalize_premise(item: dict[str, Any]) -> PremiseOption:
    return {
        "title": _to_text(item.get("title"), "未命名方向"),
        "premise": _to_text(item.get("premise") or item.get("summary"), ""),
        "core_conflict": _to_text(item.get("core_conflict"), ""),
        "character_dynamic": _to_text(item.get("character_dynamic"), ""),
        "why_it_might_work": _to_text(item.get("why_it_might_work"), ""),
        "biggest_risk": _to_text(item.get("biggest_risk"), ""),
        "escalation_path": _to_text(item.get("escalation_path"), ""),
    }


def _normalize_critique(data: dict[str, Any]) -> ThreeRoleCritique:
    synthesis = data.get("synthesis") if isinstance(data.get("synthesis"), dict) else {}
    return {
        "writer": _normalize_role_block(data.get("writer", {})),
        "performer": _normalize_role_block(data.get("performer", {})),
        "director": _normalize_role_block(data.get("director", {})),
        "synthesis": {
            "alignments": _to_list(synthesis.get("alignments")),
            "differences": _to_list(synthesis.get("differences")),
            "next_discussion": _to_list(synthesis.get("next_discussion")),
        },
    }


def _normalize_role_block(data: dict[str, Any]) -> RoleCritiqueBlock:
    block = data if isinstance(data, dict) else {}
    return {
        "what_works": _to_list(block.get("what_works") or block.get("strengths")),
        "what_feels_weak": _to_list(
            block.get("what_feels_weak")
            or block.get("what_feels_hard_to_play")
            or block.get("what_may_not_land_on_stage")
            or block.get("concerns")
        ),
        "most_important_fix": _to_list(
            block.get("most_important_fix")
            or block.get("most_important_writing_fix")
            or block.get("most_important_performance_fix")
            or block.get("most_important_directing_fix")
        ),
    }


def _normalize_freshness(data: dict[str, Any]) -> FreshnessCheck:
    return {
        "overall": _to_text(data.get("overall"), "中"),
        "diagnosis": _to_text(data.get("diagnosis"), ""),
        "fresh_points": _to_list(data.get("fresh_points") or data.get("where_it_feels_fresh")),
        "generic_risks": _to_list(data.get("generic_risks") or data.get("where_it_risks_feeling_generic")),
        "why_risk": _to_list(data.get("why_risk") or data.get("why_the_cliche_risk_appears")),
        "improvements": _to_list(data.get("improvements") or data.get("improvement_directions")),
    }


def _normalize_move(item: dict[str, Any]) -> IterationMove:
    return {
        "move": _to_text(item.get("move") or item.get("what_to_change"), "下一步"),
        "why": _to_text(item.get("why") or item.get("why_it_matters"), ""),
        "better_version": _to_text(
            item.get("better_version") or item.get("what_better_version_might_look_like"),
            "",
        ),
    }


def _normalize_moves(data: dict[str, Any]) -> list[IterationMove]:
    moves = data.get("moves") or data.get("top_3_next_moves") or []
    normalized = [_normalize_move(item) for item in moves if isinstance(item, dict)]
    if len(normalized) < 3:
        raise ValueError("模型没有返回 3 条足够清晰的下一轮修改建议。")
    return normalized[:3]


def _resolve_team_priority(inputs: WorkflowInputs) -> str:
    return _to_text(inputs.get("team_priority") or inputs.get("team_concern"), "clarity")


def _to_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    return text or fallback


def _to_list(value: Any) -> list[str]:
    if isinstance(value, list):
        result = [_to_text(item) for item in value]
        return [item for item in result if item]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return [text]
    return []
