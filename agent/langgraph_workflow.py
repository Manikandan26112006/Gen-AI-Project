"""
LangGraph Agent Workflow for Faculty Performance System
States: KPI Fetch → Score Calc → Performance Predict → RAG Retrieve → LLM Response
"""

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from backend.data_loader import load_faculty_data, load_department_data, load_all_data
from backend.score_calculator import calculate_score, classify_score, get_recommendations
from vector_db.chroma_store import retrieve
from chatbot.chatbot_engine import ask_ai


# ─────────────────────────────────────────────────────────────────────────────
# STATE DEFINITION
# ─────────────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    # Inputs
    query:        str
    role:         str
    faculty_id:   Optional[int]
    department:   Optional[str]
    faculty_name: Optional[str]

    # Intermediate
    kpi_data:     Optional[str]     # stringified dataframe
    score:        Optional[float]
    level:        Optional[str]
    recommendations: Optional[list]
    rag_context:  Optional[str]

    # Output
    response:     Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# NODE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def fetch_kpi_data(state: AgentState) -> AgentState:
    """Load the relevant KPI data based on role."""
    role = state["role"]
    if role == "Faculty" and state.get("faculty_id"):
        df = load_faculty_data(state["faculty_id"])
    elif role == "HOD" and state.get("department"):
        df = load_department_data(state["department"])
    else:
        df = load_all_data()

    state["kpi_data"] = df.to_string(index=False) if not df.empty else "No data available."
    return state


def compute_score(state: AgentState) -> AgentState:
    """Compute performance score for Faculty role (already pre-computed for others)."""
    if state["role"] == "Faculty" and state.get("faculty_id"):
        df = load_faculty_data(state["faculty_id"])
        if not df.empty:
            row = df.iloc[0]
            state["score"] = float(row.get("performance_score", 0))
            state["level"] = row.get("performance_level", "N/A")
            state["recommendations"] = get_recommendations(row)
    return state


def retrieve_rag(state: AgentState) -> AgentState:
    """Retrieve relevant chunks from ChromaDB."""
    dept_filter = state.get("department") if state["role"] == "HOD" else None
    rag = retrieve(state["query"], n_results=3, department_filter=dept_filter)
    state["rag_context"] = rag
    return state


def generate_response(state: AgentState) -> AgentState:
    """Call LLM with context and generate final response."""
    recs_text = ""
    if state.get("recommendations"):
        recs_text = "\n\nRecommendations:\n" + "\n".join(
            f"• {r}" for r in state["recommendations"]
        )

    full_context = (state["kpi_data"] or "") + recs_text
    response = ask_ai(
        question     = state["query"],
        context      = full_context,
        role         = state["role"],
        faculty_name = state.get("faculty_name"),
        rag_context  = state.get("rag_context", "")
    )
    state["response"] = response
    return state


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────
def build_workflow():
    wf = StateGraph(AgentState)
    wf.add_node("fetch_kpi",    fetch_kpi_data)
    wf.add_node("compute_score", compute_score)
    wf.add_node("retrieve_rag",  retrieve_rag)
    wf.add_node("generate",      generate_response)

    wf.set_entry_point("fetch_kpi")
    wf.add_edge("fetch_kpi",    "compute_score")
    wf.add_edge("compute_score","retrieve_rag")
    wf.add_edge("retrieve_rag", "generate")
    wf.add_edge("generate",     END)

    return wf.compile()


# Precompile once when module is imported
faculty_agent = build_workflow()


def run_agent(query: str, role: str,
              faculty_id: int | None = None,
              department: str | None = None,
              faculty_name: str | None = None) -> str:
    """
    Public entry-point. Returns the AI's text response.
    """
    initial_state: AgentState = {
        "query":        query,
        "role":         role,
        "faculty_id":   faculty_id,
        "department":   department,
        "faculty_name": faculty_name,
        "kpi_data":     None,
        "score":        None,
        "level":        None,
        "recommendations": None,
        "rag_context":  None,
        "response":     None,
    }
    result = faculty_agent.invoke(initial_state)
    return result.get("response", "No response generated.")
