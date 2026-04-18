"""
Faculty Performance AI System – Main Streamlit Dashboard
Role-Based Access: Faculty | HOD | Principal | Admin
"""

import streamlit as st
import sys, os, time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.auth           import authenticate
from backend.data_loader    import (load_all_data, load_department_data,
                                    load_faculty_data, get_department_list)
from backend.score_calculator import get_recommendations, classify_score

# modular features
from dashboard.modular_features import (
    render_floating_agent, 
    render_sidebar_voice_button,
    render_voice_mode_page,
    upload_certificate_section, 
    admin_review_section, 
    render_feedback_status
)

# Try to import LangGraph agent (gracefully fall back to direct chatbot)
try:
    from agent.langgraph_workflow import run_agent
    USE_LANGGRAPH = True
except Exception:
    from chatbot.chatbot_engine import ask_ai
    USE_LANGGRAPH = False

# Try ChromaDB (optional)
try:
    from vector_db.chroma_store import build_index, retrieve
    HAS_CHROMA = True
except Exception:
    HAS_CHROMA = False

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Professor Performance AI Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  (animated gradient + glassmorphism)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

/* ── Animated background ── */
@keyframes gradientShift {
  0%   { background-position: 0% 50%;   }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%;   }
}
@keyframes float1 {
  0%,100% { transform: translate(0,0) scale(1);      }
  33%     { transform: translate(30px,-30px) scale(1.05); }
  66%     { transform: translate(-20px,20px) scale(.95);  }
}
@keyframes float2 {
  0%,100% { transform: translate(0,0) scale(1);         }
  33%     { transform: translate(-40px,20px) scale(1.08); }
  66%     { transform: translate(25px,-25px) scale(.92);  }
}
@keyframes float3 {
  0%,100% { transform: translate(0,0) scale(1);  }
  50%     { transform: translate(15px,40px) scale(1.1); }
}
@keyframes slideIn {
  from { opacity:0; transform: translateY(20px); }
  to   { opacity:1; transform: translateY(0);    }
}
@keyframes pulse-glow {
  0%,100% { box-shadow: 0 0 20px rgba(139,92,246,0.3); }
  50%     { box-shadow: 0 0 40px rgba(139,92,246,0.6); }
}

/* ── Root body ── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background: #020617;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}
[data-testid="stAppViewContainer"]::before {
  content:"";position:fixed;top:-15%;left:-10%;width:80vw;height:80vw;
  max-width:1200px;max-height:1200px;border-radius:50%;
  background:radial-gradient(circle at 40% 40%,rgba(99,102,241,0.3) 0%,rgba(139,92,246,0.18) 30%,transparent 70%);
  animation:float1 20s ease-in-out infinite;pointer-events:none;z-index:0;
}
[data-testid="stAppViewContainer"]::after {
  content:"";position:fixed;bottom:-12%;right:-12%;width:70vw;height:70vw;
  max-width:1100px;max-height:1100px;border-radius:50%;
  background:radial-gradient(circle at 60% 60%,rgba(6,182,212,0.22) 0%,rgba(16,185,129,0.12) 40%,transparent 70%);
  animation:float2 24s ease-in-out infinite;pointer-events:none;z-index:0;
}
[data-testid="stMain"]::before {
  content:"";position:fixed;top:25%;left:25%;width:50vw;height:50vw;
  max-width:800px;max-height:800px;border-radius:50%;
  background:radial-gradient(circle,rgba(236,72,153,0.12) 0%,transparent 65%);
  animation:float3 28s ease-in-out infinite;pointer-events:none;z-index:0;
}
[data-testid="stMain"] {
  background-image: radial-gradient(circle,rgba(99,102,241,0.06) 1px,transparent 1px);
  background-size: 40px 40px;
}
[data-testid="stHeader"] {
  background: rgba(15, 23, 42, 0.4) !important;
  backdrop-filter: blur(20px) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"],section.main>div {
  background:transparent !important;
}
/* ── General text color ── */
h1, h2, h3, h4, h5, h6, p, label, span,
[data-testid="stMarkdownContainer"] * {
    color: #f1f5f9 !important;
}
/* Inputs */
input,textarea,[data-baseweb="input"] input {
  background: rgba(30, 41, 59, 0.5) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #f1f5f9 !important; border-radius: 12px !important;
}
input:focus,textarea:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
}
/* Buttons */
.stButton>button {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
  color: #fff !important; border: none !important; border-radius: 12px !important;
  font-weight: 600 !important; padding: 0.6rem 1.8rem !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}
