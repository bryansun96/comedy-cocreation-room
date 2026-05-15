"""智能体质量治理引擎。

实现「思考 → 行动 → 观察」循环，用于：
- 设定方向质量自评与自动重试
- 新鲜度风险补救
- 三角色共识检测
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from contracts import (
    FreshnessCheck,
    FreshnessRemediationItem,
    PremiseOption,
    PremiseQualityEvaluation,
    ThreeRoleCritique,
)
from llm_client import ClaudeClient
from prompt_loader import JSON_ONLY_RULE, load_all_prompts

_PROMPTS = load_all_prompts()

_AGENT_SYSTEM = (
    "你是一个内部质量评估智能体。"
    "所有内容使用简体中文。"
    "只返回严格 JSON，不要包裹代码块。"
)

# ─── Data Structures ────────────────────────────────────────────

@dataclass
class AgentStep:
    """一次「思考 → 行动 → 观察」循环。"""
    thought: str
    action: str
    observation: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentTrace:
    """Complete trace of an agent's reasoning process."""
    steps: list[AgentStep] = field(default_factory=list)
    final_decision: str = ""
    total_retries: int = 0
    total_duration_seconds: float = 0.0

    def add_step(self, thought: str, action: str, observation: str) -> None:
        self.steps.append(AgentStep(
            thought=thought,
            action=action,
            observation=observation,
        ))

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "final_decision": self.final_decision,
            "total_retries": self.total_retries,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
        }


@dataclass
class PremiseQualityResult:
    """Result of premise quality evaluation."""
    premises: list[PremiseOption]
    quality_scores: PremiseQualityEvaluation
    trace: AgentTrace
    passed: bool


@dataclass
class FreshnessRemediationResult:
    """Result of freshness remediation."""
    remediation: list[FreshnessRemediationItem]
    trace: AgentTrace


@dataclass
class ConsensusResult:
    """Result of consensus detection."""
    consensus_level: str  # "high", "medium", "low"
    shared_conclusions: list[str]
    skip_recommendation: bool
    recommended_focus: str
    reasoning: str
    trace: AgentTrace


# ─── Guardrails ─────────────────────────────────────────────────

MAX_RETRIES = 2
MAX_LOOP_SECONDS = 60.0
QUALITY_THRESHOLD = 3.5


def _is_stale(prev_score: float | None, curr_score: float) -> bool:
    """Detect if agent is stuck producing same quality."""
    if prev_score is None:
        return False
    return abs(prev_score - curr_score) < 0.1


# ─── Premise Quality Agent ──────────────────────────────────────

def evaluate_premise_quality(
    client: ClaudeClient,
    premises: list[PremiseOption],
) -> PremiseQualityEvaluation:
    """Evaluate quality of generated premises using the rubric."""
    eval_prompt = _PROMPTS.get("premise_quality_eval", "")
    if not eval_prompt:
        # Fallback: assume pass if prompt not loaded
        return {
            "scores": {},
            "average": 4.0,
            "pass": True,
            "retry_guidance": "",
        }

    payload = {"premises": premises}
    schema = {
        "scores": {
            "premise_clarity": 0,
            "conflict_engine": 0,
            "escalation_potential": 0,
            "differentiation": 0,
            "specificity": 0,
        },
        "average": 0.0,
        "pass": True,
        "retry_guidance": "",
        "weakest_dimension": "",
        "strongest_dimension": "",
    }

    user_prompt = "\n\n".join([
        eval_prompt,
        "## Premises to Evaluate",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "## JSON Schema",
        json.dumps(schema, ensure_ascii=False, indent=2),
    ])

    response = client.generate_json(
        system_prompt=_AGENT_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.2,
    )
    data = response["data"]

    # Normalize and validate
    scores = data.get("scores", {})
    avg = data.get("average", 0.0)
    if not isinstance(avg, (int, float)):
        try:
            avg = float(avg)
        except (ValueError, TypeError):
            avg = 0.0

    return {
        "scores": scores,
        "average": avg,
        "pass": avg >= QUALITY_THRESHOLD,
        "retry_guidance": data.get("retry_guidance", ""),
        "weakest_dimension": data.get("weakest_dimension", ""),
        "strongest_dimension": data.get("strongest_dimension", ""),
    }


