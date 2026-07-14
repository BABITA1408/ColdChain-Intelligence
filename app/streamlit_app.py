import streamlit as st
import os
import sys
import subprocess

APP_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
WAREHOUSE_PATH = os.path.join(PROJECT_ROOT, "warehouse.duckdb")

sys.path.insert(0, APP_DIR)


@st.cache_resource(show_spinner=False)
def bootstrap_pipeline():
    """
    Self-bootstrapping pipeline: if the warehouse doesn't exist yet (e.g. fresh
    deploy on Streamlit Cloud), generate data, load it, and run dbt - once per
    app instance. This is the same DAG run_pipeline.sh runs locally; here it's
    triggered automatically so the deployed app works with zero manual setup.
    """
    if os.path.exists(WAREHOUSE_PATH):
        return "already built"
    env = os.environ.copy()
    env["MELT_RISK_DB_PATH"] = WAREHOUSE_PATH
    env["DBT_PROFILES_DIR"] = os.path.join(PROJECT_ROOT, "dbt_project")

    # Use the exact same Python interpreter running this Streamlit app (sys.executable),
    # not a bare "python3" command - on some hosts (like Streamlit Cloud) "python3" can
    # resolve to a different interpreter than the one with our pip-installed packages.
    python_exe = sys.executable
    dbt_exe = os.path.join(os.path.dirname(python_exe), "dbt")
    if not os.path.exists(dbt_exe):
        dbt_exe = "dbt"  # fall back to PATH if not found alongside the interpreter

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


with st.spinner("Setting up data pipeline (first load only)..."):
    bootstrap_pipeline()

from agent import run_agent

st.set_page_config(page_title="Melt Risk Agent", page_icon="🍦", layout="centered")

# ============================== THEME / CSS ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Quicksand:wght@500;600;700&display=swap');

:root {
    --cream: #FFF9F0;
    --plum: #2D1B3D;
    --plum-2: #3F2350;
    --raspberry: #FF4D8D;
    --raspberry-dark: #D6266A;
    --mint: #3DE0C0;
    --mint-dark: #1FA98D;
    --lemon: #FFD866;
    --grape: #B47CFF;
    --choco: #4A2E1F;
    --text-light: #F3E8FF;
}

html, body, [class*="css"] {
    font-family: 'Quicksand', sans-serif;
}

/* Main app background: rich plum/berry gradient + scattered sprinkle confetti texture */
.stApp {
    background:
        radial-gradient(circle at 4px 4px, rgba(255,77,141,0.35) 1.5px, transparent 1.5px),
        radial-gradient(circle at 24px 34px, rgba(61,224,192,0.30) 1.5px, transparent 1.5px),
        radial-gradient(circle at 44px 14px, rgba(255,216,102,0.28) 1.5px, transparent 1.5px),
        radial-gradient(circle at 14% 10%, rgba(255,77,141,0.28) 0%, transparent 42%),
        radial-gradient(circle at 90% 12%, rgba(61,224,192,0.24) 0%, transparent 40%),
        radial-gradient(circle at 50% 100%, rgba(180,124,255,0.22) 0%, transparent 48%),
        linear-gradient(180deg, var(--plum) 0%, var(--plum-2) 100%);
    background-size: 60px 60px, 60px 60px, 60px 60px, auto, auto, auto, auto;
    background-attachment: fixed;
}

/* ---------- Header banner ---------- */
.mr-header { padding: 2.2rem 1.8rem 3.2rem 1.8rem; text-align: center; position: relative; }
.mr-title {
    font-family: 'Fredoka', sans-serif;
    font-weight: 700;
    font-size: 3.1rem;
    line-height: 1.05;
    margin: 0;
    background: linear-gradient(90deg, var(--raspberry) 0%, var(--lemon) 35%, var(--mint) 70%, var(--grape) 100%);
    background-size: 250% auto;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: mr-shimmer 8s ease-in-out infinite;
}
@keyframes mr-shimmer {
    0%   { background-position: 0% center; }
    50%  { background-position: 100% center; }
    100% { background-position: 0% center; }
}
.mr-subtitle {
    font-family: 'Quicksand', sans-serif;
    font-weight: 600;
    color: #E4D6F7;
    max-width: 640px;
    margin: 0.8rem auto 0 auto;
    font-size: 1.04rem;
    line-height: 1.55;
}
/* Melting drip divider under the header */
.mr-drip {
    height: 36px;
    margin-top: -1px;
    background-image: radial-gradient(circle at 22px -12px, transparent 20px, var(--cream) 21px);
    background-size: 44px 44px;
    background-repeat: repeat-x;
    background-position: bottom;
}

