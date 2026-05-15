import streamlit as st

from config import build_runtime_config, get_missing_runtime_fields, get_runtime_defaults
from llm_client import ClaudeClient, LLMClientError
from pipeline import (
    build_selected_direction_from_outline,
    build_selected_direction_from_premise,
    generate_feedback_bundle,
    generate_outline_diagnosis_bundle,
    generate_premise_options,
)
from prompt_loader import load_all_prompts

st.set_page_config(page_title="Co-Creation Room Copilot", layout="wide")

prompts = load_all_prompts()
RESULT_STATE_KEYS = [
    "generated_premises",
    "premise_quality_scores",
    "premise_agent_trace",
    "premise_passed",
    "selected_direction",
    "critique",
    "freshness",
    "next_iteration_plan",
    "human_judgment_gate",
    "consensus_alert",
    "freshness_remediation",
    "agent_traces",
    "agent_actions",
    "agent_errors",
    "runtime_summary",
    "generation_error",
]


CUSTOM_CSS = """
<style>
:root {
    --bg: #080807;
    --panel: rgba(22, 21, 18, 0.88);
    --panel-strong: rgba(31, 29, 24, 0.96);
    --panel-soft: rgba(255, 246, 222, 0.055);
    --line: rgba(255, 246, 222, 0.13);
    --line-strong: rgba(224, 173, 88, 0.34);
    --text: #fff3dc;
    --text-soft: rgba(255, 243, 220, 0.72);
    --text-faint: rgba(255, 243, 220, 0.48);
    --accent: #e0ad58;
    --accent-strong: #f4cb78;
    --signal: #7bd8ca;
    --signal-soft: rgba(123, 216, 202, 0.13);
    --radius-lg: 28px;
    --radius-md: 18px;
    --font-sans: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    --font-serif: ui-serif, "Songti SC", "Noto Serif CJK SC", Georgia, serif;
    --font-mono: "SF Mono", "Cascadia Code", Menlo, monospace;
}

.stApp {
    background:
        radial-gradient(circle at 12% 0%, rgba(224, 173, 88, 0.18), transparent 28rem),
        radial-gradient(circle at 88% 6%, rgba(123, 216, 202, 0.11), transparent 25rem),
        linear-gradient(180deg, #090908 0%, #11100d 52%, #070706 100%);
    color: var(--text);
    font-family: var(--font-serif);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
        linear-gradient(rgba(255, 246, 222, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 246, 222, 0.035) 1px, transparent 1px);
    background-size: 76px 76px;
    mask-image: linear-gradient(to bottom, black, transparent 76%);
}

[data-testid="stAppViewContainer"] > .main {
    position: relative;
    z-index: 1;
}

[data-testid="stHeader"] {
    background: rgba(8, 8, 7, 0.56);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 246, 222, 0.07);
}

.block-container {
    max-width: 1520px;
    padding-top: 2.2rem;
    padding-bottom: 5rem;
}

h1, h2, h3, p, li, label, span {
    color: var(--text);
}

h1 {
    font-family: var(--font-serif);
    letter-spacing: -0.075em;
}

h2, h3, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    font-family: var(--font-sans);
    letter-spacing: -0.035em;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
.stCaptionContainer {
    color: var(--text-soft);
    line-height: 1.75;
}

.hero-shell {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: 36px;
    padding: clamp(28px, 5vw, 58px);
    margin: 10px 0 28px;
    background:
        radial-gradient(circle at 74% 10%, rgba(224, 173, 88, 0.22), transparent 24rem),
        radial-gradient(circle at 18% 90%, rgba(123, 216, 202, 0.12), transparent 22rem),
        linear-gradient(145deg, rgba(255, 246, 222, 0.095), rgba(255, 246, 222, 0.022)),
        rgba(12, 11, 10, 0.82);
    box-shadow: inset 0 1px 0 rgba(255, 246, 222, 0.08), 0 28px 90px rgba(0, 0, 0, 0.32);
}

.hero-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, transparent 0%, rgba(224, 173, 88, 0.11) 50%, transparent 100%),
        repeating-linear-gradient(0deg, transparent 0 38px, rgba(255, 246, 222, 0.03) 39px 40px);
    opacity: 0.8;
    pointer-events: none;
}

.hero-content {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.72fr);
    gap: 36px;
    align-items: end;
}

.hero-kicker,
.panel-kicker,
.stage-label {
    color: var(--accent-strong);
    font-family: var(--font-mono);
    font-size: 0.76rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

.hero-title {
    max-width: 10ch;
    margin: 18px 0 22px;
    color: var(--text);
    font-size: clamp(3.8rem, 8vw, 7.8rem);
    line-height: 0.86;
    letter-spacing: -0.09em;
}

.hero-lead {
    max-width: 760px;
    color: var(--text-soft);
    font-size: clamp(1.08rem, 1.8vw, 1.45rem);
    line-height: 1.78;
}

.hero-console {
    display: grid;
    gap: 14px;
    padding: 22px;
    border: 1px solid rgba(255, 246, 222, 0.14);
    border-radius: 26px;
    background: rgba(0, 0, 0, 0.2);
}

.console-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 246, 222, 0.1);
    color: var(--text-soft);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.console-dot {
    display: inline-flex;
    width: 9px;
    height: 9px;
    margin-right: 8px;
    border-radius: 50%;
    background: var(--signal);
    box-shadow: 0 0 20px rgba(123, 216, 202, 0.85);
}

.console-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.console-metric {
    min-height: 96px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 14px;
    border: 1px solid rgba(255, 246, 222, 0.1);
    border-radius: 18px;
    background: rgba(255, 246, 222, 0.045);
}

.console-metric small {
    color: var(--text-faint);
    font-family: var(--font-mono);
    font-size: 0.68rem;
    text-transform: uppercase;
}

.console-metric strong {
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 1rem;
    line-height: 1.35;
}

.demo-steps {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: -6px 0 30px;
}

.demo-step {
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 16px;
    background: rgba(255, 246, 222, 0.046);
    box-shadow: inset 0 1px 0 rgba(255, 246, 222, 0.055);
}

.demo-step span {
    display: block;
    margin-bottom: 12px;
    color: var(--accent-strong);
    font-family: var(--font-mono);
    font-size: 0.72rem;
}

.demo-step strong {
    display: block;
    margin-bottom: 7px;
    color: var(--text);
    font-family: var(--font-sans);
}

.demo-step p {
    margin: 0;
    color: var(--text-soft);
    font-size: 0.92rem;
    line-height: 1.55;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line) !important;
    border-radius: var(--radius-lg) !important;
    background:
        linear-gradient(145deg, rgba(255, 246, 222, 0.07), rgba(255, 246, 222, 0.02)),
        rgba(13, 12, 10, 0.76) !important;
    box-shadow: inset 0 1px 0 rgba(255, 246, 222, 0.06);
}

[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-md) !important;
    background: rgba(255, 246, 222, 0.035) !important;
    overflow: hidden;
}

[data-testid="stExpander"] summary {
    color: var(--text) !important;
    font-family: var(--font-sans);
}

.stAlert {
    border-radius: 18px;
    border: 1px solid var(--line-strong);
    background: rgba(224, 173, 88, 0.09);
}

[data-testid="stStatusWidget"],
[data-testid="stStatus"] {
    border: 1px solid rgba(244, 203, 120, 0.24) !important;
    border-radius: 22px !important;
    background:
        linear-gradient(145deg, rgba(255, 246, 222, 0.07), rgba(255, 246, 222, 0.025)),
        rgba(10, 9, 8, 0.82) !important;
    box-shadow: inset 0 1px 0 rgba(255, 246, 222, 0.07) !important;
}

[data-testid="stStatusWidget"] p,
[data-testid="stStatus"] p,
[data-testid="stProgress"] p {
    color: var(--text-soft) !important;
    font-family: var(--font-sans) !important;
}

[data-testid="stProgress"] {
    padding: 12px 0 4px;
}

[data-testid="stProgress"] > div {
    background: rgba(255, 246, 222, 0.08) !important;
    border-radius: 999px !important;
    overflow: hidden !important;
}

[data-testid="stProgress"] > div > div,
[data-testid="stProgress"] > div > div > div,
[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent-strong), var(--signal)) !important;
    border-radius: 999px !important;
}

[data-testid="stSpinner"] {
    color: var(--accent-strong) !important;
}

.stButton > button {
    min-height: 46px;
    border: 1px solid var(--line-strong) !important;
    border-radius: 999px !important;
    background: linear-gradient(135deg, rgba(244, 203, 120, 0.96), rgba(173, 113, 39, 0.94)) !important;
    color: #14100a !important;
    font-family: var(--font-sans) !important;
    font-weight: 700 !important;
    box-shadow: 0 16px 42px rgba(224, 173, 88, 0.16);
    transition: transform 180ms ease, box-shadow 180ms ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 22px 56px rgba(224, 173, 88, 0.22);
}

.stTextInput,
.stTextArea {
    margin-bottom: 0.78rem;
}

.stTextInput input,
.stTextArea textarea {
    border: 1px solid rgba(255, 246, 222, 0.12) !important;
    border-radius: 20px !important;
    background:
        linear-gradient(145deg, rgba(255, 246, 222, 0.07), rgba(255, 246, 222, 0.026)),
        rgba(10, 9, 8, 0.72) !important;
    color: var(--text) !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 246, 222, 0.06),
        inset 0 -18px 40px rgba(0, 0, 0, 0.16) !important;
    caret-color: var(--accent-strong) !important;
    transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}

.stTextArea textarea {
    min-height: 116px;
    line-height: 1.72 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: rgba(255, 243, 220, 0.34) !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(244, 203, 120, 0.58) !important;
    background:
        linear-gradient(145deg, rgba(255, 246, 222, 0.09), rgba(255, 246, 222, 0.035)),
        rgba(10, 9, 8, 0.84) !important;
    box-shadow:
        0 0 0 1px rgba(244, 203, 120, 0.18),
        0 18px 46px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 246, 222, 0.08) !important;
}

[data-baseweb="select"] > div {
    border: 1px solid rgba(255, 246, 222, 0.12) !important;
    border-radius: 18px !important;
    background:
        linear-gradient(145deg, rgba(255, 246, 222, 0.066), rgba(255, 246, 222, 0.024)),
        rgba(10, 9, 8, 0.72) !important;
    color: var(--text) !important;
    box-shadow: inset 0 1px 0 rgba(255, 246, 222, 0.055) !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: var(--text) !important;
}

.stTextInput > div,
.stTextArea > div,
.stTextInput > div > div,
.stTextArea > div > div,
.stTextInput [data-baseweb="input"],
.stTextArea [data-baseweb="textarea"],
.stTextInput [data-baseweb="base-input"],
.stTextArea [data-baseweb="base-input"],
[data-testid="stTextInputRootElement"],
[data-testid="stTextAreaRootElement"] {
    border: 0 !important;
    outline: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}

.stTextInput input:hover,
.stTextArea textarea:hover,
[data-baseweb="select"] > div:hover {
    border-color: rgba(244, 203, 120, 0.34) !important;
}

.stTextInput input:-webkit-autofill {
    -webkit-text-fill-color: var(--text) !important;
    box-shadow: 0 0 0 1000px rgba(10, 9, 8, 0.92) inset !important;
}

[data-testid="stRadio"] label,
[data-testid="stSelectbox"] label,
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label {
    color: var(--text-soft) !important;
    font-family: var(--font-sans);
}

[data-testid="stMetric"] {
    padding: 14px;
    border: 1px solid rgba(255, 246, 222, 0.1);
    border-radius: 18px;
    background: rgba(255, 246, 222, 0.04);
}

[data-testid="stMetricLabel"] p {
    color: var(--text-faint) !important;
    font-family: var(--font-mono);
    font-size: 0.72rem;
}

[data-testid="stMetricValue"] {
    color: var(--accent-strong) !important;
    font-family: var(--font-sans);
}

hr {
    border-color: rgba(255, 246, 222, 0.1) !important;
}

code, pre {
    border-radius: 16px !important;
    background: rgba(0, 0, 0, 0.34) !important;
}

@media (max-width: 980px) {
    .hero-content,
    .demo-steps {
        grid-template-columns: 1fr;
    }
    .console-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def inject_design_system():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def initialize_session_state():
    defaults = get_runtime_defaults()
    session_defaults = {
        "input_mode": "设定发散",
        "input_topic": "",
        "input_format_type": "双人",
        "input_character_count": "2",
        "input_character_relationship": "",
        "input_audience_feeling": "尴尬升级 + 强共鸣 + 角色反差",
        "input_constraints": "",
        "input_existing_draft": "",
        "input_team_concern": "",
        "input_team_priority": "clarity",
        "_team_priority_label": "先让方向更清楚",
        "runtime_base_url": defaults.base_url,
        "runtime_api_key": defaults.api_key,
        "runtime_model": defaults.model,
        "auto_run_example": False,
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_generation_state():
    for key in RESULT_STATE_KEYS:
        st.session_state.pop(key, None)


def load_example_inputs():
    clear_generation_state()
    priority_options = get_team_priority_options()
    # Toggle between two example types so users can see both modes
    use_outline_example = st.session_state.get("_example_toggle", False)
    st.session_state["_example_toggle"] = not use_outline_example

    if use_outline_example:
        # Outline critique example
        st.session_state.input_mode = "大纲诊断"
        st.session_state.input_topic = "社交事故后的双人错位救场"
        st.session_state.input_existing_draft = (
            "一场不能翻车的婚礼致辞现场，一个人只想赶紧把尴尬圆过去，"
            "另一个人坚持用一套过度专业的方法论来修复场面，结果每一步都让局面更失控。"
        )
        st.session_state.input_character_relationship = "一位高度情绪敏感，一位高度流程驱动的搭档"
        st.session_state.input_team_concern = "担心现在只是在做感性 vs 理性的常见对撞。"
        st.session_state.input_team_priority = "fresher angle"
    else:
        # Premise exploration example
        st.session_state.input_mode = "设定发散"
        st.session_state.input_topic = "一个人把所有生活问题都当成项目管理问题来处理。"
        st.session_state.input_character_relationship = "双人搭档，一位情绪驱动，一位方法论驱动"
        st.session_state.input_constraints = "不要太像短视频段子；希望适合双人表演；不要只有职场黑话。"
        st.session_state.input_team_concern = "希望角色差异能落到具体行动，不只是观点互怼。"
        st.session_state.input_team_priority = "better escalation"
        st.session_state.input_existing_draft = ""

    st.session_state._team_priority_label = priority_options.get(
        st.session_state.input_team_priority,
        priority_options["clarity"],
    )
    st.session_state.auto_run_example = True


def render_header():
    st.markdown(
        """
        <section class="hero-shell">
            <div class="hero-content">
                <div>
                    <div class="hero-kicker">共创工作坊智能体助手 · 产品演示</div>
                    <h1 class="hero-title">智能体协作工作台</h1>
                    <p class="hero-lead">
                        面向喜剧共创工作坊的人工智能产品最小可行原型。它不是自动成稿工具，而是把共创讨论拆成结构化输入、
                        多角色评价、质量治理、风险提示和下一轮迭代计划。
                    </p>
                </div>
                <aside class="hero-console">
                    <div class="console-row">
                        <span><i class="console-dot"></i>工作流在线</span>
                        <span>人在回路</span>
                    </div>
                    <div class="console-grid">
                        <div class="console-metric"><small>工作模式</small><strong>设定发散 / 大纲诊断</strong></div>
                        <div class="console-metric"><small>智能体机制</small><strong>质量自评 · 共识检测 · 新鲜度治理</strong></div>
                        <div class="console-metric"><small>输出形态</small><strong>结构化评审工作台</strong></div>
                        <div class="console-metric"><small>产品边界</small><strong>辅助判断，不替代创作</strong></div>
                    </div>
                </aside>
            </div>
        </section>
        <section class="demo-steps">
            <div class="demo-step"><span>01</span><strong>载入示例</strong><p>点击左侧示例简报，先看到完整输入结构。</p></div>
            <div class="demo-step"><span>02</span><strong>选择模式</strong><p>从设定发散或大纲诊断进入不同状态流。</p></div>
            <div class="demo-step"><span>03</span><strong>查看输出</strong><p>阅读三角色评审、共识检测、新鲜度判断和下一轮计划。</p></div>
            <div class="demo-step"><span>04</span><strong>审阅治理</strong><p>展开智能体推理链路，看质量自评、重试与风险补救。</p></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def get_team_priority_options():
    return {
        "clarity": "先让方向更清楚",
        "stronger laughs": "先把笑点做强",
        "better escalation": "先把升级做出来",
        "more playable roles": "先让角色更好演",
        "fresher angle": "先找更新鲜的角度",
        "other": "其他重点",
    }