def run_premise_quality_loop(
    client: ClaudeClient,
    generate_fn: Callable[..., list[PremiseOption]],
    generate_args: tuple,
    generate_kwargs: dict,
    on_progress: Callable[[str, str], None] | None = None,
) -> PremiseQualityResult:
    """智能体循环：生成设定方向 → 评估质量 → 必要时重试。"""
    trace = AgentTrace()
    started_at = time.perf_counter()
    prev_score = None
    last_premises = None
    last_quality = None
    retry_guidance = ""

    for attempt in range(1 + MAX_RETRIES):
        elapsed = time.perf_counter() - started_at
        if elapsed > MAX_LOOP_SECONDS:
            trace.add_step(
                thought=f"已用时 {elapsed:.1f}s，超过 {MAX_LOOP_SECONDS}s 上限，停止重试。",
                action="熔断退出",
                observation="使用当前最佳结果。",
            )
            break

        # ── 思考 ──
        if attempt == 0:
            thought = "开始生成设定方向，完成后将进行质量自评。"
        else:
            thought = f"第 {attempt} 次重试，上一轮评分 {prev_score:.1f}，低于阈值 {QUALITY_THRESHOLD}。将注入引导：{retry_guidance}"
            trace.total_retries += 1

        # ── 行动：生成 ──
        if on_progress and attempt > 0:
            on_progress("retry", f"质量未达标（{prev_score:.1f}/{QUALITY_THRESHOLD}），正在重新生成…第 {attempt + 1} 次")

        # Inject retry guidance into kwargs if retrying
        kwargs = dict(generate_kwargs)
        if retry_guidance:
            current_inputs = kwargs.get("inputs") or (generate_args[1] if len(generate_args) > 1 else {})
            if isinstance(current_inputs, dict):
                augmented = dict(current_inputs)
                augmented["_retry_guidance"] = retry_guidance
                kwargs["inputs"] = augmented

        try:
            premises = generate_fn(*generate_args, **kwargs)
        except Exception as exc:
            trace.add_step(
                thought=thought,
                action=f"生成设定方向（第 {attempt + 1} 次）",
                observation=f"生成失败：{exc}",
            )
            if last_premises is not None:
                break
            raise

        # ── 行动：评估 ──
        if on_progress:
            on_progress("quality_eval", "正在评估设定方向质量…")

        try:
            quality = evaluate_premise_quality(client, premises)
        except Exception as exc:
            trace.add_step(
                thought=thought,
                action="质量自评",
                observation=f"自评失败：{exc}，将直接使用当前结果。",
            )
            last_premises = premises
            last_quality = {"scores": {}, "average": 0.0, "pass": True, "retry_guidance": ""}
            break

        # ── 观察 ──
        avg = quality["average"]
        observation = (
            f"质量评分：{avg:.1f}/{QUALITY_THRESHOLD}，"
            f"{'通过' if quality['pass'] else '未通过'}。"
            f" 最弱维度：{quality.get('weakest_dimension') or '未返回'}，"
            f"最强维度：{quality.get('strongest_dimension') or '未返回'}。"
        )

        trace.add_step(
            thought=thought,
            action=f"生成设定方向（第 {attempt + 1} 次）+ 质量自评",
            observation=observation,
        )

        last_premises = premises
        last_quality = quality

        if quality["pass"]:
            break

        # Stale detection
        if _is_stale(prev_score, avg):
            trace.add_step(
                thought=f"连续两次评分相近（{prev_score:.1f} → {avg:.1f}），智能体可能卡住。",
                action="停止重试",
                observation="使用当前结果，避免无效循环。",
            )
            break

        prev_score = avg
        retry_guidance = quality.get("retry_guidance", "")

    trace.final_decision = (
        f"使用第 {trace.total_retries + 1} 次生成的结果，"
        f"质量评分 {last_quality['average']:.1f}。"
        if last_quality else "使用初次生成的结果。"
    )
    trace.total_duration_seconds = time.perf_counter() - started_at

    return PremiseQualityResult(
        premises=last_premises or [],
        quality_scores=last_quality or {},
        trace=trace,
        passed=last_quality.get("pass", True) if last_quality else True,
    )


# ─── Freshness Guard Agent ──────────────────────────────────────

