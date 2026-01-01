from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

# 1. Define the State (The "Memory" of the Co-Founder)
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    file_context: str
    current_plan: str

# 2. Define the Nodes (The Logic Steps)
def planner_node(state: AgentState):
    # Logic to look at the user request and user spec
    return {"current_plan": "1. Read file. 2. Edit code. 3. Run Tests."}

def coder_node(state: AgentState):
    # Logic to generate code based on plan
    return {"messages": [AIMessage(content="Generated code for feature X")]}

def git_node(state: AgentState):
    # Logic to call the GitHubTool
    return {"messages": [AIMessage(content="Pushed code to branch feature/x")]}

# 3. Build the Graph (The "Workflow")
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("coder", coder_node)
workflow.add_node("git_pusher", git_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "coder")
workflow.add_edge("coder", "git_pusher")
workflow.add_edge("git_pusher", END)

# 4. Compile
app = workflow.compile()