def render_runtime_config():
    with st.expander("模型连接配置", expanded=False):
        st.text_input(
            "服务地址",
            key="runtime_base_url",
            placeholder="例如：http://127.0.0.1:15721",
        )
        st.text_input("访问密钥", key="runtime_api_key", type="password")
        st.text_input("模型名称", key="runtime_model", placeholder="例如：deepseek-v3.2")
        st.caption(
            "这个区域用于验证真实模型调用链路；优先读取环境变量，也兼容通用模型代理配置。"
        )


class ProgressReporter:
    def __init__(self):
        self._status = None
        self._progress = None
        self._supports_status = hasattr(st, "status")

    def start(self, label: str):
        if self._supports_status:
            self._status = st.status(label, expanded=True)
        self._progress = st.progress(0, text=label)

    def update(self, step: str, label: str):
        progress_map = {
            "prepare": 10,
            "premise": 25,
            "quality_eval": 40,
            "retry": 45,
            "parallel": 60,
            "consensus": 72,
            "remediation": 78,
            "next_iteration": 88,
            "human_judgment": 93,
            "complete": 100,
            "error": 100,
        }
        if self._status is not None:
            self._status.update(label=label)
        if self._progress is not None:
            self._progress.progress(progress_map.get(step, 0), text=label)

    def complete(self, label: str):
        if self._status is not None:
            self._status.update(label=label, state="complete")
        if self._progress is not None:
            self._progress.progress(100, text=label)

    def error(self, label: str):
        if self._status is not None:
            self._status.update(label=label, state="error")
        if self._progress is not None:
            self._progress.progress(100, text=label)


