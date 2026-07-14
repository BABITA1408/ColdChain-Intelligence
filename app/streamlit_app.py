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
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&family=Nunito:wght@400;600;700;800&display=swap');

:root {
    --cream: #FFF6EC;
    --deep-navy: #0E2138;
    --deep-navy-2: #16314F;
    --raspberry: #FF5D8F;
    --raspberry-dark: #E14577;
    --mint: #5EEAD4;
    --peach: #FFB37B;
    --choco: #4A2E1F;
    --text-light: #F6F3EE;
}

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}

/* Main app background: deep frosty navy with soft blurred dessert-colored blobs */
.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(255, 93, 143, 0.30) 0%, transparent 40%),
        radial-gradient(circle at 88% 15%, rgba(94, 234, 212, 0.22) 0%, transparent 38%),
        radial-gradient(circle at 50% 95%, rgba(255, 179, 123, 0.18) 0%, transparent 45%),
        linear-gradient(180deg, var(--deep-navy) 0%, var(--deep-navy-2) 100%);
    background-attachment: fixed;
}

/* ---------- Header banner ---------- */
.mr-header {
    padding: 2.2rem 1.8rem 3.2rem 1.8rem;
    text-align: center;
    position: relative;
}
.mr-title {
    font-family: 'Baloo 2', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    line-height: 1.05;
    margin: 0;
    background: linear-gradient(90deg, var(--raspberry) 0%, var(--peach) 45%, var(--mint) 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: mr-shimmer 7s ease-in-out infinite;
}
@keyframes mr-shimmer {
    0%   { background-position: 0% center; }
    50%  { background-position: 100% center; }
    100% { background-position: 0% center; }
}
.mr-subtitle {
    font-family: 'Nunito', sans-serif;
    font-weight: 600;
    color: #C9D6E5;
    max-width: 640px;
    margin: 0.7rem auto 0 auto;
    font-size: 1.02rem;
    line-height: 1.5;
}
/* Melting drip divider under the header */
.mr-drip {
    height: 34px;
    margin-top: -1px;
    background-image: radial-gradient(circle at 22px -12px, transparent 20px, var(--cream) 21px);
    background-size: 44px 44px;
    background-repeat: repeat-x;
    background-position: bottom;
}

/* ---------- Badges row ---------- */
.mr-badges { display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin-top: 1rem; }
.mr-badge {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    color: var(--text-light);
    padding: 0.28rem 0.85rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1A2C 0%, #10233B 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Baloo 2', sans-serif;
    color: var(--mint) !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
    color: #D8E2EC;
}
[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    color: var(--text-light);
    border-radius: 12px;
    padding: 0.55rem 0.9rem;
    margin-bottom: 0.4rem;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: linear-gradient(90deg, rgba(255,93,143,0.25), rgba(94,234,212,0.25));
    border-color: var(--mint);
    transform: translateX(2px);
}

/* ---------- Chat area ---------- */
.stChatMessage, [data-testid="stChatMessage"] {
    background: rgba(255, 246, 236, 0.97) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.5);
    box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    padding: 0.4rem 0.2rem;
    margin-bottom: 0.7rem;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    color: var(--choco) !important;
    font-weight: 600;
}
[data-testid="stChatMessage"] strong { color: var(--raspberry-dark) !important; }

/* Chat input box */
[data-testid="stChatInput"] {
    background: rgba(255, 246, 236, 0.95);
    border-radius: 16px;
    border: 2px solid var(--mint);
}
[data-testid="stChatInput"] textarea {
    color: var(--choco) !important;
    font-weight: 600;
}

/* Generic buttons in main area */
.stButton button {
    border-radius: 10px;
    font-weight: 700;
}

/* Form / API key card */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 16px;
    padding: 1.4rem;
}

/* Hide default Streamlit chrome we don't need */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================== HEADER ==============================
st.markdown("""
<div class="mr-header">
    <div style="font-size: 3.2rem;">🍦</div>
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