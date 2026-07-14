import streamlit as st
import os
import sys
import subprocess

APP_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
WAREHOUSE_PATH = os.path.join(PROJECT_ROOT, "warehouse.duckdb")

sys.path.insert(0, APP_DIR)

st.set_page_config(page_title="Melt Risk Agent", page_icon="🍦", layout="centered")

# ----------------------------------------------------------------------------
# Theme: hand-picked ice-cream-parlor palette + a melting-scoop signature motif
# ----------------------------------------------------------------------------
CREAM = "#FFF8EF"
STRAWBERRY = "#FF6F91"
STRAWBERRY_DARK = "#E8547A"
MINT = "#4FD1B8"
CARAMEL = "#F2A65A"
CHOCOLATE = "#3A2618"
PINK_SOFT = "#FFE3EC"
MINT_SOFT = "#DDF7F0"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Nunito', sans-serif;
    }}

    .stApp {{
        background: radial-gradient(circle at 12% 8%, {PINK_SOFT} 0%, transparent 38%),
                    radial-gradient(circle at 88% 4%, {MINT_SOFT} 0%, transparent 32%),
                    {CREAM};
    }}

    /* ---------- Hero banner + melt-drip signature divider ---------- */
    .hero-banner {{
        background: linear-gradient(135deg, {STRAWBERRY} 0%, {CARAMEL} 55%, {MINT} 100%);
        border-radius: 26px 26px 0 0;
        padding: 30px 28px 34px 28px;
        margin: -1rem -1rem 0 -1rem;
        box-shadow: 0 8px 24px rgba(58, 38, 24, 0.12);
    }}
    .hero-title {{
        font-family: 'Baloo 2', sans-serif;
        font-weight: 800;
        font-size: 2.3rem;
        color: #FFFFFF;
        margin: 0;
        text-shadow: 0 2px 6px rgba(0,0,0,0.12);
    }}
    .hero-caption {{
        font-family: 'Nunito', sans-serif;
        font-weight: 600;
        font-size: 0.98rem;
        color: rgba(255,255,255,0.94);
        margin-top: 8px;
        line-height: 1.45;
    }}
    .melt-drip {{
        height: 22px;
        margin: 0 -1rem 1.6rem -1rem;
        background:
            radial-gradient(circle at 10px 0, transparent 11px, {CARAMEL} 12px) 4px -11px / 24px 22px repeat-x;
        opacity: 0.9;
    }}

    /* ---------- Headings inherit the playful display face ---------- */
    h1, h2, h3 {{
        font-family: 'Baloo 2', sans-serif;
        color: {CHOCOLATE};
    }}

    /* ---------- Sidebar: "menu card" styling ---------- */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {MINT_SOFT} 0%, {CREAM} 55%);
        border-right: 3px dashed rgba(58,38,24,0.12);
    }}
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        font-family: 'Baloo 2', sans-serif;
        color: {CHOCOLATE};
    }}

    .suggestion-pill > button {{
        width: 100%;
        text-align: left;
        background: #FFFFFF;
        color: {CHOCOLATE};
        border: 2px solid {PINK_SOFT};
        border-radius: 999px;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(58,38,24,0.06);
        transition: all 0.15s ease;
    }}
    .suggestion-pill > button:hover {{
        border-color: {STRAWBERRY};
        color: {STRAWBERRY_DARK};
        transform: translateY(-1px);
    }}

    .arch-card {{
        background: #FFFFFF;
        border-radius: 14px;
        padding: 12px 14px;
        font-size: 0.82rem;
        color: {CHOCOLATE};
        border: 2px solid {MINT_SOFT};
        line-height: 1.5;
    }}

    /* ---------- Buttons everywhere else (Reset, Save) ---------- */
    .stButton > button {{
        border-radius: 999px;
        font-weight: 800;
        font-family: 'Baloo 2', sans-serif;
        border: none;
        background: linear-gradient(135deg, {STRAWBERRY} 0%, {STRAWBERRY_DARK} 100%);
        color: white;
        padding: 8px 20px;
        box-shadow: 0 3px 8px rgba(232,84,122,0.28);
    }}
    .stButton > button:hover {{
        filter: brightness(1.06);
        box-shadow: 0 5px 12px rgba(232,84,122,0.35);
    }}

    /* ---------- Chat bubbles ---------- */
    [data-testid="stChatMessage"] {{
        border-radius: 20px;
        padding: 4px 6px;
        margin-bottom: 10px;
    }}
    div:has([data-testid="stChatMessageAvatarUser"]) {{
        background: #FFE3EC !important;
        border-radius: 18px;
    }}
    div:has([data-testid="stChatMessageAvatarAssistant"]) {{
        background: #DDF7F0 !important;
        border-radius: 18px;
    }}

    /* ---------- Chat input + text input ---------- */
    [data-testid="stChatInput"] {{
        border-radius: 999px;
        border: 2px solid {STRAWBERRY};
    }}
    .stTextInput > div > div > input {{
        border-radius: 999px;
        border: 2px solid {MINT};
    }}

    /* ---------- Info box (API key prompt) ---------- */
    div[data-testid="stForm"] {{
        background: #FFFFFF;
        border-radius: 18px;
        padding: 18px;
        border: 2px dashed {CARAMEL};
    }}

    /* ---------- Scrollbar sprinkles ---------- */
    ::-webkit-scrollbar {{ width: 10px; }}
    ::-webkit-scrollbar-thumb {{ background: {MINT}; border-radius: 10px; }}
    ::-webkit-scrollbar-track {{ background: {CREAM}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">🍦 Melt Risk Agent</div>
        <div class="hero-caption">
            An agentic AI analyst for ice-cream cold-chain distribution. Ask about melt risk,
            stock levels, or demand — it queries a real dbt + DuckDB warehouse and reasons over
            the results using Groq's Llama&nbsp;3.3&nbsp;70B with tool calling.
        </div>
    </div>
    <div class="melt-drip"></div>
    """,
    unsafe_allow_html=True,
)


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
    steps = [
        (["python3", "generate_data.py"], os.path.join(PROJECT_ROOT, "data")),
        (["python3", "load_to_duckdb.py"], os.path.join(PROJECT_ROOT, "data")),
        (["dbt", "run"], os.path.join(PROJECT_ROOT, "dbt_project")),
    ]
    for cmd, cwd in steps:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"Pipeline step failed: {' '.join(cmd)}\n{result.stderr}")
    return "built fresh"


with st.spinner("🍨 Scooping up the data pipeline (first load only)..."):
    bootstrap_pipeline()

from agent import run_agent

# --- API key handling: Streamlit secrets (deployed) or manual entry (local) ---
try:
    api_key = st.secrets.get("GROQ_API_KEY", None)
except Exception:
    api_key = None
if not api_key:
    api_key = st.session_state.get("groq_api_key")

if not api_key:
    with st.form("api_key_form"):
        st.info("🍒 Enter your free Groq API key to start (get one at console.groq.com/keys). It is not stored anywhere.")
        key_input = st.text_input("Groq API Key", type="password")
        submitted = st.form_submit_button("Save")
        if submitted and key_input:
            st.session_state["groq_api_key"] = key_input
            st.rerun()
    st.stop()

os.environ["GROQ_API_KEY"] = api_key

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

SUGGESTIONS = [
    "Which shipments are at critical melt risk right now?",
    "What products are understocked?",
    "Forecast demand for IC001 at CW01",
    "Which warehouse has the most cold-chain problems?",
    "Summarize overall risk across the network",
]

with st.sidebar:
    st.header("🍧 Try asking")
    for i, suggestion in enumerate(SUGGESTIONS):
        st.markdown('<div class="suggestion-pill">', unsafe_allow_html=True)
        if st.button(suggestion, key=f"suggestion_{i}"):
            st.session_state.pending_prompt = suggestion
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("**🏗️ Architecture**")
    st.markdown(
        '<div class="arch-card">Synthetic data → DuckDB → dbt (staging + marts) → '
        "Groq agent (tool-calling loop) → Streamlit</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button("🔄 Reset conversation"):
        st.session_state.history = []
        st.rerun()

for msg in st.session_state.history:
    avatar = "🧑" if msg["role"] == "user" else "🍦"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask about melt risk, inventory, or demand...")
if not prompt and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🍦"):
        with st.spinner("🍨 Thinking (planning → querying data → reasoning)..."):
            try:
                answer, updated_history = run_agent(prompt, st.session_state.history)
                st.markdown(answer)
                st.session_state.history = updated_history
            except Exception as e:
                st.error(f"Error: {e}")
