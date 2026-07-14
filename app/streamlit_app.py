import streamlit as st
import os
import sys
import subprocess
import random

APP_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
WAREHOUSE_PATH = os.path.join(PROJECT_ROOT, "warehouse.duckdb")

sys.path.insert(0, APP_DIR)

# set_page_config MUST be the first Streamlit command in the script.
st.set_page_config(page_title="Melt Risk Agent", page_icon="🍦", layout="centered")


@st.cache_resource(show_spinner=False)
def bootstrap_pipeline():
    """
    Self-bootstrapping pipeline: if the warehouse doesn't exist yet (e.g. fresh
    deploy on Streamlit Cloud), generate data, load it, and run dbt - once per
    app instance.
    """
    if os.path.exists(WAREHOUSE_PATH):
        return "already built"
    env = os.environ.copy()
    env["MELT_RISK_DB_PATH"] = WAREHOUSE_PATH
    env["DBT_PROFILES_DIR"] = os.path.join(PROJECT_ROOT, "dbt_project")

    python_exe = sys.executable
    dbt_exe = os.path.join(os.path.dirname(python_exe), "dbt")
    if not os.path.exists(dbt_exe):
        dbt_exe = "dbt"

    steps = [
        ([python_exe, "generate_data.py"], os.path.join(PROJECT_ROOT, "data")),
        ([python_exe, "load_to_duckdb.py"], os.path.join(PROJECT_ROOT, "data")),
        ([dbt_exe, "run"], os.path.join(PROJECT_ROOT, "dbt_project")),
    ]
    for cmd, cwd in steps:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"Pipeline step failed: {' '.join(cmd)}\n{result.stderr}")
    return "built fresh"


with st.spinner("🍦 Scooping intelligence..."):
    bootstrap_pipeline()

from agent import run_agent

# ============================================================================
# THEME / CSS  —  "Gelato Boutique" visual system
# Palette: vanilla cream base, strawberry / mango / mint / blueberry accents,
# chocolate text. Two type families: Fredoka (display) + Manrope (body/UI).
# Signature element: the melting drip divider with real falling drops,
# tying visually into the "melt risk" concept itself.
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

/* ---------------------------------------------------------------------- */
/* 1. DESIGN TOKENS                                                        */
/* ---------------------------------------------------------------------- */
:root {
    --cream:         #FFFBF5;
    --vanilla:       #FFF3E1;
    --strawberry:    #FF7AA2;
    --strawberry-dk: #E85585;
    --mango:         #FFB648;
    --mango-dk:      #EF9B1F;
    --mint:          #4FD8B8;
    --mint-dk:       #22A98A;
    --blueberry:     #8B7CF0;
    --blueberry-dk:  #6C5AD6;
    --lavender:      #E4D9FA;
    --cotton-candy:  #FFD9E8;
    --choco:         #4A2E1F;
    --choco-soft:    #7A5B48;
    --white-glass:   rgba(255,255,255,0.55);
    --white-glass-brd: rgba(255,255,255,0.85);
    --shadow-soft:   0 10px 30px rgba(122, 91, 72, 0.12);
    --shadow-lift:   0 18px 40px rgba(122, 91, 72, 0.18);
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; }
}

html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }

/* ---------------------------------------------------------------------- */
/* 2. BACKGROUND — soft cream base + drifting pastel blobs + sprinkles     */
/*    (decorative layer sits at z-index:-1 so it can NEVER cover content,  */
/*    regardless of how Streamlit names its containers)                    */
/* ---------------------------------------------------------------------- */
.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(255,122,162,0.10) 0%, transparent 40%),
        radial-gradient(circle at 85% 6%, rgba(79,216,184,0.12) 0%, transparent 38%),
        radial-gradient(circle at 50% 95%, rgba(139,124,240,0.08) 0%, transparent 45%),
        var(--cream);
}

