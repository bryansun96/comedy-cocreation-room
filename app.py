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
from v0_theme import build_v0_css

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
    --bg: #f6f9ff;
    --panel: rgba(255, 255, 255, 0.88);
    --panel-strong: rgba(255, 255, 255, 0.97);
    --panel-soft: rgba(232, 241, 255, 0.76);
    --line: rgba(73, 112, 174, 0.16);
    --line-strong: rgba(86, 136, 224, 0.30);
    --text: #16253f;
    --text-soft: rgba(22, 37, 63, 0.72);
    --text-faint: rgba(22, 37, 63, 0.48);
    --accent: #18b8a0;
    --accent-strong: #0f8f83;
    --blue: #5f8df7;
    --blue-strong: #2f62d9;
    --blue-soft: rgba(222, 234, 255, 0.82);
    --mint: #e9f8f4;
    --jade: #16b99e;
    --warm: #fffaf2;
    --radius-lg: 30px;
    --radius-md: 20px;
    --shadow-soft: 0 26px 76px rgba(47, 98, 217, 0.16);
    --shadow-card: 0 14px 40px rgba(46, 91, 164, 0.11);
    --font-sans: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    --font-serif: ui-serif, "Songti SC", "Noto Serif CJK SC", Georgia, serif;
    --font-mono: "SF Mono", "Cascadia Code", Menlo, monospace;
}

.stApp {
    background:
        radial-gradient(circle at 8% 2%, rgba(95, 141, 247, 0.30), transparent 30rem),
        radial-gradient(circle at 92% 0%, rgba(177, 207, 255, 0.44), transparent 28rem),
        radial-gradient(circle at 82% 74%, rgba(24, 184, 160, 0.10), transparent 22rem),
        radial-gradient(circle at 20% 92%, rgba(255, 250, 242, 0.86), transparent 32rem),
        linear-gradient(180deg, #f7faff 0%, #eff5ff 50%, #ffffff 100%);
    color: var(--text);
    font-family: var(--font-sans);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
        radial-gradient(rgba(95, 141, 247, 0.10) 1px, transparent 1px),
        radial-gradient(rgba(24, 184, 160, 0.045) 1px, transparent 1px);
    background-position: 0 0, 18px 18px;
    background-size: 36px 36px;
    mask-image: linear-gradient(to bottom, black, transparent 82%);
}

[data-testid="stAppViewContainer"] > .main {
    position: relative;
    z-index: 1;
}

[data-testid="stHeader"] {
    background: rgba(247, 252, 255, 0.72);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(140, 200, 255, 0.18);
}

.block-container {
    max-width: 1120px;
    padding-top: 2.4rem;
    padding-bottom: 5rem;
}

h1, h2, h3, p, li, label, span {
    color: var(--text);
}

h1 {
    font-family: var(--font-serif);
    letter-spacing: -0.065em;
}

h2, h3, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    font-family: var(--font-sans);
    letter-spacing: -0.035em;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
.stCaptionContainer {
    color: var(--text-soft);
    line-height: 1.78;
}

.hero-shell {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.74);
    border-radius: 42px;
    padding: clamp(30px, 6vw, 62px);
    margin: 10px 0 26px;
    background:
        radial-gradient(circle at 76% 12%, rgba(95, 141, 247, 0.22), transparent 24rem),
        radial-gradient(circle at 12% 18%, rgba(185, 211, 255, 0.48), transparent 27rem),
        radial-gradient(circle at 86% 88%, rgba(24, 184, 160, 0.10), transparent 18rem),
        linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(232, 241, 255, 0.86));
    box-shadow: var(--shadow-soft);
}

.hero-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(120deg, rgba(255, 255, 255, 0.62), transparent 42%),
        radial-gradient(circle at 10% 95%, rgba(246, 250, 255, 0.92), transparent 22rem);
    pointer-events: none;
}

.hero-content {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.72fr);
    gap: 34px;
    align-items: center;
}