def _append_runtime_history(summary):
    if not summary:
        return
    history = list(st.session_state.get("runtime_history") or [])
    history.append(summary)
    st.session_state.runtime_history = history[-5:]


def render_runtime_diagnostics(summary):
    if not summary:
        return

    stages = summary.get("stages") or []
    if not stages:
        return

    returned_models = [stage.get("actual_model") for stage in stages if stage.get("actual_model")]
    configured_models = [stage.get("requested_model") for stage in stages if stage.get("requested_model")]
    configured_model = configured_models[0] if configured_models else "未返回"

    mismatch = any(stage.get("actual_model") and stage.get("actual_model") != stage.get("requested_model") for stage in stages)
    drift = len(set(returned_models)) > 1

    st.markdown("### 运行时诊断")
    st.caption("以下信息仅用于开发和排查，不属于共创输出本身。")
    st.markdown(f"**配置模型**：{configured_model}")
    if mismatch:
        st.warning("返回模型与配置模型不一致，说明代理可能做了模型映射或上游改写。")
    elif returned_models:
        st.success("本轮返回模型与配置模型一致。")
    if drift:
        st.warning("同一轮不同阶段返回了不同模型，代理路由可能存在漂移。")

    for stage in stages:
        usage = stage.get("usage") or {}
        usage_text = ", ".join(f"{key}={value}" for key, value in usage.items()) or "未返回"
        st.markdown(f"#### {stage.get('stage', 'unknown')}")
        st.markdown(f"- 配置模型：{stage.get('requested_model') or '未返回'}")
        st.markdown(f"- 实际返回模型：{stage.get('actual_model') or '未返回'}")
        st.markdown(f"- stop_reason：{stage.get('stop_reason') or '未返回'}")
        st.markdown(f"- 耗时：{stage.get('duration_seconds', '未返回')} 秒")
        st.markdown(f"- usage：{usage_text}")