def run_freshness_remediation(
    client: ClaudeClient,
    inputs: dict[str, Any],
    selected_direction: dict[str, str],
    freshness_data: FreshnessCheck,
) -> FreshnessRemediationResult:
    """When freshness is Weak, auto-generate de-cliché suggestions."""
    trace = AgentTrace()
    started_at = time.perf_counter()

    freshness_label_map = {
        "Strong": "强",
        "Medium": "中等",
        "Weak": "偏弱",
        "strong": "强",
        "medium": "中等",
        "weak": "偏弱",
    }
    freshness_label = freshness_label_map.get(freshness_data.get("overall"), freshness_data.get("overall", "?"))

    trace.add_step(
        thought=f"新鲜度评分为「{freshness_label}」，触发自动去套路化修改建议。",
        action="生成去套路化修改方向",
        observation="开始调用新鲜度修复提示词…",
    )

    remediation_prompt = _PROMPTS.get("freshness_remediation", "")
    if not remediation_prompt:
        trace.add_step(
            thought="新鲜度修复提示词未加载。",
            action="跳过",
            observation="返回空结果。",
        )
        trace.final_decision = "无法生成去套路化建议：提示词未加载。"
        trace.total_duration_seconds = time.perf_counter() - started_at
        return FreshnessRemediationResult(remediation=[], trace=trace)

    payload = {
        "current_premise": selected_direction.get("summary", ""),
        "freshness_diagnosis": freshness_data.get("diagnosis", ""),
        "generic_risks": freshness_data.get("generic_risks", []),
        "why_risk": freshness_data.get("why_risk", []),
        "format_type": inputs.get("format_type", ""),
        "constraints": inputs.get("constraints", ""),
    }
    schema = {
        "remediations": [
            {
                "what_to_change": "具体要改什么",
                "why_its_cliche": "为什么当前版本像套路",
                "fresh_alternative": "更新鲜的替代方案",
                "example_twist": "一个具体转向示例",
            }
        ]
    }

    user_prompt = "\n\n".join([
        remediation_prompt,
        "## Input",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "## JSON Schema",
        json.dumps(schema, ensure_ascii=False, indent=2),
    ])

    system_prompt = "\n\n".join([_PROMPTS["shared_principles"], JSON_ONLY_RULE])

    response = client.generate_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7,
    )

    remediations = response["data"].get("remediations", [])
    normalized = []
    for item in remediations[:3]:
        if isinstance(item, dict):
            normalized.append({
                "what_to_change": item.get("what_to_change", ""),
                "why_its_cliche": item.get("why_its_cliche", ""),
                "fresh_alternative": item.get("fresh_alternative", ""),
                "example_twist": item.get("example_twist", ""),
            })

    trace.add_step(
        thought="去套路化建议生成完成。",
        action="结果收集",
        observation=f"生成了 {len(normalized)} 条去套路化建议。",
    )
    trace.final_decision = f"为新鲜度偏弱的设定方向生成了 {len(normalized)} 条改写方向。"
    trace.total_duration_seconds = time.perf_counter() - started_at

    return FreshnessRemediationResult(remediation=normalized, trace=trace)


# ─── Consensus Detector Agent ───────────────────────────────────

def run_consensus_detection(
    client: ClaudeClient,
    critique_data: ThreeRoleCritique,
) -> ConsensusResult:
    """Detect whether three roles share strong consensus."""
    trace = AgentTrace()
    started_at = time.perf_counter()

    trace.add_step(
        thought="开始分析三角色反馈，检测是否存在高度共识。",
        action="共识检测",
        observation="调用共识检测提示词…",
    )

    consensus_prompt = _PROMPTS.get("consensus_detector", "")
    if not consensus_prompt:
        trace.add_step(
            thought="共识检测提示词未加载。",
            action="跳过",
            observation="返回默认中等结果。",
        )
        trace.final_decision = "无法检测共识：提示词未加载。"
        trace.total_duration_seconds = time.perf_counter() - started_at
        return ConsensusResult(
            consensus_level="medium",
            shared_conclusions=[],
            skip_recommendation=False,
            recommended_focus="",
            reasoning="共识检测提示词未加载，默认不做判断。",
            trace=trace,
        )

    payload = {
        "writer_feedback": critique_data.get("writer", {}),
        "performer_feedback": critique_data.get("performer", {}),
        "director_feedback": critique_data.get("director", {}),
        "synthesis": critique_data.get("synthesis", {}),
    }
    schema = {
        "consensus_level": "high / medium / low",
        "shared_conclusions": ["三方都认为..."],
        "skip_recommendation": True,
        "recommended_focus": "建议跳过分歧讨论，直接聚焦于...",
        "reasoning": "判断理由",
    }

    user_prompt = "\n\n".join([
        consensus_prompt,
        "## Three-Role Critique Data",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "## JSON Schema",
        json.dumps(schema, ensure_ascii=False, indent=2),
    ])

    response = client.generate_json(
        system_prompt=_AGENT_SYSTEM,
        user_prompt=user_prompt,
        temperature=0.2,
    )
    data = response["data"]

    consensus_level = data.get("consensus_level", "medium")
    if consensus_level not in ("high", "medium", "low"):
        consensus_level = "medium"

    shared = data.get("shared_conclusions", [])
    if isinstance(shared, str):
        shared = [shared] if shared.strip() else []

    skip = data.get("skip_recommendation", False)
    if not isinstance(skip, bool):
        skip = str(skip).lower() in ("true", "yes", "是")

    result = ConsensusResult(
        consensus_level=consensus_level,
        shared_conclusions=shared,
        skip_recommendation=skip,
        recommended_focus=data.get("recommended_focus", ""),
        reasoning=data.get("reasoning", ""),
        trace=trace,
    )

    consensus_label_map = {
        "high": "高",
        "medium": "中等",
        "low": "低",
    }
    consensus_label = consensus_label_map.get(consensus_level, consensus_level)

    observation = (
        f"共识等级：{consensus_label}，"
        f"共识结论 {len(shared)} 条，"
        f"建议跳过分歧：{'是' if skip else '否'}。"
    )
    trace.add_step(
        thought="共识检测完成。",
        action="结果分析",
        observation=observation,
    )

    trace.final_decision = (
        f"三角色共识等级为「{consensus_label}」，"
        + ("建议跳过分歧讨论，聚焦行动。" if skip else "建议保留分歧讨论环节。")
    )
    trace.total_duration_seconds = time.perf_counter() - started_at

    return result