.hero-kicker,
.panel-kicker,
.stage-label {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 8px;
    padding: 7px 13px;
    border: 1px solid rgba(34, 184, 164, 0.2);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.68);
    color: var(--accent-strong);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}

.hero-title {
    max-width: 10ch;
    margin: 22px 0 18px;
    color: var(--text);
    font-size: clamp(3.2rem, 7.2vw, 6.8rem);
    line-height: 0.95;
    letter-spacing: -0.08em;
}

.hero-lead {
    max-width: 720px;
    color: var(--text-soft);
    font-size: clamp(1.05rem, 1.7vw, 1.34rem);
    line-height: 1.85;
}

.hero-note {
    margin-top: 18px;
    color: var(--text-faint);
    font-size: 0.94rem;
}

.hero-console,
.hero-guide {
    display: grid;
    gap: 14px;
    padding: 22px;
    border: 1px solid rgba(255, 255, 255, 0.74);
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.62);
    box-shadow: var(--shadow-card);
    backdrop-filter: blur(16px);
}

.console-row,
.guide-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(76, 139, 164, 0.12);
    color: var(--text-soft);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.console-dot {
    display: inline-flex;
    width: 9px;
    height: 9px;
    margin-right: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 18px rgba(34, 184, 164, 0.46);
}

.console-grid,
.guide-list {
    display: grid;
    gap: 10px;
}

.console-metric,
.guide-item {
    display: grid;
    gap: 6px;
    padding: 14px;
    border: 1px solid rgba(76, 139, 164, 0.13);
    border-radius: 20px;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.80), rgba(232, 241, 255, 0.58));
}

.console-metric small,
.guide-item small {
    color: var(--accent-strong);
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.console-metric strong,
.guide-item strong {
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 1rem;
    line-height: 1.35;
}

.guide-item p {
    margin: 0;
    color: var(--text-soft);
    font-size: 0.88rem;
    line-height: 1.55;
}

.demo-steps {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: -2px 0 28px;
}

.demo-step {
    border: 1px solid rgba(255, 255, 255, 0.74);
    border-radius: 24px;
    padding: 18px;
    background: rgba(255, 255, 255, 0.68);
    box-shadow: var(--shadow-card);
}

.demo-step span {
    display: inline-flex;
    margin-bottom: 13px;
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
    line-height: 1.58;
}

.flow-section {
    margin: 18px 0 22px;
}

.flow-section-title {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 18px 0 12px;
}

.flow-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--blue-strong), var(--blue));
    color: white;
    font-family: var(--font-mono);
    font-weight: 800;
    box-shadow: 0 12px 24px rgba(34, 184, 164, 0.2);
}

.flow-section-title strong {
    font-size: 1.18rem;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(255, 255, 255, 0.78) !important;
    border-radius: var(--radius-lg) !important;
    background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(236, 244, 255, 0.80)) !important;
    box-shadow: var(--shadow-card);
}

[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-md) !important;
    background: rgba(255, 255, 255, 0.72) !important;
    overflow: hidden;
    box-shadow: 0 10px 28px rgba(49, 125, 143, 0.08);
}

[data-testid="stExpander"] summary {
    color: var(--text) !important;
    font-family: var(--font-sans);
}

.stAlert {
    border-radius: 20px;
    border: 1px solid rgba(34, 184, 164, 0.2);
    background: rgba(232, 241, 255, 0.68);
}

[data-testid="stStatusWidget"],
[data-testid="stStatus"] {
    border: 1px solid rgba(95, 141, 247, 0.18) !important;
    border-radius: 24px !important;
    background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(232, 241, 255, 0.78)) !important;
    box-shadow: var(--shadow-card) !important;
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
    background: rgba(76, 139, 164, 0.12) !important;
    border-radius: 999px !important;
    overflow: hidden !important;
}

[data-testid="stProgress"] > div > div,
[data-testid="stProgress"] > div > div > div,
[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, var(--blue-strong), var(--blue), var(--jade)) !important;
    border-radius: 999px !important;
}