def render_input_panel():
    priority_options = get_team_priority_options()

    st.markdown("<div class='panel-kicker'>结构化输入简报</div>", unsafe_allow_html=True)
    st.subheader("本轮讨论简报")
    st.caption("先定义这一轮要做什么，再补题材、边界和团队关注点，系统会把它整理成可讨论的结构化材料。")

    st.markdown("### 这一轮要做什么")
    st.radio(
        "工作模式",
        ["设定发散", "大纲诊断"],
        key="input_mode",
        horizontal=True,
    )
    st.caption(
        "设定发散：适合只有生活观察、角色关系或题材苗头时；大纲诊断：适合已经有方向或草稿时。"
    )

    st.markdown("### 题材与已有素材")
    st.text_area(
        "主题 / 生活观察 / 初步设定",
        key="input_topic",
        placeholder="例如：一个人把所有生活问题都当成项目管理问题来处理。",
        height=140,
    )
    st.text_area(
        "现有大纲 / 草稿 / 已有方向（可选）",
        key="input_existing_draft",
        placeholder="设定发散时可补充已有方向；大纲诊断时建议直接粘贴现有大纲或草稿。",
        height=140,
    )

    st.markdown("### 表演与边界信息")
    st.selectbox(
        "表演形式",
        ["短剧 / Sketch", "双人", "多人", "肢体", "音乐", "其他"],
        key="input_format_type",
    )
    st.selectbox("角色数量", ["1", "2", "3", "4+"], key="input_character_count")
    st.text_input("角色关系（可选）", key="input_character_relationship")
    st.text_input("这轮想打到什么观众感受", key="input_audience_feeling")
    st.text_area(
        "约束 / 边界 / 不想要什么",
        key="input_constraints",
        placeholder="例如：不要太像短视频段子；不要只有职场黑话；希望适合双人表演。",
        height=100,
    )

    with st.expander("团队这轮最关心什么（可选）", expanded=False):
        st.text_area("团队当前最担心什么", key="input_team_concern", height=90)
        priority_label = priority_options.get(st.session_state.input_team_priority, priority_options["clarity"])
        st.selectbox(
            "这轮最想优先解决什么",
            list(priority_options.values()),
            index=list(priority_options.values()).index(priority_label),
            key="_team_priority_label",
        )
        reverse_priority_options = {label: value for value, label in priority_options.items()}
        st.session_state.input_team_priority = reverse_priority_options[st.session_state._team_priority_label]

    c1, c2 = st.columns(2)
    with c1:
        generate = st.button("生成本轮讨论材料", use_container_width=True)
    with c2:
        load_example = st.button("载入示例简报", use_container_width=True, on_click=load_example_inputs)

    st.caption("设定发散会先给 3 个方向；大纲诊断会直接进入结构反馈与下一轮优先修改点。")

    if load_example:
        st.success("已载入示例简报，接下来会展示一轮完整的讨论输出。")

    return {
        "mode": st.session_state.input_mode,
        "topic": st.session_state.input_topic,
        "format_type": st.session_state.input_format_type,
        "character_count": st.session_state.input_character_count,
        "character_relationship": st.session_state.input_character_relationship,
        "audience_feeling": st.session_state.input_audience_feeling,
        "constraints": st.session_state.input_constraints,
        "existing_draft": st.session_state.input_existing_draft,
        "team_concern": st.session_state.input_team_concern,
        "team_priority": st.session_state.input_team_priority,
        "generate": generate,
    }


