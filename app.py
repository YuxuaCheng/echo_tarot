import os
import random
import openai
import streamlit as st

from tarot_data import TAROT_DECK, SUIT_SYMBOLS, SUIT_NAMES_CN
from prompts import (
    ECHO_SYSTEM_PROMPT,
    SPREAD_DESCRIPTIONS,
    build_reading_prompt,
    build_diary_prompt,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Echo · 塔罗",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Lora:ital,wght@0,400;0,500;1,400;1,500&display=swap');

/* ── Base ── */
.stApp { background-color: #0c0c18 !important; }
.block-container { max-width: 720px !important; padding-top: 2rem !important; }
* { font-family: 'Lora', 'PingFang SC', serif; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Typography ── */
h1, h2, h3, .echo-title { font-family: 'Cinzel', serif !important; }

/* ── Brand header ── */
.echo-header {
    text-align: center;
    padding: 2.5rem 0 1rem;
}
.echo-title {
    font-family: 'Cinzel', serif;
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: 0.25em;
    background: linear-gradient(135deg, #c9a227 0%, #f0d060 50%, #c9a227 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
}
.echo-subtitle {
    color: #8a7050;
    font-size: 0.95rem;
    letter-spacing: 0.15em;
    margin-top: 0.5rem;
    font-style: italic;
}
.echo-divider {
    color: #3a2e1e;
    letter-spacing: 0.4em;
    text-align: center;
    font-size: 0.8rem;
    margin: 1.5rem 0;
    user-select: none;
}

/* ── Spread selector ── */
.spread-card {
    background: linear-gradient(145deg, #161624, #1e1c30);
    border: 1px solid #2e2640;
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
    margin-bottom: 0.5rem;
}
.spread-card:hover { border-color: #6a5020; }
.spread-card.active {
    border-color: #c9a227;
    box-shadow: 0 0 12px rgba(201,162,39,0.15);
}
.spread-title {
    font-family: 'Cinzel', serif;
    color: #d4a843;
    font-size: 0.95rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
}
.spread-desc {
    color: #7a6a50;
    font-size: 0.82rem;
    line-height: 1.5;
}

/* ── Question input ── */
.stTextArea textarea, .stTextInput input {
    background-color: #13121f !important;
    border: 1px solid #2a2438 !important;
    border-radius: 8px !important;
    color: #d8ccb8 !important;
    font-family: 'Lora', serif !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #7a5a20 !important;
    box-shadow: 0 0 0 1px #7a5a20 !important;
}
label { color: #8a7050 !important; font-size: 0.85rem !important; letter-spacing: 0.05em !important; }

/* ── Primary button ── */
.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #8a6018, #c9a227) !important;
    color: #0c0c18 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
.stButton > button[kind="primary"]:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #6a5030 !important;
    border: 1px solid #3a2e1e !important;
    border-radius: 8px !important;
    font-family: 'Cinzel', serif !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    width: 100% !important;
}
.stButton > button[kind="secondary"]:hover { border-color: #7a5a20 !important; color: #9a7830 !important; }

/* ── Tarot card display ── */
.cards-row {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    margin: 1.5rem 0;
}
.tarot-card {
    background: linear-gradient(160deg, #161624 0%, #1a1830 100%);
    border: 1px solid #3a3050;
    border-radius: 14px;
    padding: 1.4rem 1rem 1.2rem;
    min-width: 160px;
    max-width: 200px;
    flex: 1;
    text-align: center;
    position: relative;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}
.tarot-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 14px;
    background: linear-gradient(160deg, rgba(201,162,39,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.card-position {
    font-size: 0.7rem;
    color: #6a5a40;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.card-symbol {
    font-size: 2rem;
    line-height: 1;
    margin-bottom: 0.5rem;
    opacity: 0.85;
}
.card-name-cn {
    font-family: 'Cinzel', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #d4a843;
    margin-bottom: 0.2rem;
}
.card-name-en {
    font-size: 0.7rem;
    color: #5a4a32;
    letter-spacing: 0.06em;
    margin-bottom: 0.6rem;
}
.card-orientation {
    display: inline-block;
    font-size: 0.65rem;
    padding: 0.15rem 0.55rem;
    border-radius: 20px;
    letter-spacing: 0.1em;
    margin-bottom: 0.8rem;
}
.card-orientation.upright {
    background: rgba(201,162,39,0.12);
    color: #b08828;
    border: 1px solid rgba(201,162,39,0.2);
}
.card-orientation.reversed {
    background: rgba(100,60,140,0.15);
    color: #8060a0;
    border: 1px solid rgba(100,60,140,0.2);
}
.card-keywords {
    font-size: 0.72rem;
    color: #6a5a42;
    line-height: 1.6;
}
.card-suit {
    font-size: 0.65rem;
    color: #4a3a28;
    margin-top: 0.6rem;
    letter-spacing: 0.08em;
}

/* ── Reading section ── */
.reading-container {
    background: linear-gradient(160deg, #11101c, #161524);
    border: 1px solid #2a2438;
    border-radius: 14px;
    padding: 1.8rem 1.8rem 1.5rem;
    margin: 1.5rem 0;
    line-height: 1.9;
    color: #ccc0a8;
    font-size: 0.95rem;
}
.reading-label {
    font-family: 'Cinzel', serif;
    font-size: 0.7rem;
    color: #6a5030;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Echo diary ── */
.diary-container {
    background: linear-gradient(160deg, #130e1e, #1a1228);
    border: 1px solid #3a2850;
    border-radius: 14px;
    padding: 1.8rem;
    margin: 1.2rem 0;
    position: relative;
    overflow: hidden;
}
.diary-container::before {
    content: '◈';
    position: absolute;
    top: -1rem;
    right: 1.5rem;
    font-size: 4rem;
    color: rgba(180,120,220,0.06);
    pointer-events: none;
}
.diary-label {
    font-family: 'Cinzel', serif;
    font-size: 0.7rem;
    color: #7050a0;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.diary-text {
    color: #b8a8c8;
    font-style: italic;
    font-size: 0.95rem;
    line-height: 2;
}

/* ── Radio (hidden, replaced by custom buttons) ── */
div[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] > div { gap: 0 !important; }
div[data-testid="stRadio"] > div > label {
    background: transparent !important;
    padding: 0 !important;
    cursor: pointer;
    width: 100%;
}

/* ── Misc ── */
.stSpinner > div { border-top-color: #c9a227 !important; }
hr { border-color: #1e1a2a !important; margin: 1.5rem 0 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_client() -> openai.OpenAI:
    api_key = st.session_state.get("api_key") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        st.error("请在侧栏输入 DeepSeek API Key，或设置环境变量 `DEEPSEEK_API_KEY`。")
        st.stop()
    return openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def draw_cards(n: int) -> list[dict]:
    deck = [c.copy() for c in TAROT_DECK]
    drawn = random.sample(deck, n)
    for card in drawn:
        card["reversed"] = random.random() < 0.5
    return drawn


def _stream(client: openai.OpenAI, prompt: str):
    stream = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=700,
        stream=True,
        messages=[
            {"role": "system", "content": ECHO_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def _render_card(card: dict, position: str) -> str:
    symbol = SUIT_SYMBOLS[card["suit"]]
    suit_cn = SUIT_NAMES_CN[card["suit"]]
    orientation_cls = "reversed" if card["reversed"] else "upright"
    orientation_label = "逆位 ▼" if card["reversed"] else "正位 ▲"
    keywords = card["keywords_reversed"] if card["reversed"] else card["keywords_upright"]
    kw_str = " · ".join(keywords[:4])
    return f"""
<div class="tarot-card">
  <div class="card-position">{position}</div>
  <div class="card-symbol">{symbol}</div>
  <div class="card-name-cn">{card['name_cn']}</div>
  <div class="card-name-en">{card['name']}</div>
  <span class="card-orientation {orientation_cls}">{orientation_label}</span>
  <div class="card-keywords">{kw_str}</div>
  <div class="card-suit">{suit_cn}</div>
</div>"""


# ── Session state ──────────────────────────────────────────────────────────────
for key, default in [
    ("phase", "setup"),
    ("drawn_cards", None),
    ("reading_text", ""),
    ("diary_text", ""),
    ("spread_type", "single"),
    ("question", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar: API key ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✦ Echo 设置")
    key_input = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=st.session_state.get("api_key", ""),
        placeholder="sk-...",
        help="也可设置环境变量 DEEPSEEK_API_KEY",
    )
    if key_input:
        st.session_state["api_key"] = key_input

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="echo-header">
  <div class="echo-title">ECHO</div>
  <div class="echo-subtitle">在纸牌的镜面里，听见内心的回声</div>
</div>
<div class="echo-divider">· · ✦ · ·</div>
""",
    unsafe_allow_html=True,
)

# ── PHASE: SETUP ──────────────────────────────────────────────────────────────
if st.session_state.phase == "setup":

    # Question
    question = st.text_area(
        "你想探寻的问题或意图（可留空）",
        value=st.session_state.question,
        placeholder="例如：关于这段关系，我应该如何面对？\n也可以只是「此刻想听听内心的声音」",
        height=90,
        max_chars=200,
    )
    st.session_state.question = question

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Spread selection
    st.markdown(
        "<div style='color:#6a5030;font-size:0.82rem;letter-spacing:0.08em;margin-bottom:0.7rem'>选择牌阵</div>",
        unsafe_allow_html=True,
    )

    spreads = [
        ("single", "一张指引", "✦", "单张牌阵", "从当下汲取一个核心信息"),
        ("three", "三张时间轴", "✦ ✦ ✦", "过去 · 现在 · 未来", "呈现事件的脉络与走向"),
        ("choice", "两难抉择", "✦ ✦", "选择 A  ·  选择 B", "照见两条路径的能量与代价"),
    ]

    for sid, sname, sicon, stitle, sdesc in spreads:
        active = "active" if st.session_state.spread_type == sid else ""
        st.markdown(
            f"""<div class="spread-card {active}" id="spread-{sid}">
  <div class="spread-title">{sicon}&nbsp;&nbsp;{stitle}</div>
  <div class="spread-desc">{sdesc}</div>
</div>""",
            unsafe_allow_html=True,
        )
        if st.button(sname, key=f"btn_{sid}", use_container_width=True, type="secondary"):
            st.session_state.spread_type = sid
            st.rerun()

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    if st.button("洗牌  ·  开始占卜", type="primary", use_container_width=True):
        n_cards = {"single": 1, "three": 3, "choice": 2}[st.session_state.spread_type]
        st.session_state.drawn_cards = draw_cards(n_cards)
        st.session_state.reading_text = ""
        st.session_state.diary_text = ""
        st.session_state.phase = "reading"
        st.rerun()

# ── PHASE: READING ────────────────────────────────────────────────────────────
elif st.session_state.phase == "reading":

    cards = st.session_state.drawn_cards
    spread_type = st.session_state.spread_type
    question = st.session_state.question

    from tarot_data import SPREAD_POSITIONS
    positions = SPREAD_POSITIONS[spread_type]

    # Card display
    cards_html = '<div class="cards-row">' + "".join(
        _render_card(c, p) for c, p in zip(cards, positions)
    ) + "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("<div class='echo-divider'>· · ✦ · ·</div>", unsafe_allow_html=True)

    # Stream reading
    client = _get_client()
    prompt = build_reading_prompt(cards, spread_type, question)

    st.markdown(
        '<div class="reading-container"><div class="reading-label">Echo 的解读</div>',
        unsafe_allow_html=True,
    )
    reading_placeholder = st.empty()
    reading_text = ""
    with st.spinner(""):
        for chunk in _stream(client, prompt):
            reading_text += chunk
            reading_placeholder.markdown(reading_text)
    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.reading_text = reading_text

    # Stream Echo Diary
    st.markdown("<div class='echo-divider'>· · ✦ · ·</div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="diary-container"><div class="diary-label">◈ 回声日记</div>',
        unsafe_allow_html=True,
    )
    diary_placeholder = st.empty()
    diary_text = ""
    diary_prompt = build_diary_prompt(reading_text, spread_type, question)
    for chunk in _stream(client, diary_prompt):
        diary_text += chunk
        diary_placeholder.markdown(f'<div class="diary-text">{diary_text}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.diary_text = diary_text
    st.session_state.phase = "complete"
    st.rerun()

# ── PHASE: COMPLETE ───────────────────────────────────────────────────────────
elif st.session_state.phase == "complete":

    cards = st.session_state.drawn_cards
    spread_type = st.session_state.spread_type

    from tarot_data import SPREAD_POSITIONS
    positions = SPREAD_POSITIONS[spread_type]

    # Card display
    cards_html = '<div class="cards-row">' + "".join(
        _render_card(c, p) for c, p in zip(cards, positions)
    ) + "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("<div class='echo-divider'>· · ✦ · ·</div>", unsafe_allow_html=True)

    # Reading
    st.markdown(
        f'<div class="reading-container"><div class="reading-label">Echo 的解读</div>'
        f'{st.session_state.reading_text}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div class='echo-divider'>· · ✦ · ·</div>", unsafe_allow_html=True)

    # Diary
    st.markdown(
        f'<div class="diary-container"><div class="diary-label">◈ 回声日记</div>'
        f'<div class="diary-text">{st.session_state.diary_text}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("重新占卜", type="primary", use_container_width=True):
            st.session_state.phase = "setup"
            st.session_state.drawn_cards = None
            st.session_state.reading_text = ""
            st.session_state.diary_text = ""
            st.rerun()
    with col2:
        if st.button("换个问题", type="secondary", use_container_width=True):
            st.session_state.phase = "setup"
            st.session_state.drawn_cards = None
            st.session_state.reading_text = ""
            st.session_state.diary_text = ""
            st.session_state.question = ""
            st.rerun()
