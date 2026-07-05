from __future__ import annotations

import streamlit as st

from v0_theme import build_v0_css


st.set_page_config(
    page_title="喜剧点子共创小助手 · Visual V0",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(build_v0_css(), unsafe_allow_html=True)


def chapter(number: str, kicker: str, title: str, intro: str) -> None:
    st.markdown(
        f"""
        <section class="chapter-heading">
            <div class="chapter-number">{number}</div>
            <div>
                <div class="chapter-kicker">{kicker}</div>
                <h2 class="chapter-title">{title}</h2>
                <p class="chapter-intro">{intro}</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


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
    """,
    unsafe_allow_html=True,
)

chapter(
    "01",
    "Drop the idea",
    "先把脑海中的想法，放进来",
    "不用写完整剧本。一句观察、一个尴尬场面、两个人的关系，已经足够开始。",
)
st.markdown('<div class="wave-mark"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### 这次想先做哪件事？")
    st.radio(
        "创作模式",
        ["我只有一个点子，先找 3 个方向", "我已经有草稿，想知道哪里弱"],
        horizontal=True,
        label_visibility="collapsed",
    )
    left, right = st.columns([1.25, 0.75])
    with left:
        st.text_area(
            "主题 / 生活观察 / 初步想法",
            value="一个人把所有生活问题都当成项目管理问题来处理。",
            height=150,
        )
        st.text_area(
            "不想要什么 / 有哪些限制",
            value="不要太像短视频段子；希望适合双人表演；不要只有职场黑话。",
            height=110,
        )
    with right:
        st.selectbox("想做成什么形式", ["双人", "短剧 / Sketch", "多人", "肢体", "音乐"])
        st.selectbox("大概有几个角色", ["2", "1", "3", "4+"])
        st.text_input("角色关系", value="一位情绪驱动，一位方法论驱动")
        st.text_input("观众感受", value="尴尬升级、强共鸣、角色反差")
    b1, b2, spacer = st.columns([1, 1, 1.3])
    with b1:
        st.button("开始整理这个点子", use_container_width=True)
    with b2:
        st.button("换一个示例", use_container_width=True)

st.markdown(
    """
    <section class="photo-break">
        <div class="photo-quote">好点子不必一开始就完整，它只需要一个值得落地的锚点。</div>
    </section>
    """,
    unsafe_allow_html=True,
)

chapter(
    "02",
    "Choose a direction",
    "同一个观察，也可以长成三种完全不同的喜剧",
    "它们不是最终答案，而是三条可比较的路。先看哪一种最让你想继续往下聊。",
)

directions = [
    (
        "01 / CONTROL",
        "人生项目经理",
        "他为朋友的失恋制定了一份七阶段恢复计划，却因为对方提前开心起来而陷入项目失控。",
        "风险：容易停留在职场黑话，需要让方法真正改变两个人的行动。",
    ),
    (
        "02 / REVERSE",
        "被流程反向管理",
        "所有表格、提醒和自动化工具开始要求他证明自己的人生正在按计划推进。",
        "风险：设定很新，但必须尽快落到可表演的具体场景。",
    ),
    (
        "03 / RELATIONSHIP",
        "临时搭档，永久复盘",
        "一个只想被安慰的人，被迫参加一场关于“如何正确接受安慰”的复盘会。",
        "风险：人物对撞清楚，但升级不能只是重复争吵。",
    ),
]

cols = st.columns(3)
for index, (label, title, body, risk) in enumerate(directions):
    with cols[index]:
        offset = " offset" if index == 1 else ""
        st.markdown(
            f"""
            <article class="direction-card{offset}">
                <div class="card-index">{label}</div>
                <h3>{title}</h3>
                <p>{body}</p>
                <p class="risk">{risk}</p>
            </article>
            """,
            unsafe_allow_html=True,
        )
        st.button("继续看这个方向", key=f"direction_{index}", use_container_width=True)

roles = [
    (
        "编剧视角",
        "Writer",
        "角色目标很清楚：他想把一切重新变得可控。",
        ["让每次升级都来自上一次解决方案", "给搭档一个同样强烈但相反的目标"],
    ),
    (
        "演员视角",
        "Performer",
        "最好玩的不是术语，而是他真的相信流程能照顾别人。",
        ["把焦虑藏进过分镇定的动作里", "设计一个不断被打断的固定仪式"],
    ),
    (
        "导演视角",
        "Director",
        "现场需要一眼看懂的秩序，以及秩序逐渐崩坏的视觉变化。",
        ["让道具从整齐到失控", "最后留一个安静、反常的小停顿"],
    ),
]

role_markup = "".join(
    (
        f'<article class="role-card">'
        f'<div class="tiny-label">{en}</div>'
        f"<h3>{title}</h3>"
        f"<p>{summary}</p>"
        f"<ul><li>{bullets[0]}</li><li>{bullets[1]}</li></ul>"
        f"</article>"
    )
    for title, en, summary, bullets in roles
)
st.markdown(
    (
        '<section class="about-shell">'
        '<header class="about-header">'
        '<div class="chapter-number about-step-number">03</div>'
        '<div class="chapter-kicker">Three ways of seeing</div>'
        "<h2>About the Idea</h2>"
        "<p>从纸面，到角色，再到现场</p>"
        '<div class="sun-illustration" aria-hidden="true"></div>'
        "</header>"
        f'<div class="role-grid">{role_markup}</div>'
        "</section>"
    ),
    unsafe_allow_html=True,
)

chapter(
    "04",
    "Keep it fresh",
    "退后一步，看看它是不是正走向熟悉的套路",
    "新鲜感不一定来自奇怪的设定，也可能来自角色为什么非得这么做。",
)
st.markdown(
    """
    <section class="fresh-grid">
        <article class="fresh-panel dark">
            <div class="tiny-label">What feels alive</div>
            <h3>这个角色是真的想做些什么</h3>
            <p>
                如果他只是一个爱说黑话的讨厌鬼，笑点会很快耗尽。
                让观众看见他的笨拙善意，冲突才会同时好笑和让人心疼。
            </p>
        </article>
        <article class="fresh-panel">
            <div class="tiny-label">What feels familiar</div>
            <h3>“感性对理性”太容易被猜到</h3>
            <p>
                不要让另一个角色只负责反对。更有趣的版本是：
                对方比他更擅长利用流程，最后反过来要求他直面自己的情绪。
            </p>
        </article>
    </section>
    """,
    unsafe_allow_html=True,
)

chapter(
    "05",
    "Take the next step",
    "下一轮，不必全部重写，只做这三件事",
    "把讨论收束成动作，让团队知道下一次坐下来时应该从哪里继续。",
)
st.markdown(
    """
    <section class="timeline">
        <div class="timeline-row">
            <div class="time">01</div>
            <h3>先写出双方真正想要什么</h3>
            <p>不要使用“理性”和“感性”这样的抽象词，改成一句能直接表演的目标。</p>
        </div>
        <div class="timeline-row">
            <div class="time">02</div>
            <h3>让解决方案制造下一轮麻烦</h3>
            <p>每一次整理、提醒或复盘，都必须留下一个更具体、更难收拾的新问题。</p>
        </div>
        <div class="timeline-row">
            <div class="time">03</div>
            <h3>设计一个不靠台词的崩坏时刻</h3>
            <p>用道具、站位和节奏证明秩序已经失效，给观众一次视觉上的兑现。</p>
        </div>
    </section>
    <section class="closing-photo">
        <div>
            <div class="eyebrow">The work continues</div>
            <h2>先带走一个更清楚的问题，再继续写。</h2>
            <p>这不是最终答案，只是下一次好讨论的起点。</p>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.expander("关于这个视觉样例"):
    st.markdown(
        """
        - 这是独立 v0，不调用模型、不写入现有业务状态。
        - 海岸照片已存入项目本地；正式版本会补充完整摄影署名。
        - 太阳与海浪为 CSS 原创线描，没有复用参考网站素材。
        - 后续可将这套视觉语言迁移到正式 `app.py`。
        """
    )