def render_premise_cards(premises):
    st.subheader("可供讨论的 3 个方向")
    st.caption("先挑一个最值得继续聊的方向，后面的三视角判断和修改建议会围绕它展开。")
    cols = st.columns(3)
    selected_index = None
    for idx, premise in enumerate(premises[:3]):
        with cols[idx]:
            with st.container(border=True):
                st.markdown(f"### {premise['title']}")
                st.markdown(f"**设定**：{premise['premise']}")
                st.markdown(f"**角色动态**：{premise.get('character_dynamic', '')}")
                st.markdown(f"**核心冲突**：{premise['core_conflict']}")
                st.markdown(f"**为什么可能成立**：{premise['why_it_might_work']}")
                st.markdown(f"**最大风险**：{premise['biggest_risk']}")
                st.markdown(f"**升级路径**：{premise['escalation_path']}")
                if st.button("选为本轮讨论焦点", key=f"use_{idx}"):
                    selected_index = idx
    return selected_index


def render_selected_direction(selected):
    with st.container(border=True):
        st.subheader("当前讨论焦点")
        st.caption("下面的三视角判断、新鲜度评估和下一轮建议，都会围绕这个方向展开。")
        st.markdown(f"**方向**：{selected['title']}")
        st.markdown(f"**概述**：{selected['summary']}")
        st.markdown(f"**形式**：{selected['format']}")
        st.markdown(f"**角色关系**：{selected['character_setup']}")
        st.markdown(f"**预期感受**：{selected['audience_feeling']}")


def render_three_role_critique(critique):
    st.subheader("三种创作视角的判断")
    st.caption("先看编剧、演员、导演分别在意什么，再决定团队要先对齐哪些问题。")
    cols = st.columns(3)
    mapping = [
        ("编剧视角", critique["writer"]),
        ("演员视角", critique["performer"]),
        ("导演视角", critique["director"]),
    ]
    for col, (title, content) in zip(cols, mapping):
        with col:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.markdown("**已经成立的点**")
                for item in content["what_works"]:
                    st.markdown(f"- {item}")
                st.markdown("**还偏弱的点**")
                for item in content["what_feels_weak"]:
                    st.markdown(f"- {item}")
                st.markdown("**这一视角最想先改什么**")
                for item in content["most_important_fix"]:
                    st.markdown(f"- {item}")

    st.markdown("### 优先对齐的问题")
    st.markdown("**大家基本同意的点**")
    for item in critique["synthesis"]["alignments"]:
        st.markdown(f"- {item}")
    st.markdown("**还没完全对齐的点**")
    for item in critique["synthesis"]["differences"]:
        st.markdown(f"- {item}")
    st.markdown("**建议下一轮先聊什么**")
    for item in critique["synthesis"]["next_discussion"]:
        st.markdown(f"- {item}")