.mr-decor { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }
.mr-blob {
    position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.45;
    animation: blobDrift 18s ease-in-out infinite;
    will-change: transform;
}
.mr-blob.b1 { width: 320px; height: 320px; top: -100px; left: -80px; background: var(--strawberry); animation-delay: 0s; }
.mr-blob.b2 { width: 280px; height: 280px; top: 8%; right: -90px; background: var(--mint); animation-delay: -6s; }
.mr-blob.b3 { width: 260px; height: 260px; bottom: -80px; left: 15%; background: var(--blueberry); opacity: 0.3; animation-delay: -10s; }
.mr-blob.b4 { width: 220px; height: 220px; bottom: 6%; right: 8%; background: var(--mango); opacity: 0.3; animation-delay: -3s; }
@keyframes blobDrift {
    0%, 100% { transform: translate(0,0) scale(1); }
    33%      { transform: translate(26px,-24px) scale(1.06); }
    66%      { transform: translate(-20px,20px) scale(0.96); }
}
.mr-sprinkle {
    position: fixed; font-size: 1.4rem; opacity: 0.5; pointer-events: none; z-index: -1;
    animation: sprinkleFloat 7s ease-in-out infinite;
    will-change: transform;
}
@keyframes sprinkleFloat {
    0%, 100% { transform: translateY(0) rotate(-6deg); }
    50%      { transform: translateY(-16px) rotate(6deg); }
}

