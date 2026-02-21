import asyncio
from typing import Any, Dict, List, Optional

from EnterpriseHub_new.backend.models.state import AgentMessage, AgentState
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

app = FastAPI(title="EnterpriseHub AI Agentic Core")

# CORS configuration for modern frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Agent Nodes ---


async def lead_intelligence_node(state: AgentState) -> Dict[str, Any]:
    """Analyzes lead intent and sentiment."""
    print(f"--- ANALYZING LEAD: {state['lead_id']} ---")
    # In a real implementation, this would call PydanticAI / LLM
    last_message = state["messages"][-1].content
    analysis = f"Processed intelligence for: {last_message}"

    new_message = AgentMessage(role="assistant", content=analysis)
    return {
        "messages": state["messages"] + [new_message],
        "current_agent": "lead_intelligence",
        "next_action": "respond",
    }


# --- Workflow Definition ---

workflow = StateGraph(AgentState)

workflow.add_node("lead_intelligence", lead_intelligence_node)

workflow.set_entry_point("lead_intelligence")
workflow.add_edge("lead_intelligence", END)

orchestrator = workflow.compile()

# --- API Endpoints ---


class QueryRequest(BaseModel):
    lead_id: str
    tenant_id: str
    message: str


@app.post("/query")
async def handle_query(request: QueryRequest):
    """Entry point for agentic reasoning."""
    initial_state = {
        "messages": [AgentMessage(role="user", content=request.message)],
        "lead_id": request.lead_id,
        "tenant_id": request.tenant_id,
        "current_agent": "entry",
        "metadata": {},
        "next_action": None,
        "errors": [],
    }

    try:
        final_state = await orchestrator.ainvoke(initial_state)
        return final_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine": "LangGraph"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