def render_freshness_check(freshness):
    freshness_level_map = {
        "strong": "强",
        "medium": "中等",
        "weak": "偏弱",
        "Strong": "强",
        "Medium": "中等",
        "Weak": "偏弱",
    }
    overall = freshness_level_map.get(freshness.get("overall"), freshness.get("overall"))
    st.subheader("新鲜度判断：这个方向会不会落俗")
    st.caption("新鲜度不是附带检查，而是判断这个方向值不值得继续推进的核心标准之一。")
    st.markdown(f"**整体判断**：{overall}")
    st.markdown(f"**一句话诊断**：{freshness['diagnosis']}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**哪里有新鲜感**")
        for item in freshness["fresh_points"]:
            st.markdown(f"- {item}")
        st.markdown("**为什么会出现这个风险**")
        for item in freshness["why_risk"]:
            st.markdown(f"- {item}")
    with c2:
        st.markdown("**哪里容易落俗**")
        for item in freshness["generic_risks"]:
            st.markdown(f"- {item}")
        st.markdown("**如果继续做，优先往哪改**")
        for item in freshness["improvements"]:
            st.markdown(f"- {item}")


def render_consensus_alert(consensus):
    consensus_level_map = {
        "high": "高",
        "medium": "中等",
        "low": "低",
        "High": "高",
        "Medium": "中等",
        "Low": "低",
    }
    st.subheader("团队可先对齐的重点")
    st.info("如果团队要快速推进，可以先从下面这些三方都在意的点开始。")
    level = consensus.get("consensus_level")
    if level:
        st.caption(f"共识程度：{consensus_level_map.get(level, level)}")
    for item in consensus.get("shared_conclusions", []):
        st.markdown(f"- {item}")
    focus = consensus.get("recommended_focus")
    if focus:
        st.markdown(f"**建议优先讨论**：{focus}")
    reasoning = consensus.get("reasoning")
    if reasoning:
        with st.expander("查看补充说明", expanded=False):
            st.markdown(reasoning)


