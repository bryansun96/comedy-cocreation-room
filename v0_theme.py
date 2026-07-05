from __future__ import annotations

import base64
from pathlib import Path


ASSET_DIR = Path(__file__).parent / "assets" / "photos"


def _image_data(filename: str) -> str:
    payload = (ASSET_DIR / filename).read_bytes()
    return f"data:image/jpeg;base64,{base64.b64encode(payload).decode('ascii')}"


def build_v0_css() -> str:
    hero = _image_data("ocean-sand.jpg")
    cliffs = _image_data("hawaii-cliffs.jpg")
    sunset = _image_data("coast-sunset.jpg")
    return f"""
<style>
:root {{
    --paper: #eee8dc;
    --paper-light: #f7f3eb;
    --paper-dark: #ded5c5;
    --ink: #292a26;
    --sage: #777968;
    --sage-dark: #55594d;
    --terracotta: #a45f43;
    --terracotta-soft: #c98f72;
    --line: rgba(41, 42, 38, 0.22);
    --display: "Iowan Old Style", "Baskerville", "Noto Serif SC",
        "Songti SC", "STSong", Georgia, serif;
    --sans: "Avenir Next Condensed", "Avenir Next", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}}

html {{
    scroll-behavior: smooth;
}}

.stApp {{
    color: var(--ink);
    background:
        radial-gradient(circle at 20% 4%, rgba(255,255,255,.56), transparent 22rem),
        linear-gradient(180deg, var(--paper-light), var(--paper) 30%, #e8e0d3 100%);
    font-family: var(--sans);
}}

.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    opacity: .28;
    background-image:
        repeating-linear-gradient(0deg, rgba(70,60,45,.035) 0 1px, transparent 1px 4px),
        radial-gradient(rgba(80,65,45,.10) .6px, transparent .8px);
    background-size: auto, 5px 5px;
    mix-blend-mode: multiply;
}}

[data-testid="stAppViewContainer"] > .main {{
    position: relative;
    z-index: 1;
}}

[data-testid="stHeader"] {{
    background: rgba(238, 232, 220, .75);
    border-bottom: 1px solid rgba(41,42,38,.08);
    backdrop-filter: blur(14px);
}}

[data-testid="stToolbar"],
[data-testid="stDecoration"] {{
    display: none;
}}

.block-container {{
    max-width: 1180px;
    padding: 1.25rem 2.4rem 6rem;
}}

h1, h2, h3, p, li, label, span {{
    color: var(--ink);
}}

h1, h2, h3 {{
    font-family: var(--display);
    font-weight: 500;
    text-wrap: balance;
}}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
.stCaptionContainer {{
    line-height: 1.82;
}}

.editorial-hero {{
    min-height: min(810px, 88vh);
    margin: 0 0 104px;
    padding: clamp(34px, 6vw, 76px);
    position: relative;
    overflow: hidden;
    display: grid;
    align-content: end;
    background:
        linear-gradient(90deg, rgba(31,32,28,.70) 0%, rgba(31,32,28,.30) 46%, rgba(31,32,28,.04) 100%),
        linear-gradient(180deg, rgba(238,232,220,.05), rgba(41,42,38,.20)),
        url("{hero}") center 56% / cover;
}}

.editorial-hero::after {{
    content: "";
    position: absolute;
    width: 180px;
    height: 180px;
    right: 7%;
    top: 11%;
    border: 1px solid rgba(247,243,235,.62);
    border-radius: 50%;
    box-shadow:
        0 0 0 20px rgba(247,243,235,.05),
        0 0 0 42px rgba(247,243,235,.035);
}}

.hero-copy {{
    position: relative;
    z-index: 2;
    max-width: 850px;
}}

.eyebrow, .chapter-kicker, .card-index, .tiny-label {{
    font-family: var(--sans);
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .22em;
    text-transform: uppercase;
}}

.eyebrow {{
    color: #f5efe5;
    margin-bottom: 20px;
}}

.hero-title {{
    max-width: 10ch;
    margin: 0;
    color: #fffaf1 !important;
    font-family: var(--display) !important;
    font-size: clamp(3.9rem, 8vw, 7.8rem);
    font-weight: 400;
    line-height: .96;
    letter-spacing: -.055em;
}}

.hero-bottom {{
    margin-top: 34px;
    max-width: 600px;
    display: flex;
    align-items: flex-end;
    gap: 26px;
}}

.hero-lead {{
    margin: 0;
    color: rgba(255,250,241,.88);
    font-size: 1rem;
    line-height: 1.9;
}}

.journey-line {{
    display: flex;
    justify-content: space-between;
    gap: 24px;
    padding: 16px 0 20px;
    margin: -72px 0 86px;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
}}

.journey-line span {{
    color: var(--sage-dark);
    font-size: .69rem;
    letter-spacing: .12em;
    text-transform: uppercase;
}}

.chapter-heading {{
    display: grid;
    grid-template-columns: 120px 1fr;
    align-items: start;
    gap: 30px;
    margin: 0 0 42px;
    padding-top: 34px;
    border-top: 1px solid var(--line);
}}

.chapter-number {{
    color: var(--terracotta);
    font-family: var(--display);
    font-size: 3.2rem;
    font-style: italic;
    line-height: 1;
}}

.chapter-kicker {{
    margin: 4px 0 11px;
    color: var(--terracotta);
}}

.chapter-title {{
    max-width: 780px;
    margin: 0;
    font-family: var(--display) !important;
    font-size: clamp(2.6rem, 5.4vw, 5.3rem);
    line-height: 1.02;
    letter-spacing: -.045em;
}}

.chapter-intro {{
    max-width: 650px;
    margin: 17px 0 0;
    color: var(--sage-dark);
    font-size: 1rem;
}}

.wave-mark {{
    height: 54px;
    margin: 6px 0 30px;
    overflow: hidden;
    position: relative;
}}

.wave-mark::before,
.wave-mark::after {{
    content: "";
    position: absolute;
    width: 58%;
    height: 70px;
    border: 1px solid var(--terracotta);
    border-color: var(--terracotta) transparent transparent transparent;
    border-radius: 50%;
    top: 23px;
}}

.wave-mark::before {{ left: -8%; transform: rotate(3deg); }}
.wave-mark::after {{ left: 39%; transform: rotate(-4deg); }}

[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 1px solid rgba(41,42,38,.18) !important;
    border-radius: 8px !important;
    background: rgba(247,243,235,.64) !important;
    box-shadow: 0 16px 45px rgba(64,52,35,.07);
}}

[data-testid="stVerticalBlockBorderWrapper"] > div {{
    padding: clamp(18px, 3vw, 34px);
}}

.panel-kicker {{
    display: inline-flex;
    width: fit-content;
    margin-bottom: 12px;
    color: var(--terracotta) !important;
    font-family: var(--sans);
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .16em;
    text-transform: uppercase;
}}

.flow-section {{
    margin: 88px 0 28px;
}}

.flow-section-title {{
    display: grid;
    grid-template-columns: 90px 1fr;
    gap: 24px;
    align-items: center;
    padding-top: 25px;
    border-top: 1px solid var(--line);
}}

.flow-number {{
    display: block;
    width: auto;
    height: auto;
    color: var(--terracotta) !important;
    background: none !important;
    box-shadow: none !important;
    font-family: var(--display);
    font-size: 2.7rem;
    font-style: italic;
    font-weight: 400;
}}

.flow-section-title strong {{
    color: var(--ink);
    font-family: var(--display);
    font-size: clamp(1.8rem, 3vw, 2.8rem);
    font-weight: 500;
}}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="select"] > div {{
    border: 0 !important;
    border-bottom: 1px solid rgba(41,42,38,.4) !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: var(--ink) !important;
    box-shadow: none !important;
}}

.stTextInput input:focus,
.stTextArea textarea:focus,
[data-baseweb="select"] > div:focus-within {{
    border-bottom-color: var(--terracotta) !important;
    box-shadow: 0 2px 0 var(--terracotta) !important;
}}

.stTextArea textarea {{
    min-height: 116px;
}}

[data-testid="stRadio"] label,
[data-testid="stSelectbox"] label,
[data-testid="stTextArea"] label,
[data-testid="stTextInput"] label {{
    color: var(--sage-dark) !important;
    font-family: var(--sans);
}}

.stButton > button {{
    min-height: 48px;
    border: 1px solid var(--ink) !important;
    border-radius: 2px !important;
    background: var(--ink) !important;
    color: var(--paper-light) !important;
    font-family: var(--sans) !important;
    font-size: .78rem !important;
    font-weight: 700 !important;
    letter-spacing: .08em;
    box-shadow: none !important;
    transition: background 180ms ease, color 180ms ease, transform 180ms ease;
}}

.stButton > button p,
.stButton > button span {{
    color: var(--paper-light) !important;
}}

.stButton > button:hover {{
    background: var(--terracotta) !important;
    border-color: var(--terracotta) !important;
    transform: translateY(-2px);
}}

.photo-break {{
    min-height: 460px;
    margin: 104px 0;
    padding: 44px;
    position: relative;
    display: grid;
    align-items: end;
    overflow: hidden;
    background:
        linear-gradient(180deg, transparent 25%, rgba(25,27,24,.62)),
        url("{cliffs}") center / cover;
}}

.photo-break::before {{
    content: "LET THE IDEA BREATHE";
    position: absolute;
    right: 26px;
    top: 28px;
    color: rgba(255,255,255,.8);
    font-size: .68rem;
    letter-spacing: .2em;
}}

.photo-quote {{
    max-width: 650px;
    color: rgba(255, 250, 241, .72);
    font-family: var(--display) !important;
    font-size: clamp(2.2rem, 4.6vw, 4.4rem);
    line-height: 1.03;
}}

.direction-card {{
    min-height: 390px;
    padding: 28px 25px;
    display: flex;
    flex-direction: column;
    border-top: 1px solid var(--ink);
    border-bottom: 1px solid var(--line);
    background: rgba(247,243,235,.50);
    transition: transform 220ms ease, background 220ms ease;
}}

.direction-card:hover {{
    transform: translateY(-6px);
    background: rgba(247,243,235,.88);
}}

.direction-card.offset {{
    margin-top: 48px;
}}

.card-index {{
    color: var(--terracotta);
}}

.direction-card h3 {{
    margin: 40px 0 16px;
    font-family: var(--display) !important;
    font-size: 2rem;
    line-height: 1.08;
}}

.direction-card p {{
    color: var(--sage-dark);
}}

.direction-card .risk {{
    margin-top: auto;
    padding-top: 22px;
    border-top: 1px solid var(--line);
    font-size: .83rem;
}}

.about-shell {{
    margin: 118px 0 92px;
    padding: 80px clamp(26px, 5vw, 72px);
    background: #d9d5c8;
    border: 1px solid rgba(41,42,38,.16);
}}

.about-header {{
    text-align: center;
    margin-bottom: 72px;
}}

.about-step-number {{
    margin: 0 auto 10px;
    color: var(--terracotta);
    font-family: var(--display) !important;
    font-size: 3.2rem;
    font-style: italic;
}}

.about-header h2 {{
    margin: 0;
    font-family: var(--display) !important;
    font-size: clamp(3.6rem, 8vw, 7.8rem);
    line-height: .88;
    letter-spacing: -.06em;
}}

.about-header p {{
    color: var(--terracotta);
    font-family: var(--display);
    font-size: 1.55rem;
    font-style: italic;
}}

.role-grid {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
}}

.sun-illustration {{
    width: 94px;
    height: 94px;
    margin: 30px auto;
    position: relative;
    border: 1.5px solid var(--terracotta);
    border-radius: 50%;
}}

.sun-illustration::before,
.sun-illustration::after {{
    content: "";
    position: absolute;
    left: -32px;
    right: -32px;
    top: 45px;
    border-top: 1px solid var(--terracotta);
}}

.sun-illustration::after {{
    transform: rotate(90deg);
}}

.role-card {{
    min-height: 360px;
    padding: 8px 25px 28px;
    border-left: 1px solid rgba(41,42,38,.28);
}}

.role-card h3 {{
    margin: 20px 0 22px;
    font-family: var(--display) !important;
    font-size: 2.1rem;
}}

.role-card p,
.role-card li {{
    color: #4f5149;
    font-size: .94rem;
}}

.fresh-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    margin-bottom: 96px;
    background: var(--line);
    border: 1px solid var(--line);
}}

.fresh-panel {{
    min-height: 340px;
    padding: clamp(28px, 4vw, 54px);
    background: var(--paper-light);
}}

.fresh-panel.dark {{
    color: #f4eee4;
    background:
        linear-gradient(rgba(37,39,35,.66), rgba(37,39,35,.78)),
        url("{cliffs}") 68% center / cover;
}}

.fresh-panel.dark h3,
.fresh-panel.dark p,
.fresh-panel.dark .tiny-label {{
    color: rgba(244, 238, 228, .70) !important;
}}

.fresh-panel h3 {{
    margin: 40px 0 20px;
    font-family: var(--display) !important;
    font-size: 2.5rem;
}}

.timeline {{
    margin: 30px 0 100px;
    border-top: 1px solid var(--ink);
}}

.timeline-row {{
    display: grid;
    grid-template-columns: 110px 1fr 1.1fr;
    gap: 34px;
    padding: 28px 0;
    border-bottom: 1px solid var(--line);
}}

.timeline-row .time {{
    color: var(--terracotta);
    font-family: var(--display);
    font-size: 2.3rem;
    font-style: italic;
}}

.timeline-row h3 {{
    margin: 4px 0;
    font-family: var(--display) !important;
    font-size: 1.55rem;
}}

.timeline-row p {{
    margin: 5px 0;
    color: var(--sage-dark);
}}

.closing-photo {{
    min-height: 590px;
    margin: 88px 0 24px;
    padding: clamp(32px, 6vw, 72px);
    display: grid;
    align-content: end;
    background:
        linear-gradient(180deg, rgba(35,35,30,.04), rgba(35,35,30,.68)),
        url("{sunset}") center / cover;
}}

.closing-photo h2 {{
    max-width: 760px;
    margin: 0;
    color: #fffaf1 !important;
    font-family: var(--display) !important;
    font-size: clamp(3rem, 6vw, 6.4rem);
    line-height: .98;
    opacity: .58 !important;
}}

.closing-photo p {{
    color: rgba(255,250,241,.62) !important;
}}

.closing-photo .eyebrow {{
    color: rgba(255,250,241,.58) !important;
}}

/* Keep the step-04 heading and its paragraph on the exact same rendered color. */
.fresh-grid .fresh-panel.dark h3,
.fresh-grid .fresh-panel.dark p {{
    color: rgba(244, 238, 228, .70) !important;
    -webkit-text-fill-color: rgba(244, 238, 228, .70) !important;
    opacity: 1 !important;
}}

[data-testid="stExpander"] {{
    border: 1px solid rgba(41,42,38,.17) !important;
    border-radius: 4px !important;
    background: rgba(247,243,235,.4) !important;
}}

[data-testid="stStatusWidget"],
[data-testid="stStatus"] {{
    border: 1px solid rgba(41,42,38,.24) !important;
    border-radius: 5px !important;
    background: rgba(247,243,235,.78) !important;
    box-shadow: 0 14px 34px rgba(64,52,35,.07) !important;
}}

[data-testid="stStatusWidget"]::before,
[data-testid="stStatus"]::before {{
    content: "IN PROGRESS";
    display: block;
    padding: 10px 16px 0;
    color: var(--terracotta);
    font-family: var(--sans);
    font-size: .62rem;
    font-weight: 700;
    letter-spacing: .18em;
}}

[data-testid="stStatusWidget"] p,
[data-testid="stStatus"] p,
[data-testid="stProgress"] p {{
    color: var(--sage-dark) !important;
    font-family: var(--sans) !important;
}}

[data-testid="stProgress"] > div {{
    height: 3px !important;
    overflow: hidden;
    border-radius: 0 !important;
    background: rgba(41,42,38,.12) !important;
}}

[data-testid="stProgress"] > div > div,
[data-testid="stProgress"] > div > div > div,
[data-testid="stProgress"] > div > div > div > div {{
    border-radius: 0 !important;
    background: var(--terracotta) !important;
}}

[data-testid="stSpinner"] {{
    color: var(--terracotta) !important;
}}

[data-testid="stSpinner"] > div {{
    border-top-color: var(--terracotta) !important;
}}

@keyframes gentle-rise {{
    from {{ opacity: 0; transform: translateY(18px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.chapter-heading, .direction-card, .about-shell, .fresh-grid, .timeline {{
    animation: gentle-rise 600ms cubic-bezier(.22,.65,.3,1) both;
}}

@media (max-width: 760px) {{
    .block-container {{
        padding: .6rem 1rem 4rem;
    }}
    .editorial-hero {{
        min-height: 720px;
        margin-bottom: 72px;
        padding: 28px 22px;
        background-position: 58% center;
    }}
    .editorial-hero::after {{
        width: 106px;
        height: 106px;
        right: 6%;
    }}
    .hero-title {{
        font-size: clamp(3.6rem, 16vw, 5.5rem);
    }}
    .hero-bottom {{
        display: block;
    }}
    .journey-line {{
        overflow-x: auto;
        justify-content: flex-start;
    }}
    .journey-line span {{
        min-width: max-content;
    }}
    .chapter-heading {{
        grid-template-columns: 56px 1fr;
        gap: 12px;
    }}
    .flow-section-title {{
        grid-template-columns: 56px 1fr;
        gap: 12px;
    }}
    .chapter-number {{
        font-size: 2.4rem;
    }}
    .photo-break {{
        min-height: 420px;
        margin: 72px 0;
        padding: 24px;
    }}
    .direction-card.offset {{
        margin-top: 0;
    }}
    .about-shell {{
        margin: 80px 0 70px;
        padding: 60px 18px;
    }}
    .role-card {{
        min-height: 0;
        margin-bottom: 34px;
    }}
    .role-grid {{
        grid-template-columns: 1fr;
    }}
    .fresh-grid {{
        grid-template-columns: 1fr;
    }}
    .timeline-row {{
        grid-template-columns: 66px 1fr;
        gap: 14px;
    }}
    .timeline-row > p {{
        grid-column: 2;
    }}
    .closing-photo {{
        min-height: 520px;
        margin-top: 60px;
        padding: 28px 22px;
    }}
}}

@media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior: auto; }}
    *, *::before, *::after {{
        animation: none !important;
        transition: none !important;
    }}
}}
</style>
"""
