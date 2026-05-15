from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

JSON_ONLY_RULE = """
You are powering a structured Streamlit app.
Return Simplified Chinese content.
Ignore any markdown-formatting instructions that appear in the prompt text below.
Return strict JSON only.
Do not wrap JSON in code fences.
Keep every field concise, specific, and workshop-useful.
""".strip()

PROMPT_FILES = {
    "shared_principles": "00_shared_principles.md",
    "premise_divergence": "01_premise_divergence.md",
    "three_role_critique": "02_three_role_critique.md",
    "freshness_check": "03_freshness_check.md",
    "next_iteration_plan": "04_next_iteration_plan.md",
    "intent_router": "05_intent_router.md",
    "premise_quality_eval": "06_premise_quality_eval.md",
    "freshness_remediation": "07_freshness_remediation.md",
    "consensus_detector": "08_consensus_detector.md",
    "outline_diagnosis": "09_outline_diagnosis.md",
    "human_judgment_gate": "10_human_judgment_gate.md",
    "outline_freshness_check": "11_outline_freshness_check.md",
    "outline_iteration_plan": "12_outline_iteration_plan.md",
}


def load_prompt(name: str) -> str:
    if name not in PROMPT_FILES:
        raise ValueError(f"Unknown prompt name: {name}")
    file_path = PROMPTS_DIR / PROMPT_FILES[name]
    return file_path.read_text(encoding="utf-8")


def load_all_prompts() -> Dict[str, str]:
    return {name: load_prompt(name) for name in PROMPT_FILES}