def render_freshness_remediation(remediations):
    st.subheader("补充可讨论的改写方向")
    st.warning("这个方向现在有一点熟悉感，因此这里补了 3 个可以继续往下聊的改写方向。")
    cols = st.columns(min(3, len(remediations))) if remediations else []
    for col, remediation in zip(cols, remediations[:3]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {remediation['what_to_change']}")
                st.markdown(f"**为什么像套路**：{remediation['why_its_cliche']}")
                st.markdown(f"**更新鲜的替代**：{remediation['fresh_alternative']}")
                st.markdown(f"**可以怎么转一下**：{remediation['example_twist']}")


_AGENT_LABEL_MAP = {
    "consensus_detector": ("三角色共识检测", "共识"),
    "freshness_guard": ("新鲜度修复", "新鲜"),
}

_SCORE_LABEL_MAP = {
    "premise_clarity": "设定清晰度",
    "conflict_engine": "冲突引擎",
    "escalation_potential": "升级潜力",
    "differentiation": "方向差异度",
    "specificity": "具体程度",
}


def _format_agent_error_label(agent_key: str, stage_key: str) -> str:
    agent_label_map = {
        "consensus_detector": "三角色共识检测",
        "freshness_guard": "新鲜度修复",
    }
    stage_label_map = {
        "consensus": "共识检测",
        "remediation": "新鲜度修复",
    }
    agent_label = agent_label_map.get(agent_key, agent_key or "智能体")
    stage_label = stage_label_map.get(stage_key, stage_key or "未知阶段")
    return f"{agent_label} · {stage_label}"


def _render_agent_trace_block(
    label: str,
    icon: str,
    trace: dict,
    quality_scores: dict | None = None,
) -> None:
    steps = trace.get("steps") or []
    total_retries = trace.get("total_retries", 0)
    duration = trace.get("total_duration_seconds")
    final_decision = trace.get("final_decision", "")

    st.markdown(f"#### {icon} · {label}")

    m1, m2, m3 = st.columns(3)
    m1.metric("推理步骤", len(steps))
    m2.metric("重试次数", total_retries)
    m3.metric("耗时", f"{duration:.1f}s" if isinstance(duration, (int, float)) else "—")

    if quality_scores and quality_scores.get("scores"):
        scores = quality_scores["scores"]
        avg = quality_scores.get("average", 0)
        passed = avg >= 3.5
        score_items = list(scores.items())
        cols = st.columns(len(score_items) + 1)
        for col, (key, val) in zip(cols, score_items):
            col.metric(_SCORE_LABEL_MAP.get(key, key), f"{val}/5")
        cols[-1].metric(
            "综合评分",
            f"{avg:.1f}/5",
            delta="通过" if passed else "未通过",
            delta_color="normal" if passed else "inverse",
        )

    for i, step in enumerate(steps):
        with st.container(border=True):
            st.markdown(f"**步骤 {i + 1}**")
            thought = step.get("thought", "")
            action = step.get("action", "")
            observation = step.get("observation", "")
            if thought:
                st.markdown(f"**思考**&emsp;{thought}")
            if action:
                st.markdown(f"**行动**&emsp;{action}")
            if observation:
                st.markdown(f"**观察**&emsp;{observation}")

    if final_decision:
        st.success(f"**最终决策**：{final_decision}")


def render_react_trace_panel() -> None:
    premise_trace = st.session_state.get("premise_agent_trace") or {}
    premise_scores = st.session_state.get("premise_quality_scores") or {}
    feedback_traces = st.session_state.get("agent_traces") or []
    agent_errors = st.session_state.get("agent_errors") or []

    has_premise_steps = bool(premise_trace.get("steps"))
    has_feedback_steps = any(t.get("steps") for t in feedback_traces)

    if not has_premise_steps and not has_feedback_steps and not agent_errors:
        return

    auto_expand = (premise_trace.get("total_retries") or 0) > 0

    with st.expander("智能体推理与治理过程", expanded=auto_expand):
        st.caption(
            "记录每个智能体的「思考 → 行动 → 观察」链路，用于展示质量自评、重试、共识检测与风险补救机制。"
        )

        if agent_errors:
            for err in agent_errors:
                st.error(
                    f"{_format_agent_error_label(err.get('agent', ''), err.get('stage', ''))}：{err.get('error', '')}"
                )
            st.divider()

        if has_premise_steps:
            _render_agent_trace_block(
                label="设定质量自评",
                icon="质量",
                trace=premise_trace,
                quality_scores=premise_scores,
            )

        for trace in feedback_traces:
            if not trace.get("steps"):
                continue
            agent_key = trace.get("agent", "agent")
            label, icon = _AGENT_LABEL_MAP.get(agent_key, (agent_key, "智能体"))
            st.divider()
            _render_agent_trace_block(
                label=label,
                icon=icon,
                trace=trace,
                quality_scores=None,
            )


def render_next_iteration_plan(moves):
    st.subheader("下一轮优先修改什么")
    st.caption("如果决定继续推进这个方向，建议先围绕下面 3 个动作展开讨论。")
    cols = st.columns(3)
    for col, move in zip(cols, moves[:3]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {move['move']}")
                st.markdown(f"**为什么重要**：{move['why']}")
                st.markdown(f"**更好版本可能是什么样**：{move['better_version']}")


def render_human_judgment_gate(items):
    st.subheader("人工判断提醒")
    st.warning("以下建议用于帮助讨论，不替代创作团队的最终判断。")
    for item in items:
        st.markdown(f"- {item}")


def render_prompt_debug():
    st.markdown("### 提示词与产品机制验证")
    st.caption("这里展示各阶段提示词，便于说明这个演示不是单轮提示词，而是分阶段智能体工作流。")
    for name, content in prompts.items():
        st.markdown(f"**{name}**")
        st.code(content[:800] + ("\n..." if len(content) > 800 else ""), language="markdown")


def render_debug_panel():
    has_runtime = bool(st.session_state.get("runtime_summary"))
    has_actions = bool(st.session_state.get("agent_actions"))

    if not has_runtime and not has_actions:
        return

    with st.expander("后台诊断 / 技术验证信息", expanded=False):
        st.caption("这里展示后台动作、模型返回与耗时信息，用于证明演示的真实调用链路和可排查性。")
        if has_actions:
            st.markdown("**后台触发的动作**")
            for action in (st.session_state.get("agent_actions") or []):
                st.markdown(f"- `{action}`")
        if has_runtime:
            render_runtime_diagnostics(st.session_state.runtime_summary)


def build_client() -> ClaudeClient:
    config = build_runtime_config(
        base_url=st.session_state.runtime_base_url,
        api_key=st.session_state.runtime_api_key,
        model=st.session_state.runtime_model,
    )
    missing_fields = get_missing_runtime_fields(config)
    if missing_fields:
        raise ValueError(f"请先补充模型配置：{', '.join(missing_fields)}")
    return ClaudeClient(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model,
    )


def validate_inputs(state, mode):
    if mode == "设定发散" and not state["topic"].strip():
        raise ValueError("设定发散模式至少需要填写主题 / 生活观察 / 初步设定。")
    if mode == "大纲诊断" and not (state["existing_draft"].strip() or state["topic"].strip()):
        raise ValueError("大纲诊断模式至少需要填写现有大纲 / 草稿，或更具体的题材设定。")


def run_premise_generation(state, client):
    clear_generation_state()
    reporter = ProgressReporter()
    reporter.start("正在发散设定方向…")
    reporter.update("premise", "正在发散设定方向…")
    result = generate_premise_options(client, state, on_progress=reporter.update)
    st.session_state.generated_premises = result["premises"]
    st.session_state.premise_quality_scores = result.get("quality_scores") or {}
    st.session_state.premise_agent_trace = result.get("agent_trace") or {}
    st.session_state.premise_passed = result.get("passed", True)
    reporter.complete("设定方向生成完成。")


def run_feedback_generation(state, selected_direction, client=None):
    st.session_state.pop("generation_error", None)
    if client is None:
        client = build_client()
    reporter = ProgressReporter()
    reporter.start("已选择方向，准备生成反馈…")
    reporter.update("prepare", "已选择方向，准备生成反馈…")
    st.session_state.selected_direction = selected_direction
    st.session_state.pop("critique", None)
    st.session_state.pop("freshness", None)
    st.session_state.pop("next_iteration_plan", None)
    st.session_state.pop("human_judgment_gate", None)
    st.session_state.pop("consensus_alert", None)
    st.session_state.pop("freshness_remediation", None)
    st.session_state.pop("agent_traces", None)
    st.session_state.pop("agent_actions", None)
    st.session_state.pop("agent_errors", None)
    st.session_state.pop("runtime_summary", None)

    if state.get("mode") == "大纲诊断":
        bundle = generate_outline_diagnosis_bundle(client, state, on_progress=reporter.update)
    else:
        bundle = generate_feedback_bundle(client, state, selected_direction, on_progress=reporter.update)

    st.session_state.selected_direction = bundle["selected_direction"]
    st.session_state.critique = bundle["critique"]
    st.session_state.freshness = bundle["freshness"]
    st.session_state.next_iteration_plan = bundle["next_iteration_plan"]
    st.session_state.human_judgment_gate = bundle["human_judgment_gate"]
    st.session_state.consensus_alert = bundle.get("consensus_alert")
    st.session_state.freshness_remediation = bundle.get("freshness_remediation")
    st.session_state.agent_traces = bundle.get("agent_traces") or []
    st.session_state.agent_actions = bundle.get("agent_actions") or []
    st.session_state.agent_errors = bundle.get("agent_errors") or []
    st.session_state.runtime_summary = bundle.get("runtime_summary") or {}
    _append_runtime_history(st.session_state.runtime_summary)
    reporter.complete("反馈生成完成。")


def handle_primary_action(state):
    should_generate = state["generate"] or st.session_state.pop("auto_run_example", False)
    if not should_generate:
        return

    try:
        client = build_client()
        selected_mode = state["mode"]

        validate_inputs(state, selected_mode)
        if selected_mode == "设定发散":
            run_premise_generation(state, client)
        else:
            clear_generation_state()
            selected_direction = build_selected_direction_from_outline(state)
            run_feedback_generation(state, selected_direction, client=client)
    except (ValueError, LLMClientError, TypeError, KeyError) as exc:
        st.session_state.generation_error = str(exc)


def render_results_workspace(state):
    st.markdown("<div class='panel-kicker'>智能体输出工作台</div>", unsafe_allow_html=True)

    if st.session_state.get("generation_error"):
        st.error(st.session_state.generation_error)

    selected_mode = state.get("mode", st.session_state.get("input_mode", "设定发散"))

    if selected_mode == "设定发散" and st.session_state.get("generated_premises"):
        selected_index = render_premise_cards(st.session_state.generated_premises)
        if selected_index is not None:
            selected_direction = build_selected_direction_from_premise(
                st.session_state.generated_premises[selected_index],
                state,
            )
            try:
                run_feedback_generation(state, selected_direction)
            except (ValueError, LLMClientError, TypeError, KeyError) as exc:
                st.session_state.generation_error = str(exc)
                st.error(st.session_state.generation_error)
                return

        if not st.session_state.get("selected_direction"):
            st.info("先从上面的 3 个方向里选一个，右侧就会继续展开三视角判断、新鲜度风险和下一轮讨论重点。")

    if st.session_state.get("selected_direction"):
        render_selected_direction(st.session_state.selected_direction)
    if st.session_state.get("critique"):
        render_three_role_critique(st.session_state.critique)
    if st.session_state.get("consensus_alert"):
        render_consensus_alert(st.session_state.consensus_alert)
    if st.session_state.get("freshness"):
        render_freshness_check(st.session_state.freshness)
    if st.session_state.get("freshness_remediation"):
        render_freshness_remediation(st.session_state.freshness_remediation)
    if st.session_state.get("next_iteration_plan"):
        render_next_iteration_plan(st.session_state.next_iteration_plan)
    if st.session_state.get("human_judgment_gate"):
        render_human_judgment_gate(st.session_state.human_judgment_gate)
    render_react_trace_panel()

    has_results = any(st.session_state.get(key) for key in RESULT_STATE_KEYS if key != "generation_error")
    if not has_results:
        st.subheader("本轮讨论输出板")
        st.info(
            "这是一个结构化智能体工作流演示，不是单轮提示词：先把输入压成讨论简报，再经过多角色评价、质量治理和人类判断边界。"
        )
        st.markdown("- 如果是**设定发散**，你会先看到 3 个可比较的方向。\n"
                    "- 如果是**大纲诊断**，你会直接看到结构反馈和下一轮修改重点。\n"
                    "- 接着会出现编剧 / 演员 / 导演三种视角的判断。\n"
                    "- 同时会补一层新鲜度风险和共识检测，帮助判断这个方向值不值得继续推。\n"
                    "- 最后带走下一轮最值得优先讨论的 3 个动作，并保留人工判断提醒。")


def main():
    initialize_session_state()
    inject_design_system()
    render_header()
    left, right = st.columns([1, 2], gap="large")

    with left:
        with st.container(border=True):
            state = render_input_panel()

    with right:
        with st.container(border=True):
            handle_primary_action(state)
            render_results_workspace(state)


if __name__ == "__main__":
    main()