[data-testid="stSpinner"] {
    color: var(--accent-strong) !important;
}

.stButton > button {
    min-height: 46px;
    border: 1px solid rgba(95, 141, 247, 0.28) !important;
    border-radius: 999px !important;
    background: linear-gradient(135deg, #2f62d9, #5f8df7 78%, #18b8a0) !important;
    color: #ffffff !important;
    font-family: var(--font-sans) !important;
    font-weight: 800 !important;
    box-shadow: 0 16px 34px rgba(47, 98, 217, 0.20);
    transition: transform 180ms ease, box-shadow 180ms ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 22px 46px rgba(47, 98, 217, 0.25);
}

.stTextInput,
.stTextArea {
    margin-bottom: 0.78rem;
}

.stTextInput input,
.stTextArea textarea {
    border: 1px solid rgba(76, 139, 164, 0.14) !important;
    border-radius: 22px !important;
    background: rgba(255, 255, 255, 0.84) !important;
    color: var(--text) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
    caret-color: var(--accent-strong) !important;
    transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}

.stTextArea textarea {
    min-height: 116px;
    line-height: 1.72 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: rgba(23, 49, 66, 0.34) !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(95, 141, 247, 0.52) !important;
    background: rgba(255, 255, 255, 0.96) !important;
    box-shadow:
        0 0 0 4px rgba(95, 141, 247, 0.13),
        0 12px 30px rgba(46, 91, 164, 0.09) !important;
}

[data-baseweb="select"] > div {
    border: 1px solid rgba(76, 139, 164, 0.14) !important;
    border-radius: 20px !important;
    background: rgba(255, 255, 255, 0.84) !important;
    color: var(--text) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
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
    border-color: rgba(95, 141, 247, 0.34) !important;
}

.stTextInput input:-webkit-autofill {
    -webkit-text-fill-color: var(--text) !important;
    box-shadow: 0 0 0 1000px rgba(255, 255, 255, 0.96) inset !important;
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
    border: 1px solid rgba(76, 139, 164, 0.12);
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.72);
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
    border-color: rgba(76, 139, 164, 0.12) !important;
}

code, pre {
    border-radius: 16px !important;
    background: rgba(234, 248, 252, 0.82) !important;
    color: #173142 !important;
}

