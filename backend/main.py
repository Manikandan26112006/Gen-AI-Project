from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys, os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.data_loader import load_faculty_data, load_department_data
from backend.score_calculator import calculate_score, get_recommendations
from agent.langgraph_workflow import run_agent

app = FastAPI(title="Professor Performance AI API")

class KPIEntry(BaseModel):
    faculty_id: int
    publications: int
    scie_scopus: int
    conferences: int
    books: int
    fdp_sttp: int
    nptel: int
    workshops_organized: int
    industrial_training: int
    consultancy_projects: int
    research_funding: int
    patents: int
    institutional_activities: int
    feedback_score: float
    year: int

class ChatQuery(BaseModel):
    query: str
    role: str
    faculty_id: Optional[int] = None
    department: Optional[str] = None
    faculty_name: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Professor Performance AI API is running"}

@app.get("/faculty/{id}")
async def get_faculty(id: int):
    df = load_faculty_data(id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return df.iloc[0].to_dict()

@app.get("/faculty/{id}/score")
async def get_faculty_score(id: int):
    df = load_faculty_data(id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return {"faculty_id": id, "performance_score": df.iloc[0]["performance_score"]}

@app.get("/faculty/{id}/recommendation")
async def get_faculty_recs(id: int):
    df = load_faculty_data(id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    recs = get_recommendations(df.iloc[0])
    return {"faculty_id": id, "recommendations": recs}

@app.get("/department/{department}/summary")
async def get_dept_summary(department: str):
    df = load_department_data(department)
    if df.empty:
        raise HTTPException(status_code=404, detail="Department not found")
    return {
        "department": department,
        "faculty_count": len(df),
        "avg_score": round(df["performance_score"].mean(), 2),
        "top_performer": df.loc[df["performance_score"].idxmax(), "name"]
    }

@app.post("/faculty/kpi/add")
async def add_kpi(entry: KPIEntry):
    # This endpoint mimics the logic in Streamlit app but for API usage
    # In a real app, this would use a database transaction
    return {"status": "success", "message": "KPI data received (mock)", "data": entry}

@app.post("/chatbot/query")
async def chatbot_query(query_data: ChatQuery):
    try:
        response = run_agent(
            query=query_data.query,
            role=query_data.role,
            faculty_id=query_data.faculty_id,
            department=query_data.department,
            faculty_name=query_data.faculty_name
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