/* ---------- Badges row ---------- */
.mr-badges { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 1.1rem; }
.mr-badge {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.22);
    color: var(--text-light);
    padding: 0.32rem 0.9rem;
    border-radius: 999px;
    font-family: 'Quicksand', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #201029 0%, #2D1B3D 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Fredoka', sans-serif;
    color: var(--mint) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
    color: #E4D6F7;
}
[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    color: var(--text-light);
    border-radius: 12px;
    padding: 0.6rem 0.95rem;
    margin-bottom: 0.45rem;
    font-family: 'Quicksand', sans-serif;
    font-weight: 700;
    font-size: 0.85rem;
    transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stButton button:nth-of-type(5n+1):hover { border-color: var(--raspberry); box-shadow: 0 0 16px rgba(255,77,141,0.35); }
[data-testid="stSidebar"] .stButton button:nth-of-type(5n+2):hover { border-color: var(--mint); box-shadow: 0 0 16px rgba(61,224,192,0.35); }
[data-testid="stSidebar"] .stButton button:nth-of-type(5n+3):hover { border-color: var(--lemon); box-shadow: 0 0 16px rgba(255,216,102,0.35); }
[data-testid="stSidebar"] .stButton button:nth-of-type(5n+4):hover { border-color: var(--grape); box-shadow: 0 0 16px rgba(180,124,255,0.35); }
[data-testid="stSidebar"] .stButton button:hover { transform: translateX(3px); }

/* ---------- Chat area ---------- */
[data-testid="stChatMessage"] {
    background: rgba(255, 249, 240, 0.98) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 22px rgba(0,0,0,0.22);
    padding: 0.5rem 0.3rem;
    margin-bottom: 0.8rem;
    border-left: 5px solid var(--mint);
}
/* Chat messages alternate user/assistant in DOM order - color-code by position */
[data-testid="stChatMessage"]:nth-of-type(odd) { border-left-color: var(--raspberry); }
[data-testid="stChatMessage"]:nth-of-type(even) { border-left-color: var(--mint-dark); }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: var(--choco) !important;
    font-weight: 600;
    font-family: 'Quicksand', sans-serif;
}
[data-testid="stChatMessage"] strong { color: var(--raspberry-dark) !important; }

/* Chat input box */
[data-testid="stChatInput"] {
    background: rgba(255, 249, 240, 0.97);
    border-radius: 16px;
    border: 2px solid var(--grape);
}
[data-testid="stChatInput"] textarea {
    color: var(--choco) !important;
    font-weight: 600;
    font-family: 'Quicksand', sans-serif;
}

/* Generic buttons in main area */
.stButton button {
    border-radius: 10px;
    font-family: 'Quicksand', sans-serif;
    font-weight: 700;
}

/* Form / API key card */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 18px;
    padding: 1.5rem;
}

/* Hide default Streamlit chrome we don't need */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================== HEADER ==============================
st.markdown("""
<div class="mr-header">
    <div style="font-size: 3.4rem;">🍦</div>
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
<div class="mr-drip"></div>
""", unsafe_allow_html=True)

# --- API key handling: Streamlit secrets (deployed) or manual entry (local) ---
try:
    api_key = st.secrets.get("GROQ_API_KEY", None)
except Exception:
    api_key = None
if not api_key:
    api_key = st.session_state.get("groq_api_key")

if not api_key:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
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

with st.sidebar:
    st.markdown("### 🍨 Try asking")
    for s in SUGGESTIONS:
        if st.button(s, key=f"sugg_{s}", use_container_width=True):
            st.session_state.queued_prompt = s.split(" ", 1)[1]  # strip emoji
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

# ============================== CHAT ==============================
for msg in st.session_state.history:
    avatar = "🍦" if msg["role"] == "assistant" else "🙋"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


def handle_prompt(prompt: str):
    with st.chat_message("user", avatar="🙋"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🍦"):
        with st.spinner("Thinking (planning → querying data → reasoning)..."):
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