@media (max-width: 980px) {
    .hero-content,
    .demo-steps {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def inject_design_system():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(build_v0_css(), unsafe_allow_html=True)


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
        <section class="editorial-hero">
            <div class="hero-copy">
                <div class="eyebrow">Comedy Co-Creation Room · A creative journey</div>
                <h1 class="hero-title">把一个喜剧点子，慢慢变成可以讨论的作品</h1>
                <div class="hero-bottom">
                    <p class="hero-lead">
                        从一句生活观察出发，经过方向选择、三种视角和风格收敛，
                        最后进入真正值得继续修改的头脑风暴。
                    </p>
                </div>
            </div>
        </section>
        <nav class="journey-line">
            <span>01 Drop the idea</span>
            <span>02 Choose a direction</span>
            <span>03 About the idea</span>
            <span>04 Keep it fresh</span>
            <span>05 Take the next step</span>
        </nav>
        <section class="chapter-heading">
            <div class="chapter-number">01</div>
            <div>
                <div class="chapter-kicker">Drop the idea</div>
                <h2 class="chapter-title">先把脑海中的想法，放进来</h2>
                <p class="chapter-intro">不用写完整剧本。一句观察、一个尴尬场面、两个人的关系，已经足够开始。</p>
            </div>
        </section>
        <div class="wave-mark"></div>
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
        st.text_input("模型名称", key="runtime_model", placeholder="例如：deepseek-v4-pro")
        st.caption(
            "这个区域用于验证真实模型调用链路；优先读取环境变量，也兼容通用模型代理配置。"
        )


class ProgressReporter:
    def __init__(self):
        self._status = None
        self._fallback = None
        self._supports_status = hasattr(st, "status")

    def start(self, label: str):
        if self._supports_status:
            self._status = st.status(label, expanded=True)
        else:
            self._fallback = st.empty()
            self._fallback.info(label)

    def update(self, step: str, label: str):
        if self._status is not None:
            self._status.update(label=label)
        elif self._fallback is not None:
            self._fallback.info(label)

    def complete(self, label: str):
        if self._status is not None:
            self._status.update(label=label, state="complete", expanded=False)
        elif self._fallback is not None:
            self._fallback.success(label)

    def error(self, label: str):
        if self._status is not None:
            self._status.update(label=label, state="error", expanded=False)
        elif self._fallback is not None:
            self._fallback.error(label)


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

    st.markdown("<div class='panel-kicker'>Step 1 · 先把想法放进来</div>", unsafe_allow_html=True)
    st.subheader("告诉我你现在手里有什么")
    st.caption("不用写完整剧本。可以只是一句生活观察、一个人物关系、一个尴尬场面，或者一段还没打磨好的草稿。")

    st.markdown("### 这次你想先做哪件事")
    st.radio(
        "选择任务",
        ["设定发散", "大纲诊断"],
        key="input_mode",
        horizontal=True,
        format_func=lambda option: {
            "设定发散": "我只有一个点子，先找 3 个方向",
            "大纲诊断": "我已经有草稿，想知道哪里弱",
        }.get(option, option),
    )
    st.caption(
        "如果你还没想清楚，就选第一个；如果已经有故事梗概、段落或草稿，就选第二个。"
    )

    st.markdown("### 点子或草稿")
    st.text_area(
        "主题 / 生活观察 / 初步想法",
        key="input_topic",
        placeholder="例如：一个人总是把生活里的小事当成正式项目来管理。",
        height=140,
    )
    st.text_area(
        "已有草稿 / 大概剧情（可选）",
        key="input_existing_draft",
        placeholder="如果你已经写了几句话或一段大概剧情，可以贴在这里；没有也没关系。",
        height=140,
    )

    st.markdown("### 角色和边界")
    st.selectbox(
        "大概想做成什么形式",
        ["短剧 / Sketch", "双人", "多人", "肢体", "音乐", "其他"],
        key="input_format_type",
    )
    st.selectbox("大概有几个角色", ["1", "2", "3", "4+"], key="input_character_count")
    st.text_input("角色之间是什么关系（可选）", key="input_character_relationship")
    st.text_input("希望观众看完有什么感觉", key="input_audience_feeling")
    st.text_area(
        "不想要什么 / 有哪些限制",
        key="input_constraints",
        placeholder="例如：不要太像短视频段子；不要只靠网络热梗；希望适合两个人演。",
        height=100,
    )

    with st.expander("如果你有特别担心的地方，可以补充在这里", expanded=False):
        st.text_area("你现在最担心这个点子哪里不成立", key="input_team_concern", height=90)
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
        generate = st.button("开始整理这个点子", use_container_width=True)
    with c2:
        load_example = st.button("先看一个示例", use_container_width=True, on_click=load_example_inputs)

    st.caption("下一步会把内容整理成可讨论的方向或反馈，不会直接替你写成最终剧本。")

    if load_example:
        st.success("已载入示例。你可以直接往下看一轮完整输出，也可以改成自己的想法再生成。")

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
    st.markdown("<div class='panel-kicker'>Step 2 · 先挑一个方向继续聊</div>", unsafe_allow_html=True)
    st.subheader("这里有 3 个可以发展的方向")
    st.caption("它们不是最终答案，而是 3 个可比较的走法。先选一个你最想继续看的方向，后面会围绕它给反馈。")
    cols = st.columns(3)
    selected_index = None
    for idx, premise in enumerate(premises[:3]):
        with cols[idx]:
            with st.container(border=True):
                st.markdown(f"### {premise['title']}")
                st.markdown(f"**这个点子在说什么**：{premise['premise']}")
                st.markdown(f"**人物关系**：{premise.get('character_dynamic', '')}")
                st.markdown(f"**好玩的冲突**：{premise['core_conflict']}")
                st.markdown(f"**为什么可能有戏**：{premise['why_it_might_work']}")
                st.markdown(f"**目前最大的风险**：{premise['biggest_risk']}")
                st.markdown(f"**可以怎么升级**：{premise['escalation_path']}")
                if st.button("我想继续看这个", key=f"use_{idx}"):
                    selected_index = idx
    return selected_index


def render_selected_direction(selected):
    with st.container(border=True):
        st.markdown("<div class='panel-kicker'>Step 3 · 当前选中的方向</div>", unsafe_allow_html=True)
        st.subheader("我们先围绕这个点子继续分析")
        st.caption("下面的反馈都会基于这个方向展开。你可以把它理解成一张临时草图，而不是最终定稿。")
        st.markdown(f"**方向**：{selected['title']}")
        st.markdown(f"**一句话说明**：{selected['summary']}")
        st.markdown(f"**形式**：{selected['format']}")
        st.markdown(f"**角色关系**：{selected['character_setup']}")
        st.markdown(f"**希望观众感受到**：{selected['audience_feeling']}")


def render_three_role_critique(critique):
    st.markdown("<div class='panel-kicker'>Step 4 · 从三个角度看看它稳不稳</div>", unsafe_allow_html=True)
    st.subheader("编剧、演员、导演会分别担心什么")
    st.caption("不用有专业背景也能看：编剧看故事结构，演员看角色好不好演，导演看现场或画面能不能成立。")
    cols = st.columns(3)
    mapping = [
        ("编剧视角", "看这个点子是否清楚、冲突能不能持续", critique["writer"]),
        ("演员视角", "看角色有没有可演的动作、态度和节奏", critique["performer"]),
        ("导演视角", "看场面、节奏和观众理解是否顺畅", critique["director"]),
    ]
    for col, (title, helper, content) in zip(cols, mapping):
        with col:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.caption(helper)
                st.markdown("**已经不错的地方**")
                for item in content["what_works"]:
                    st.markdown(f"- {item}")
                st.markdown("**还需要加强的地方**")
                for item in content["what_feels_weak"]:
                    st.markdown(f"- {item}")
                st.markdown("**这一角度最想先改**")
                for item in content["most_important_fix"]:
                    st.markdown(f"- {item}")

    st.markdown("### 这轮最值得先讨论的问题")
    st.markdown("**大家都比较同意的点**")
    for item in critique["synthesis"]["alignments"]:
        st.markdown(f"- {item}")
    st.markdown("**还没有完全想清楚的点**")
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
    st.subheader("这个点子会不会太像常见套路")
    st.caption("这里检查的不是“好不好笑”的最终结论，而是提醒它有没有太熟、太泛、太像别人已经做过的风险。")
    st.markdown(f"**整体判断**：{overall}")
    st.markdown(f"**一句话诊断**：{freshness['diagnosis']}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**哪里比较新鲜**")
        for item in freshness["fresh_points"]:
            st.markdown(f"- {item}")
        st.markdown("**为什么会有这个风险**")
        for item in freshness["why_risk"]:
            st.markdown(f"- {item}")
    with c2:
        st.markdown("**哪里可能太常见**")
        for item in freshness["generic_risks"]:
            st.markdown(f"- {item}")
        st.markdown("**如果继续做，可以先往哪改**")
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
    st.subheader("大家都在意的重点")
    st.info("如果想快速推进，可以先处理这些多个角度都提到的问题。")
    level = consensus.get("consensus_level")
    if level:
        st.caption(f"一致程度：{consensus_level_map.get(level, level)}")
    for item in consensus.get("shared_conclusions", []):
        st.markdown(f"- {item}")
    focus = consensus.get("recommended_focus")
    if focus:
        st.markdown(f"**建议优先讨论**：{focus}")
    reasoning = consensus.get("reasoning")
    if reasoning:
        with st.expander("为什么这样判断", expanded=False):
            st.markdown(reasoning)


def render_freshness_remediation(remediations):
    st.subheader("如果觉得太常见，可以试试这些转向")
    st.warning("这个方向现在有一点熟悉感，下面补了 3 个可以继续讨论的改写方向。")
    cols = st.columns(min(3, len(remediations))) if remediations else []
    for col, remediation in zip(cols, remediations[:3]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {remediation['what_to_change']}")
                st.markdown(f"**为什么现在像套路**：{remediation['why_its_cliche']}")
                st.markdown(f"**可以换成什么**：{remediation['fresh_alternative']}")
                st.markdown(f"**一个具体转法**：{remediation['example_twist']}")


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

    with st.expander("为什么会给出这些建议（调试信息）", expanded=auto_expand):
        st.caption(
            "这里记录系统如何生成、检查和必要时重试结果。普通使用时可以先不看，想了解后台过程时再展开。"
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
    st.markdown("<div class='panel-kicker'>Step 5 · 带走下一轮修改重点</div>", unsafe_allow_html=True)
    st.subheader("接下来先改哪 3 件事")
    st.caption("如果你想继续发展这个方向，可以先从下面 3 个动作开始，而不是一次性重写全部。")
    cols = st.columns(3)
    for col, move in zip(cols, moves[:3]):
        with col:
            with st.container(border=True):
                st.markdown(f"### {move['move']}")
                st.markdown(f"**为什么重要**：{move['why']}")
                st.markdown(f"**更好版本可能是什么样**：{move['better_version']}")


def render_human_judgment_gate(items):
    st.subheader("最后仍然需要人来判断")
    st.warning("这些建议只是帮你整理讨论方向。最后好不好笑、适不适合演、要不要继续做，仍然要由创作者自己决定。")
    for item in items:
        st.markdown(f"- {item}")


def render_prompt_debug():
    st.markdown("### 后台提示词预览")
    st.caption("这里给开发或演示排查使用，普通用户不需要理解这些内容。")
    for name, content in prompts.items():
        st.markdown(f"**{name}**")
        st.code(content[:800] + ("\n..." if len(content) > 800 else ""), language="markdown")


def render_debug_panel():
    has_runtime = bool(st.session_state.get("runtime_summary"))
    has_actions = bool(st.session_state.get("agent_actions"))

    if not has_runtime and not has_actions:
        return

    with st.expander("后台诊断（调试用）", expanded=False):
        st.caption("这里展示模型调用、耗时和后台动作。普通体验时可以忽略。")
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
    st.markdown("<div class='panel-kicker'>整理结果</div>", unsafe_allow_html=True)

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
            st.info("先从上面的 3 个方向里选一个，下面就会继续展开三种视角的反馈、套路风险和下一轮修改重点。")

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
        st.subheader("第二步：结果会出现在这里")
        st.info(
            "填写上面的内容后，我会把它整理成几个可以讨论的部分。你不需要懂喜剧行业术语，只要按顺序往下看就可以。"
        )
        st.markdown("- 如果你选择**我只有一个点子**，会先看到 3 个不同发展方向。\n"
                    "- 如果你选择**我已经有草稿**，会直接看到哪里清楚、哪里还弱。\n"
                    "- 后面会分别从故事结构、角色表演、现场呈现三个角度给反馈。\n"
                    "- 还会提醒这个点子会不会太像常见套路。\n"
                    "- 最后会给你 3 个下一轮最值得先改的动作。")


def main():
    initialize_session_state()
    inject_design_system()
    render_header()

    with st.container(border=True):
        state = render_input_panel()

    st.markdown(
        """
        <section class="photo-break">
            <div class="photo-quote">好点子不必一开始就完整，它只需要一个值得落地的锚点。</div>
        </section>
        <section class="flow-section">
            <div class="flow-section-title">
                <span class="flow-number">02</span>
                <strong>让想法进入真实的整理与反馈</strong>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        handle_primary_action(state)
        render_results_workspace(state)


if __name__ == "__main__":
    main()