/* ---------------------------------------------------------------------- */
/* 3. HERO — colorful gradient card, guaranteed contrast (white text on   */
/*    saturated gradient, never gradient-clipped text on a pale bg)       */
/* ---------------------------------------------------------------------- */
.mr-hero {
    background: linear-gradient(135deg, var(--strawberry) 0%, var(--mango) 50%, var(--mint) 100%);
    border-radius: 32px;
    padding: 2.6rem 2rem 3.6rem 2rem;
    text-align: center;
    position: relative;
    box-shadow: var(--shadow-lift);
    overflow: hidden;
}
.mr-hero::before {
    content: "";
    position: absolute; inset: 0;
    background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.35) 0%, transparent 45%);
    pointer-events: none;
}
.mr-logo-wrap {
    position: relative; display: inline-block; margin-bottom: 0.3rem;
}
.mr-logo-glow {
    position: absolute; inset: -20px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,255,255,0.55) 0%, transparent 70%);
    animation: glowPulse 3.2s ease-in-out infinite;
    z-index: 0;
}
@keyframes glowPulse {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50%      { opacity: 1; transform: scale(1.12); }
}
.mr-logo {
    position: relative; z-index: 1;
    font-size: 4.2rem; display: inline-block;
    animation: logoBob 3.2s ease-in-out infinite;
    filter: drop-shadow(0 12px 18px rgba(74,46,31,0.28));
}
@keyframes logoBob {
    0%, 100% { transform: translateY(0) rotate(-2deg); }
    50%      { transform: translateY(-10px) rotate(2deg); }
}
.mr-title {
    font-family: 'Fredoka', sans-serif;
    font-weight: 700;
    font-size: 3rem;
    line-height: 1.1;
    margin: 0.4rem 0 0 0;
    color: #FFFFFF;
    text-shadow: 0 4px 14px rgba(74,46,31,0.25);
    letter-spacing: -0.01em;
}
.mr-subtitle {
    font-weight: 600;
    color: rgba(255,255,255,0.96);
    max-width: 600px;
    margin: 0.9rem auto 0 auto;
    font-size: 1.03rem;
    line-height: 1.65;
    text-shadow: 0 2px 8px rgba(74,46,31,0.15);
}
.mr-badges { display: flex; gap: 0.6rem; justify-content: center; flex-wrap: wrap; margin-top: 1.6rem; }
.mr-badge {
    background: var(--white-glass);
    backdrop-filter: blur(10px);
    border: 1px solid var(--white-glass-brd);
    color: var(--choco);
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.mr-badge:hover { transform: translateY(-3px) scale(1.03); box-shadow: 0 10px 20px rgba(0,0,0,0.15); }

/* Signature element: melting drip divider with real falling drops */
.mr-drip-wrap { position: relative; height: 46px; margin: -2px 0 2.2rem 0; }
.mr-drip {
    position: absolute; inset: 0;
    background-image: radial-gradient(circle at 24px -14px, transparent 22px, var(--cream) 23px);
    background-size: 48px 48px;
    background-repeat: repeat-x;
    background-position: top;
}
.mr-drop {
    position: absolute; top: 14px; width: 10px; height: 10px; border-radius: 50% 50% 50% 0;
    transform: rotate(45deg);
    animation: dripFall 3.4s ease-in infinite;
    will-change: transform, opacity;
}
.mr-drop.d1 { left: 18%; background: var(--strawberry); animation-delay: 0s; }
.mr-drop.d2 { left: 42%; background: var(--mango); animation-delay: 1.1s; }
.mr-drop.d3 { left: 66%; background: var(--mint-dk); animation-delay: 2.0s; }
.mr-drop.d4 { left: 84%; background: var(--blueberry); animation-delay: 0.6s; }
@keyframes dripFall {
    0%   { transform: translateY(0) rotate(45deg); opacity: 0; }
    15%  { opacity: 1; }
    80%  { opacity: 0.9; }
    100% { transform: translateY(26px) rotate(45deg); opacity: 0; }
}

/* ---------------------------------------------------------------------- */
/* 4. SIDEBAR — pastel dashboard                                          */
/* ---------------------------------------------------------------------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--lavender) 0%, var(--cream) 65%);
    border-right: 1px solid rgba(74,46,31,0.06);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Fredoka', sans-serif;
    color: var(--choco) !important;
    font-weight: 600;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
    color: var(--choco-soft);
}
[data-testid="stSidebar"] .stButton button {
    width: 100%; text-align: left;
    background: rgba(255,255,255,0.75);
    border: 1.5px solid rgba(255,255,255,0.9);
    color: var(--choco);
    border-radius: 16px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.55rem;
    font-weight: 700;
    font-size: 0.85rem;
    box-shadow: var(--shadow-soft);
    transition: transform 0.2s cubic-bezier(.2,.8,.2,1), box-shadow 0.2s ease, border-color 0.2s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
    transform: translateY(-3px) scale(1.015);
    border-color: var(--strawberry);
    box-shadow: var(--shadow-lift);
}
[data-testid="stSidebar"] .stButton button:active { transform: translateY(-1px) scale(0.98); }

/* ---------------------------------------------------------------------- */
/* 5. CHAT MESSAGES — floating pastel bubbles, animated entrance          */
/* ---------------------------------------------------------------------- */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border-radius: 22px !important;
    box-shadow: var(--shadow-soft);
    padding: 0.6rem 0.4rem;
    margin-bottom: 0.9rem;
    border: 1.5px solid var(--vanilla);
    animation: messageIn 0.45s cubic-bezier(.2,.8,.2,1) both;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    will-change: transform, opacity;
}
[data-testid="stChatMessage"]:hover { transform: translateY(-2px); box-shadow: var(--shadow-lift); }
@keyframes messageIn {
    from { opacity: 0; transform: translateY(14px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
[data-testid="stChatMessage"]:nth-of-type(odd)  { border-left: 5px solid var(--strawberry); }
[data-testid="stChatMessage"]:nth-of-type(even) { border-left: 5px solid var(--mint-dk); background: #FBFFFD !important; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: var(--choco) !important; font-weight: 600;
}
[data-testid="stChatMessage"] strong { color: var(--strawberry-dk) !important; }

/* Chat input — pill, glow on focus */
[data-testid="stChatInput"] {
    background: #FFFFFF;
    border-radius: 999px;
    border: 2px solid var(--lavender);
    box-shadow: var(--shadow-soft);
    transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--strawberry);
    box-shadow: 0 0 0 5px rgba(255,122,162,0.18), var(--shadow-lift);
}
[data-testid="stChatInput"] textarea { color: var(--choco) !important; font-weight: 600; }

/* ---------------------------------------------------------------------- */
/* 6. BUTTONS (global)                                                     */
/* ---------------------------------------------------------------------- */
.stButton button {
    border-radius: 14px;
    font-weight: 700;
    transition: all 0.22s cubic-bezier(.2,.8,.2,1);
}
.stButton button:hover { transform: translateY(-2px) scale(1.02); }
.stButton button:active { transform: translateY(0) scale(0.97); }

/* ---------------------------------------------------------------------- */
/* 7. API KEY FORM CARD — glass card                                       */
/* ---------------------------------------------------------------------- */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.75);
    border: 1.5px solid rgba(255,255,255,0.9);
    border-radius: 24px;
    padding: 1.7rem;
    backdrop-filter: blur(10px);
    box-shadow: var(--shadow-soft);
}