.stButton>button:hover { transform: translateY(-3px) scale(1.02) !important; box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5) !important; filter: brightness(1.1) !important; }
/* Selectbox */
[data-baseweb="select"]>div {
  background: rgba(30, 41, 59, 0.5) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px !important; color: #f1f5f9 !important;
}
/* ── Dataframe (Dark Theme) ── */
[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    background: rgba(15, 23, 42, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.dvn-scroller {
    background: rgba(15, 23, 42, 0.9) !important;
}
hr { border:none !important; border-top:1px solid rgba(255, 255, 255, 0.1) !important; margin:1.5rem 0 !important; }
.stSuccess { background:rgba(16,185,129,.15) !important; border-color:rgba(16,185,129,.4) !important; }
.stError   { background:rgba(239,68,68,.15) !important; border-color:rgba(239,68,68,.4) !important; }
[data-testid="stSpinner"] p { color:#4f46e5 !important; }

/* ── Hero ── */
.hero-title { text-align:center; padding:2.5rem 1rem 1.5rem; animation:slideIn .8s ease; }
.hero-title h1 {
    font-size: 2.6rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #4f46e5, #0ea5e9, #10b981);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 0.4rem !important;
    letter-spacing: -0.5px;
}
.hero-title p {
    font-size: 1.05rem !important;
    color: #64748b !important;
    margin-top: 0 !important;
}
/* ── Login card ── */
.login-card {
  max-width:440px; margin:0 auto; padding:2.5rem 2rem;
  box-shadow:0 8px 40px rgba(0,0,0,.45); animation:pulse-glow 4s ease infinite;
}

/* ── Role badge ── */
.role-badge {
  display:inline-block; padding:.25rem .85rem; border-radius:999px;
  font-size:.78rem; font-weight:600; letter-spacing:.5px;
  background:linear-gradient(135deg,rgba(124,58,237,.35),rgba(59,130,246,.25));
  border:1px solid rgba(139,92,246,.40); color:#c4b5fd !important; margin-bottom:1rem;
}

/* ── Glassy card for every stBlock ── */
.stAlert,
[data-testid="stExpander"],
div[data-testid="stForm"] {
    background: rgba(15, 12, 45, 0.55) !important;
    backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(139, 92, 246, 0.22) !important;
    border-radius: 16px !important;
}

/* ── Dataframe visibility Fix ── */
[data-testid="stDataFrame"], .stDataFrame {
    background: white !important;
    color: #1e293b !important;
    border-radius: 14px !important;
    padding: 5px;
}
/* Global dataframe cell text */
[data-testid="stDataFrame"] * {
    color: #1e293b !important;
}
/* ── Force black text in custom HTML tables ── */
.black-table-wrap {
    background-color: #ffffff !important;
    border-radius: 10px;
}
.black-table-wrap td {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    background-color: #ffffff !important;
}
.black-table-wrap tr:nth-child(even) td {
    background-color: #f0f9ff !important;
}
.black-table-wrap th {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(90deg, #4f46e5, #7c3aed) !important;
    font-weight: bold !important;
    padding: 9px 10px !important;
    border: 1px solid #4f46e5 !important;
}
/* ── KPI cards (Glassy) ── */
.kpi-card {
  background: rgba(30, 41, 59, 0.45);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 1.5rem; margin: 0.6rem 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.kpi-card:hover {
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-5px) scale(1.01);
  background: rgba(30, 41, 59, 0.6);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
}
.kpi-card .kpi-label { font-size: 0.85rem; color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
.kpi-card .kpi-value { font-size: 2.4rem; font-weight: 800; color: #f8fafc !important; margin: 0.2rem 0; }
.kpi-card .kpi-sublabel { font-size: 0.8rem; color: #64748b !important; }

/* ── Level badge ── */
.level-excellent   { color:#34d399 !important; font-weight:700; }
.level-good        { color:#38bdf8 !important; font-weight:700; }
.level-average     { color:#fbbf24 !important; font-weight:700; }
.level-needs       { color:#f87171 !important; font-weight:700; }

/* ── Chat bubble ── */
.chat-bubble-user { background:rgba(124,58,237,.25); border:1px solid rgba(139,92,246,.3); border-radius:14px 14px 4px 14px; padding:.8rem 1rem; margin:.5rem 0; }
.chat-bubble-ai   { background:rgba(6,182,212,.12);  border:1px solid rgba(6,182,212,.25); border-radius:4px 14px 14px 14px; padding:.8rem 1rem; margin:.5rem 0; }

/* ── Section title ── */
.section-title { font-size:1.3rem; font-weight:700; margin-bottom:1rem;
  background:linear-gradient(90deg,#a78bfa,#38bdf8);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }

/* ── Creds hint ── */
.creds-box {
  background:rgba(15,12,45,.4); border:1px solid rgba(139,92,246,.2);
  border-radius:12px; padding:.8rem 1rem; font-size:.8rem; color:rgba(200,200,230,.7) !important; margin-top:.8rem;
}
/* ── Refined Table Theme (Blue/White/Violet) ── */
.bw-table [data-testid="stDataFrame"] {
    background-color: white !important;
    border: 2px solid #6366f1 !important;
    border-radius: 12px !important;
}
/* Ensure headers are visible with violet gradient */
.bw-table .dvn-scroller [role="columnheader"] {
    background: linear-gradient(90deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    font-weight: bold !important;
}
/* Alternating row colors (Light Blue / White) */
.bw-table .dvn-scroller [role="row"]:nth-child(even) {
    background-color: #f0f9ff !important;
}
.bw-table .dvn-scroller [role="row"]:nth-child(odd) {
    background-color: white !important;
}
/* Dark text for visibility - Pure Black */
.bw-table [data-testid="stDataFrame"] *, 
.bw-table .dvn-scroller *,
.bw-table [data-testid="stDataFrame"] .stDataFrame * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
.bw-table .dvn-scroller [role="columnheader"] *,
.bw-table [role="columnheader"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
/* ── Red Table Theme (For Institutional Table) ── */
.red-table [data-testid="stDataFrame"] {
    background-color: white !important;
    border: 2px solid #ef4444 !important;
    border-radius: 12px !important;
}
.red-table .dvn-scroller [role="columnheader"] {
    background: linear-gradient(90deg, #dc2626, #991b1b) !important;
    color: white !important;
    font-weight: bold !important;
}
.red-table .dvn-scroller [role="row"]:nth-child(even) {
    background-color: #fef2f2 !important;
}
.red-table .dvn-scroller [role="row"]:nth-child(odd) {
    background-color: white !important;
}
.red-table [data-testid="stDataFrame"] *, 
.red-table .dvn-scroller * {
    color: #450a0a !important;
}
.red-table .dvn-scroller [role="columnheader"] * {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-title">
  <h1>🎓 Professor Performance AI Agent</h1>
  <p>Intelligent Analytics · Role-Based Insights · AI-Powered Q&amp;A · LangGraph Workflow</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k, v in [("logged_in", False), ("chat_history", []),
             ("role", None), ("session", None)]:
    if k not in st.session_state:
        st.session_state[k] = v




# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def level_class(level: str) -> str:
    mapping = {"Excellent": "level-excellent", "Good": "level-good",
               "Average": "level-average", "Needs Improvement": "level-needs"}
    return mapping.get(level, "")

def score_gauge(score: float) -> go.Figure:
    color = ("#34d399" if score >= 85 else "#38bdf8" if score >= 60
             else "#fbbf24" if score >= 40 else "#f87171")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        gauge=dict(
            axis=dict(range=[0,100], tickcolor="#e2e8f0"),
            bar=dict(color=color),
            bgcolor="rgba(15,12,45,0.5)",
            bordercolor="rgba(139,92,246,0.3)",
            steps=[
                dict(range=[0,40],  color="rgba(248,113,113,0.12)"),
                dict(range=[40,60], color="rgba(251,191,36,0.12)"),
                dict(range=[60,85], color="rgba(56,189,248,0.12)"),
                dict(range=[85,100],color="rgba(52,211,153,0.12)"),
            ],
            threshold=dict(line=dict(color=color, width=4), value=score),
        ),
        number=dict(suffix="/100", font=dict(size=26, color=color)),
        title=dict(text="Performance Score", font=dict(size=14, color="#a78bfa")),
    ))
    fig.update_layout(
        height=250, paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        margin=dict(l=20, r=20, t=30, b=10),
    )
    return fig

def kpi_radar(row: pd.Series, name: str) -> go.Figure:
    categories = ["Publications","SCIE/Scopus","Conferences","FDP/STTP",
                  "NPTEL","Workshops","Consultancy","Research Funding","Patents"]
    values = [
        min(row.get("publications",0)/15,1)*100,
        min(row.get("scie_scopus",0)/10,1)*100,
        min(row.get("conferences",0)/10,1)*100,
        min(row.get("fdp_sttp",0)/8,1)*100,
        min(row.get("nptel",0)/6,1)*100,
        min(row.get("workshops_organized",0)/5,1)*100,
        min(row.get("consultancy_projects",0)/6,1)*100,
        min(row.get("research_funding",0)/6,1)*100,
        min(row.get("patents",0)/5,1)*100,
    ]
    fig = go.Figure(go.Scatterpolar(
        r=values+[values[0]], theta=categories+[categories[0]],
        fill='toself',
        fillcolor='rgba(139,92,246,0.20)',
        line=dict(color='#a78bfa', width=2),
        name=name,
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(15,12,45,0.4)',
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(color="#a78bfa",size=9)),
            angularaxis=dict(tickfont=dict(color="#e2e8f0",size=10)),
        ),
        showlegend=False, height=340,
        paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=40,r=40,t=20,b=20),
    )
    return fig

def dept_bar(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(df, x="name", y="performance_score", color="performance_level",
                 color_discrete_map={"Excellent":"#34d399","Good":"#38bdf8",
                                     "Average":"#fbbf24","Needs Improvement":"#f87171"},
                 labels={"name":"Faculty","performance_score":"Score","performance_level":"Level"},
                 text_auto=".1f")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0", height=350,
        xaxis=dict(tickfont=dict(size=10), gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(range=[0,105], gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10,r=10,t=20,b=60),
    )
    return fig

def inst_dept_summary(df: pd.DataFrame) -> go.Figure:
    d = df.groupby("department")["performance_score"].mean().reset_index()
    fig = px.bar(d, x="department", y="performance_score",
                 color="performance_score", color_continuous_scale="Viridis",
                 text_auto=".1f",
                 labels={"department":"Department","performance_score":"Avg Score"})
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0", height=320, coloraxis_showscale=False,
        margin=dict(l=10,r=10,t=20,b=40),
    )
    return fig

def generate_strategic_plan(faculty_id: int, level: str) -> pd.DataFrame:
    import random
    random.seed(faculty_id)  # stable results per faculty
    
    particulars = [
        "FDP/ STTP/ FTTP (to be Organized)",
        "FDP/STTP (to be Attended)",
        "NPTEL Certification",
        "NITTTR Program",
        "Symposium (to be Organized)",
        "Conference (to be Organized)",
        "Seminar/ Workshop (to be Organized)",
        "Seminar/ Workshop (to be Attended)",
        "Publications in SCIE Journal",
        "Publications in Conference (IEEE/Springer/Scopus indexed) / Publication in SCIE/Scopus/UGC care listed journals",
        "Value added courses (No. of. Programme)",
        "Professional Bodies",
        "Industrial Training: 15 Days / 2 Weeks",
        "Ph.D Registration",
        "Ph.D Completion",
        "Resource Person",
        "Research Fund (10 Lakhs)",
        "Seminar/Workshop/FDP/STTP/ Project Expo/Science Exhibition Proposal",
        "Consultancy (Civil - 2.5 Lakhs)",
        "IPR/Copy Rights/ Industrial Designs",
        "Book Publication",
        "MOU's",
        "IIC Calendar Activities: Quarter 1,2,3,4",
        "MIC Driven/ Celebration Activities",
        "UBA Activity"
    ]
    
    data = []
    
    for i, p in enumerate(particulars, 1):
        if "Ph.D" in p or "MOU" in p or "Symposium" in p or "Conference (to be Organized)" in p or "NITTTR" in p:
            total_planned = random.choice([0, 1])
        elif "Publications in SCIE" in p or "Industrial Training" in p:
            total_planned = random.randint(10, 25)
        else:
            total_planned = random.randint(1, 12)
            
        odd_planned = total_planned // 2 + total_planned % 2
        even_planned = total_planned // 2
        
        # Simulate 'mixed of average, excellent and bad' tracking based on level
        if level == "Excellent":
            achieved = odd_planned + random.randint(0, 3)
        elif level == "Good":
            achieved = max(0, odd_planned - random.randint(0, 1))
        elif level == "Average":
            achieved = max(0, odd_planned // 2 + random.randint(0, 1))
        else: # Needs Improvement (Bad)
            achieved = random.choice([0, max(0, odd_planned // 3)])
            
        if total_planned == 0:
            achieved = 0

        data.append({
            "Sl. No": i,
            "Particulars": p,
            "Total Planned": str(total_planned) if total_planned > 0 else "-",
            "ODD SEM Planned": str(odd_planned) if odd_planned > 0 else "-",
            "ODD SEM Achieved": str(achieved) if achieved > 0 else "-",
            "Even Sem Planned": str(even_planned) if even_planned > 0 else "-"
        })
        
    return pd.DataFrame(data)

def render_metric_card(label: str, value, sublabel: str = ""):
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {"<div class='kpi-sublabel'>"+sublabel+"</div>" if sublabel else ""}
    </div>
    """, unsafe_allow_html=True)




# ─────────────────────────────────────────────────────────────────────────────
# ═══════════════════════════  LOGIN  ═════════════════════════════════════════
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    with col_c:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Sign In")
        st.caption("Enter your credentials to access the dashboard")
        username = st.text_input("Username", placeholder="e.g. arun_kumar")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Login →", use_container_width=True):
            session = authenticate(username, password)
            if session:
                st.session_state.logged_in = True
                st.session_state.session   = session
                st.session_state.role      = session["role"]
                st.rerun()
            else:
                st.error("⚠️ Invalid credentials. Please try again.")

        # Removed credentials hint box per user request
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ═══════════════════════  MAIN DASHBOARD  ════════════════════════════════════
# ─────────────────────────────────────────────────────────────────────────────
else:
    session    = st.session_state.session
    role       = session["role"]
    faculty_id = session.get("faculty_id")
    dept       = session.get("department")
    fname      = session.get("faculty_name") or session["username"]

    # Handle Voice Mode routing
    if st.session_state.get("voice_mode_active", False):
        render_voice_mode_page(role, faculty_id, fname)
        st.stop()

    # Render agents ONLY for logged-in users
    render_floating_agent(role, faculty_id, fname)
    render_sidebar_voice_button()

    # ── Top bar ───────────────────────────────────────────────────────────────
    top_l, top_r = st.columns([4, 1])
    with top_l:
        display_name = fname if fname else session["username"]
        st.markdown(
            f'<span class="role-badge">🟣 &nbsp;{display_name}&nbsp;·&nbsp;<strong>{role}</strong>'
            + (f'&nbsp;·&nbsp;{dept}' if dept else '')
            + '</span>',
            unsafe_allow_html=True
        )
    with top_r:
        if st.button("Logout ↩", use_container_width=True):
            for k in ["logged_in","session","role","chat_history"]:
                st.session_state[k] = False if k=="logged_in" else ([] if k=="chat_history" else None)
            st.rerun()

    # ═════════════════════════ FACULTY VIEW ═══════════════════════════════════
    if role == "Faculty":
        df = load_faculty_data(faculty_id)
        if df.empty:
            st.error("No data found for your account. Please contact admin.")
            st.stop()

        row = df.iloc[0]
        score = float(row["performance_score"])
        level = row["performance_level"]
        recs  = get_recommendations(row)

        st.markdown(f'<div class="section-title">👤 My Performance Dashboard</div>', unsafe_allow_html=True)
        st.markdown(f"**{row['name']}** &nbsp;·&nbsp; {row['department']} &nbsp;·&nbsp; {row['designation']}", unsafe_allow_html=True)

        # Score gauge + level + top metrics
        g_col, m_col = st.columns([1, 2])
        with g_col:
            st.plotly_chart(score_gauge(score), use_container_width=True)
            lc = level_class(level)
            st.markdown(f'<div style="text-align:center"><span class="{lc}" style="font-size:1.2rem;">● {level}</span></div>', unsafe_allow_html=True)

        with m_col:
            r1, r2, r3 = st.columns(3)
            with r1:
                render_metric_card("Publications", int(row["publications"]))
                render_metric_card("SCIE/Scopus", int(row["scie_scopus"]))
                render_metric_card("Conferences", int(row["conferences"]))
            with r2:
                render_metric_card("FDP/STTP", int(row["fdp_sttp"]))
                render_metric_card("NPTEL", int(row["nptel"]))
                render_metric_card("Workshops", int(row["workshops_organized"]))
            with r3:
                render_metric_card("Consultancy", int(row["consultancy_projects"]))
                render_metric_card("Research Funding", int(row["research_funding"]))
                render_metric_card("Patents", int(row["patents"]))

        # Radar chart
        st.markdown('<div class="section-title">📡 KPI Radar</div>', unsafe_allow_html=True)
        st.plotly_chart(kpi_radar(row, row["name"]), use_container_width=True)

        # Recommendations
        st.markdown('<div class="section-title">💡 AI Recommendations</div>', unsafe_allow_html=True)
        for r in recs:
            st.markdown(f"• {r}")

        # ── KPI Details – point-wise list ──────────────────────────────────
        st.markdown('<div class="section-title">📋 My KPI Details</div>', unsafe_allow_html=True)
        kpi_items = [
            ("1",  "Publications (SCIE/Scopus)",           int(row["publications"])),
            ("2",  "SCIE / Scopus Indexed Journals",       int(row["scie_scopus"])),
            ("3",  "Conferences Attended / Published",     int(row["conferences"])),
            ("4",  "Books / Book Chapters",                int(row["books"])),
            ("5",  "FDP / STTP Attended",                  int(row["fdp_sttp"])),
            ("6",  "NPTEL Certifications",                 int(row["nptel"])),
            ("7",  "Workshops / Seminars Organized",       int(row["workshops_organized"])),
            ("8",  "Industrial Training (15 days/2 wks)",  int(row["industrial_training"])),
            ("9",  "Consultancy Projects",                  int(row["consultancy_projects"])),
            ("10", "Research Funding (Lakhs)",              int(row["research_funding"])),
            ("11", "Patents / IPR",                         int(row["patents"])),
            ("12", "Institutional Activities",              int(row["institutional_activities"])),
            ("13", "Student Feedback Score (/ 5)",         round(float(row["feedback_score"]), 2)),
        ]
        rows_html = "".join(
            f"<tr><td style='width:40px;text-align:center;color:#000;padding:7px 10px;border:1px solid #cbd5e1;'>{sl}</td>"
            f"<td style='text-align:left;color:#000;padding:7px 10px;border:1px solid #cbd5e1;'>{cat}</td>"
            f"<td style='width:80px;text-align:center;color:#000;font-weight:700;padding:7px 10px;border:1px solid #cbd5e1;'>{val}</td></tr>"
            for sl, cat, val in kpi_items
        )
        st.markdown(f"""
        <div class="black-table-wrap" style="padding:12px 14px;border-radius:10px;margin-bottom:1rem;border:1px solid #e2e8f0;">
          <table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:0.92rem;">
            <thead>
              <tr>
                <th style="background:linear-gradient(90deg,#4f46e5,#7c3aed);padding:9px 10px;text-align:center;border:1px solid #4f46e5;">Sl.No</th>
                <th style="background:linear-gradient(90deg,#4f46e5,#7c3aed);padding:9px 10px;text-align:left;border:1px solid #4f46e5;">KPI Category</th>
                <th style="background:linear-gradient(90deg,#4f46e5,#7c3aed);padding:9px 10px;text-align:center;border:1px solid #4f46e5;">Count / Score</th>
              </tr>
            </thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

        # Strategic Plan
        st.markdown('<div class="section-title">📅 Strategic Plan (July 2025 to Dec 2025)</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 1rem;'>
            <h3 style='margin-bottom: 0;'>KONGUNADU COLLEGE OF ENGINEERING &amp; TECHNOLOGY</h3>
            <p style='margin-bottom: 0;'>(Autonomous)<br>Tholurpatti, Thottiam – 621 215.</p>
            <h4 style='margin-top: 0.5rem;'>DEPARTMENT OF {row['department']}</h4>
            <p style='font-weight: bold;'>Strategic Plan for 2025-2026 (July 2025 to December 2025)</p>
        </div>
        """, unsafe_allow_html=True)
        sp_df = generate_strategic_plan(faculty_id, level)
        sp_html = sp_df.to_html(index=False)
        st.markdown(f"""
        <div class="black-table-wrap" style="overflow-x:auto;padding:8px;border-radius:10px;">
            {sp_html}
        </div>""", unsafe_allow_html=True)



        # --- MODULAR ADDITIONS (Feature 3, 4, 7 & 8) ---
        st.divider()
        upload_certificate_section(faculty_id, fname)
        render_feedback_status(faculty_id)
        # ---------------------------------------------

    # ═════════════════════════ HOD VIEW ═══════════════════════════════════════
    elif role == "HOD":
        df = load_department_data(dept)
        if df.empty:
            st.error(f"No faculty data found for department: {dept}")
            st.stop()

        st.markdown(f'<div class="section-title">🏢 Department Dashboard – {dept}</div>', unsafe_allow_html=True)

        # Department metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1: render_metric_card("Faculty Count", len(df))
        with m2: render_metric_card("Avg Score", f"{df['performance_score'].mean():.1f}")
        with m3: render_metric_card("Top Performer", df.loc[df['performance_score'].idxmax(),'name'].split()[-1])
        with m4: render_metric_card("Needs Attention", int((df["performance_level"]=="Needs Improvement").sum()))

        # Bar chart
        st.markdown('<div class="section-title">📊 Faculty Performance Comparison</div>', unsafe_allow_html=True)
        st.plotly_chart(dept_bar(df), use_container_width=True)

        # Full table
        with st.expander("📋 Full Department KPI Table", expanded=False):
            cols_show = [
                "name", "designation", "publications", "scie_scopus", "conferences", 
                "books", "fdp_sttp", "nptel", "workshops_organized", "industrial_training", 
                "consultancy_projects", "research_funding", "patents", "institutional_activities", 
                "feedback_score", "performance_score", "performance_level"
            ]
            kpi_html = df[cols_show].to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{kpi_html}</div>', unsafe_allow_html=True)

        # Top / Weak lists
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🏅 Top Performers")
            top = df.nlargest(3, "performance_score")[["name","performance_score","performance_level"]]
            top_html = top.to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{top_html}</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown("#### ⚠️ Needs Attention")
            weak = df.nsmallest(3, "performance_score")[["name","performance_score","performance_level"]]
            weak_html = weak.to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{weak_html}</div>', unsafe_allow_html=True)



    # ═════════════════════════ PRINCIPAL VIEW ═════════════════════════════════
    elif role == "Principal":
        df = load_all_data()
        st.markdown('<div class="section-title">🏛️ Institutional Performance Dashboard</div>', unsafe_allow_html=True)

        # Institutional summary metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: render_metric_card("Total Faculty",  len(df))
        with m2: render_metric_card("Departments",    df["department"].nunique())
        with m3: render_metric_card("Avg Score",      f"{df['performance_score'].mean():.1f}")
        with m4: render_metric_card("Excellent",      int((df["performance_level"]=="Excellent").sum()))
        with m5: render_metric_card("Needs Help",     int((df["performance_level"]=="Needs Improvement").sum()))

        # Dept comparison + level distribution
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("#### 🏢 Dept-wise Avg Performance Score")
            st.plotly_chart(inst_dept_summary(df), use_container_width=True)
        with ch2:
            st.markdown("#### 📊 Performance Level Distribution")
            level_counts = df["performance_level"].value_counts().reset_index()
            level_counts.columns = ["Level","Count"]
            fig_pie = px.pie(level_counts, values="Count", names="Level",
                             color="Level",
                             color_discrete_map={"Excellent":"#34d399","Good":"#38bdf8",
                                                 "Average":"#fbbf24","Needs Improvement":"#f87171"},
                             hole=0.4)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  font_color="#e2e8f0", height=320,
                                  margin=dict(l=10,r=10,t=10,b=10),
                                  legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_pie, use_container_width=True)

        # Institutional Top/Weak Lists
        st.markdown('<div class="section-title">🏆 Institutional Highlights</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("#### 🏅 Top Overall Performers")
            top_inst = df.nlargest(5, "performance_score")[["name","department","performance_score"]]
            top_inst_html = top_inst.to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{top_inst_html}</div>', unsafe_allow_html=True)
            
        with pc2:
            st.markdown("#### ⚠️ Immediate Support Required")
            weak_inst = df.nsmallest(5, "performance_score")[["name","department","performance_score"]]
            weak_inst_html = weak_inst.to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{weak_inst_html}</div>', unsafe_allow_html=True)

        # Department tabs
        st.markdown('<div class="section-title">🔍 Department Details</div>', unsafe_allow_html=True)
        departments = df["department"].unique().tolist()
        tabs = st.tabs(departments)
        for tab, d in zip(tabs, departments):
            with tab:
                ddf = df[df["department"] == d]
                st.plotly_chart(dept_bar(ddf), use_container_width=True)
                cols_show = [
                    "name", "designation", "publications", "scie_scopus", "conferences", 
                    "books", "fdp_sttp", "nptel", "workshops_organized", "industrial_training", 
                    "consultancy_projects", "research_funding", "patents", "institutional_activities", 
                    "feedback_score", "performance_score", "performance_level"
                ]
                kpi_html = ddf[cols_show].sort_values("performance_score",ascending=False).to_html(index=False)
                st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{kpi_html}</div>', unsafe_allow_html=True)

        # Full institutional table
        with st.expander("📋 Full Institutional KPI Table", expanded=False):
            kpi_html = df.sort_values("department").to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{kpi_html}</div>', unsafe_allow_html=True)

        # Institutional Report Generation
        st.markdown('<div class="section-title">📄 Institutional Report</div>', unsafe_allow_html=True)
        if st.button("📊 Generate & Export Performance Report", use_container_width=True):
            top_performers = df.nlargest(5, "performance_score")[["name", "department", "performance_score"]]
            weak_performers = df.nsmallest(5, "performance_score")[["name", "department", "performance_score"]]
            
            report_html = f"""
            <div style="background: white; color: black; padding: 20px; border-radius: 10px; font-family: sans-serif;">
                <h1 style="color: #4f46e5;">Institutional Performance Report</h1>
                <p><strong>Date:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <h3>Overall Metrics</h3>
                <ul>
                    <li>Total Faculty: {len(df)}</li>
                    <li>Average Score: {df['performance_score'].mean():.2f}</li>
                </ul>
                <h3 style="color: #10b981;">Top 5 Performers</h3>
                {top_performers.to_html(index=False)}
                <h3 style="color: #ef4444;">Faculty Needing Improvement</h3>
                {weak_performers.to_html(index=False)}
            </div>
            """
            st.download_button(
                label="📥 Download HTML Report",
                data=report_html,
                file_name=f"Institutional_Report_{time.strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
            st.success("✅ Report generated! Click below to download.")




    # ═════════════════════════ ADMIN VIEW ═════════════════════════════════════
    elif role == "Admin":
        df = load_all_data()
        st.markdown('<div class="section-title">⚙️ Admin Panel</div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 View All Data", "➕ Add/Edit KPI", "📤 CSV Upload", "👤 Faculty Management", "🔍 Verification Queue"])

        with tab5:
            # --- MODULAR ADDITIONS (Feature 5 & 6) ---
            admin_review_section()
            # ----------------------------------------

        with tab1:
            kpi_html = df.to_html(index=False)
            st.markdown(f'<div class="black-table-wrap" style="overflow-x:auto; padding:8px; border-radius:12px;">{kpi_html}</div>', unsafe_allow_html=True)
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            with m1: render_metric_card("Total Faculty",  len(df))
            with m2: render_metric_card("Departments",    df["department"].nunique())
            with m3: render_metric_card("Avg Score",      f"{df['performance_score'].mean():.1f}")

        with tab4:
            st.markdown("#### Manage Faculty Directory")
            st.caption("Add new faculty, edit their department/designation, or permanently delete them.")
            from sqlalchemy import text as sa_text
            from backend.data_loader import engine as db_engine

            col_edit, col_del = st.columns(2)
            with col_edit:
                with st.form("edit_faculty_form"):
                    st.markdown("**Insert / Update Faculty**")
                    f_id = st.number_input("Faculty ID", min_value=1, step=1)
                    f_name = st.text_input("Name", placeholder="e.g. Dr. John Doe")
                    f_dept = st.text_input("Department", placeholder="e.g. CSE")
                    f_desig = st.text_input("Designation", placeholder="e.g. Assistant Professor")
                    save_fac = st.form_submit_button("💾 Save Faculty")

                    if save_fac and f_name and f_dept:
                        try:
                            with db_engine.connect() as conn:
                                # Update Faculty table
                                conn.execute(sa_text("""
                                    INSERT OR REPLACE INTO faculty (faculty_id, name, department, designation)
                                    VALUES (:fid, :name, :dept, :desig)
                                """), {"fid": f_id, "name": f_name, "dept": f_dept, "desig": f_desig})
                                
                                # Auto-create/update user credentials
                                user_name = f"faculty{f_id}"
                                pass_word = f"faculty{f_id}123"
                                conn.execute(sa_text("""
                                    INSERT OR REPLACE INTO users (username, password, role, faculty_id, department)
                                    VALUES (:usr, :pwd, 'Faculty', :fid, :dept)
                                """), {"usr": user_name, "pwd": pass_word, "fid": f_id, "dept": f_dept})
                                
                                conn.commit()
                            st.success(f"✅ Faculty '{f_name}' saved! Username: {user_name} | Password: {pass_word}")
                        except Exception as e:
                            st.error(f"❌ DB Error: {e}")

            with col_del:
                with st.form("delete_faculty_form"):
                    st.markdown("**Delete Faculty**")
                    del_id = st.number_input("Enter Faculty ID to delete", min_value=1, step=1)
                    confirm_del = st.checkbox("I confirm deletion of this data")
                    del_fac = st.form_submit_button("🗑️ Delete Faculty")

                    if del_fac and confirm_del:
                        try:
                            with db_engine.connect() as conn:
                                conn.execute(sa_text("DELETE FROM faculty WHERE faculty_id=:fid"), {"fid": del_id})
                                conn.execute(sa_text("DELETE FROM kpi WHERE faculty_id=:fid"), {"fid": del_id})
                                conn.execute(sa_text("DELETE FROM scores WHERE faculty_id=:fid"), {"fid": del_id})
                                conn.execute(sa_text("DELETE FROM users WHERE faculty_id=:fid"), {"fid": del_id})
                                conn.commit()
                            st.warning(f"🗑️ Faculty ID {del_id} and all associated data permanently deleted.")
                        except Exception as e:
                            st.error(f"❌ Delete Error: {e}")

        with tab2:
            st.markdown("#### Add / Update KPI Entry")
            a1, a2 = st.columns(2)
            with a1:
                fid     = st.number_input("Faculty ID", min_value=1, step=1)
                pubs    = st.number_input("Publications", min_value=0, step=1)
                scie    = st.number_input("SCIE/Scopus", min_value=0, step=1)
                conf    = st.number_input("Conferences", min_value=0, step=1)
                books   = st.number_input("Books", min_value=0, step=1)
                fdp     = st.number_input("FDP/STTP", min_value=0, step=1)
                nptel   = st.number_input("NPTEL", min_value=0, step=1)
            with a2:
                wshop   = st.number_input("Workshops Organized", min_value=0, step=1)
                ind_tr  = st.number_input("Industrial Training", min_value=0, step=1)
                consult = st.number_input("Consultancy Projects", min_value=0, step=1)
                rfund   = st.number_input("Research Funding", min_value=0, step=1)
                patents = st.number_input("Patents", min_value=0, step=1)
                inst    = st.number_input("Institutional Activities", min_value=0, step=1)
                fb      = st.slider("Feedback Score", 1.0, 5.0, 4.0, 0.1)

            if st.button("💾 Save KPI Entry", use_container_width=True):
                from sqlalchemy import text as sa_text
                from backend.data_loader import engine as db_engine
                from backend.score_calculator import calculate_score, classify_score
                kpi_row = {
                    "faculty_id":faculty_id if faculty_id else fid,
                    "publications":pubs,"scie_scopus":scie,"conferences":conf,
                    "books":books,"fdp_sttp":fdp,"nptel":nptel,
                    "workshops_organized":wshop,"industrial_training":ind_tr,
                    "consultancy_projects":consult,"research_funding":rfund,
                    "patents":patents,"institutional_activities":inst,
                    "feedback_score":fb,"year":2025
                }
                score_val = calculate_score(kpi_row)
                level_val = classify_score(score_val)
                try:
                    with db_engine.connect() as conn:
                        conn.execute(sa_text("""
                            INSERT OR REPLACE INTO kpi
                            (faculty_id,publications,scie_scopus,conferences,books,fdp_sttp,nptel,
                             workshops_organized,industrial_training,consultancy_projects,
                             research_funding,patents,institutional_activities,feedback_score,year)
                            VALUES (:faculty_id,:publications,:scie_scopus,:conferences,:books,:fdp_sttp,:nptel,
                                    :workshops_organized,:industrial_training,:consultancy_projects,
                                    :research_funding,:patents,:institutional_activities,:feedback_score,:year)
                        """), kpi_row)
                        conn.execute(sa_text("""
                            INSERT OR REPLACE INTO scores (faculty_id,performance_score,performance_level,year)
                            VALUES (:fid,:score,:level,:year)
                        """), {"fid":kpi_row["faculty_id"],"score":score_val,"level":level_val,"year":2025})
                        conn.commit()
                    st.success(f"✅ KPI saved! Score: {score_val:.1f} | Level: {level_val}")
                except Exception as e:
                    st.error(f"❌ Failed to save: {e}")

        with tab3:
            st.markdown("#### 📥 Multi-Faculty CSV Upload")
            st.caption("Upload a CSV file to bulk update faculty KPI and performance scores.")
            
            # Expanded instructions
            with st.expander("ℹ️ CSV Format Instructions"):
                st.write("""
                The CSV must contain the following columns:
                `faculty_id`, `publications`, `scie_scopus`, `conferences`, `books`, `fdp_sttp`, `nptel`, 
                `workshops_organized`, `industrial_training`, `consultancy_projects`, `research_funding`, 
                `patents`, `institutional_activities`, `feedback_score`, `year`
                """)
                st.info("Performance scores and levels will be auto-calculated upon import.")

            uploaded = st.file_uploader("Upload Faculty KPI Data (CSV or Excel)", type=["csv", "xlsx"], help="Select a CSV or Excel file containing faculty KPI information")
            
            if uploaded:
                try:
                    udf = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
                    st.markdown("##### 🔍 Data Preview (First 5 Rows)")
                    st.markdown('<div class="bw-table">', unsafe_allow_html=True)
                    st.dataframe(udf.head(5), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    if st.button("🚀 Process & Import to Database", use_container_width=True):
                        from backend.data_loader import engine as db_engine
                        from backend.score_calculator import calculate_score, classify_score
                        
                        with st.status("Processing data...") as status:
                            st.write("Calculating scores...")
                            udf["performance_score"] = udf.apply(calculate_score, axis=1)
                            st.write("Classifying levels...")
                            udf["performance_level"]  = udf["performance_score"].apply(classify_score)
                            
                            st.write("Writing to KPI table...")
                            udf.to_sql("kpi", db_engine, if_exists="append", index=False)
                            
                            st.write("Writing to Scores table...")
                            score_df = udf[["faculty_id","performance_score","performance_level","year"]]
                            score_df.to_sql("scores", db_engine, if_exists="append", index=False)
                            
                            status.update(label="✅ Import Complete!", state="complete", expanded=False)
                        
                        st.success(f"Successfully imported {len(udf)} rows of faculty data.")
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error during import: {e}")