/* ---------------------------------------------------------------------- */
/* 8. CUSTOM SCROLLBAR                                                     */
/* ---------------------------------------------------------------------- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--strawberry), var(--mint));
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, var(--strawberry-dk), var(--mint-dk)); }

#MainMenu, footer { visibility: hidden; }
</style>

<div class="mr-decor">
    <div class="mr-blob b1"></div>
    <div class="mr-blob b2"></div>
    <div class="mr-blob b3"></div>
    <div class="mr-blob b4"></div>
    <div class="mr-sprinkle" style="top:10%; left:6%; animation-delay:0s;">🍓</div>
    <div class="mr-sprinkle" style="top:16%; right:8%; animation-delay:-2s;">🍫</div>
    <div class="mr-sprinkle" style="bottom:20%; left:9%; animation-delay:-4s;">✨</div>
    <div class="mr-sprinkle" style="bottom:12%; right:10%; animation-delay:-1s;">🧊</div>
    <div class="mr-sprinkle" style="top:45%; left:3%; animation-delay:-3s;">🍭</div>
    <div class="mr-sprinkle" style="top:55%; right:4%; animation-delay:-5s;">⭐</div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# HERO
# ============================================================================
st.markdown("""
<div class="mr-hero">
    <div class="mr-logo-wrap">
        <div class="mr-logo-glow"></div>
        <div class="mr-logo">🍦</div>
    </div>
    <h1 class="mr-title">Melt Risk Agent</h1>
    <p class="mr-subtitle">
        An agentic AI analyst for ice cream cold-chain distribution. Ask about melt risk,
        stock levels, or demand — it queries a real dbt + DuckDB warehouse and reasons over
        the results using Groq's Llama 3.3 70B with tool calling.
    </p>
    <div class="mr-badges">
        <span class="mr-badge">🧊 DuckDB</span>
        <span class="mr-badge">🔧 dbt</span>
        <span class="mr-badge">🤖 Groq · Llama 3.3 70B</span>
        <span class="mr-badge">⚡ Agentic tool-calling</span>
    </div>
</div>
<div class="mr-drip-wrap">
    <div class="mr-drip"></div>
    <div class="mr-drop d1"></div>
    <div class="mr-drop d2"></div>
    <div class="mr-drop d3"></div>
    <div class="mr-drop d4"></div>
</div>
""", unsafe_allow_html=True)

# --- API key handling: Streamlit secrets (deployed) or manual entry (local) ---
try:
    api_key = st.secrets.get("GROQ_API_KEY", None)
except Exception:
    api_key = None
if not api_key:
    api_key = st.session_state.get("groq_api_key")

if not api_key:
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    with st.form("api_key_form"):
        st.markdown("##### 🔑 Enter your free Groq API key to start")
        st.caption("Get one at console.groq.com/keys — it's free, takes 30 seconds, and is never stored anywhere.")
        key_input = st.text_input("Groq API Key", type="password", label_visibility="collapsed")
        submitted = st.form_submit_button("Let's go 🍨")
        if submitted and key_input:
            st.session_state["groq_api_key"] = key_input
            st.rerun()
    st.stop()

os.environ["GROQ_API_KEY"] = api_key

if "history" not in st.session_state:
    st.session_state.history = []
if "queued_prompt" not in st.session_state:
    st.session_state.queued_prompt = None

SUGGESTIONS = [
    "🚨 Which shipments are at critical melt risk?",
    "📦 What products are understocked?",
    "📈 Forecast demand for IC001 at CW01",
    "🌡️ Which warehouse has the worst cold-chain issues?",
    "📋 Summarize overall risk across the network",
]

THINKING_MESSAGES = [
    "🍦 Scooping intelligence...",
    "🍨 Checking frozen inventory...",
    "❄️ Keeping things cool...",
    "🧊 Calculating melt risk...",
    "🍓 Chasing the right data...",
]

with st.sidebar:
    st.markdown("### 🍨 Try asking")
    for s in SUGGESTIONS:
        if st.button(s, key=f"sugg_{s}", use_container_width=True):
            st.session_state.queued_prompt = s.split(" ", 1)[1]
            st.rerun()

    st.divider()
    st.markdown("### 🏗️ Architecture")
    st.markdown(
        "Synthetic data → **DuckDB** → **dbt** "
        "(staging + marts) → **Groq agent** (tool-calling loop) → **Streamlit**"
    )

    st.divider()
    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# ============================================================================
# CHAT
# ============================================================================
for msg in st.session_state.history:
    avatar = "🍦" if msg["role"] == "assistant" else "🙋"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


def handle_prompt(prompt: str):
    with st.chat_message("user", avatar="🙋"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🍦"):
        with st.spinner(random.choice(THINKING_MESSAGES)):
            try:
                answer, updated_history = run_agent(prompt, st.session_state.history)
                st.markdown(answer)
                st.session_state.history = updated_history
            except Exception as e:
                st.error(f"Error: {e}")


if st.session_state.queued_prompt:
    p = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
    handle_prompt(p)

if prompt := st.chat_input("Ask about melt risk, inventory, or demand... 🍨"):
    handle_prompt(prompt)