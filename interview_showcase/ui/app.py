from __future__ import annotations

import os
from typing import Any, Dict, List

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AgentBridge Showcase", page_icon="🤖", layout="wide")


def api_get(path: str, **params: Any) -> Dict[str, Any] | List[Dict[str, Any]]:
    try:
        res = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as exc:
        st.error(f"API GET failed: {exc}")
        return {}


def api_post(path: str, payload: Dict[str, Any] | None = None, **params: Any) -> Dict[str, Any]:
    try:
        res = requests.post(f"{API_BASE_URL}{path}", json=payload, params=params, timeout=20)
        if res.status_code >= 400:
            return {"error": res.text, "status_code": res.status_code}
        return res.json()
    except Exception as exc:
        return {"error": str(exc), "status_code": 500}


st.title("AgentBridge Interview Showcase")
st.caption("Multilingual + Multi-tenant + Deterministic Task Routing")

with st.sidebar:
    st.header("Session Settings")
    tenant_id = st.text_input("Tenant ID", value="tenant-alpha")
    user_id = st.text_input("User ID", value="demo-user")
    channel = st.selectbox("Channel", ["web", "sms", "whatsapp", "email"], index=0)

    st.divider()
    st.subheader("Quick Scenarios")
    if st.button("Run Kialash Scenario", use_container_width=True):
        scenario = api_post("/v1/demo/scenario/kialash", tenant_id=tenant_id, user_id=user_id)
        st.session_state["scenario_output"] = scenario

    if st.button("Run Chase Scenario", use_container_width=True):
        scenario = api_post("/v1/demo/scenario/chase", tenant_id=tenant_id, user_id=user_id)
        st.session_state["scenario_output"] = scenario


tab_live, tab_metrics, tab_events, tab_approvals, tab_arch, tab_script, tab_quality = st.tabs(
    ["Live Demo", "Metrics", "Events", "Approvals", "Architecture", "Presenter Script", "Quality"]
)

with tab_live:
    st.subheader("Interactive Message Router")

    message = st.text_area(
        "Message",
        value="Hola, quiero comprar una casa y agendar una reunion.",
        height=120,
        help="Try English, Spanish, French, or Hebrew content.",
    )

    col_send, col_block = st.columns([1, 1])

    with col_send:
        if st.button("Send Message", type="primary", use_container_width=True):
            payload = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "message": message,
                "channel": channel,
            }
            result = api_post("/v1/demo/message", payload=payload)
            st.session_state["last_result"] = result

    with col_block:
        if st.button("Simulate Cross-Tenant Block", use_container_width=True):
            payload = {
                "tenant_id": tenant_id,
                "requested_tenant_id": "tenant-other",
                "user_id": user_id,
                "message": message,
                "channel": channel,
            }
            result = api_post("/v1/demo/message", payload=payload)
            st.session_state["last_result"] = result

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        if "error" in result:
            st.error(f"Request failed ({result.get('status_code')}): {result.get('error')}")
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Language", result.get("language", "-"))
            c2.metric("Task Type", result.get("task_type", "-"))
            c3.metric("Cache", "HIT" if result.get("from_cache") else "MISS")
            c4.metric("Latency (ms)", result.get("latency_ms", 0.0))
            c5.metric("Approval", "REQUIRED" if result.get("approval_required") else "NONE")

            st.json(result)

    if "scenario_output" in st.session_state:
        st.subheader("Latest Scenario Output")
        scenario_output = st.session_state["scenario_output"]
        if "error" in scenario_output:
            st.error(str(scenario_output["error"]))
        else:
            st.json(scenario_output)

with tab_metrics:
    st.subheader("Performance and Reliability Metrics")
    metrics = api_get("/v1/metrics")
    if metrics:
        top = st.columns(6)
        top[0].metric("Total Requests", metrics.get("total_requests", 0))
        top[1].metric("Cache Hit Rate", f"{metrics.get('cache_hit_rate', 0.0) * 100:.1f}%")
        top[2].metric("P95 Latency", f"{metrics.get('p95_latency_ms', 0.0)} ms")
        top[3].metric("Cost Savings", f"{metrics.get('estimated_cost_savings_percent', 0.0)}%")
        top[4].metric("Pending Approvals", metrics.get("approvals_pending", 0))
        top[5].metric("Approved Actions", metrics.get("approvals_approved", 0))

        st.write("### Detail")
        st.json(metrics)

with tab_events:
    st.subheader("Event Timeline")
    limit = st.slider("Events", min_value=10, max_value=300, value=100, step=10)
    events = api_get("/v1/events", tenant_id=tenant_id, limit=limit)

    if isinstance(events, list) and events:
        df = pd.DataFrame(events)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No events yet. Send a few messages first.")

with tab_approvals:
    st.subheader("Approval Workflow")
    st.caption("High-risk calendar/email actions are queued for approval.")

    approvals = api_get("/v1/approvals", tenant_id=tenant_id)
    if isinstance(approvals, list) and approvals:
        df = pd.DataFrame(approvals)
        st.dataframe(df, use_container_width=True, hide_index=True)

        pending_ids = [row["approval_id"] for row in approvals if row.get("status") == "pending"]
        if pending_ids:
            selected = st.selectbox("Pending approval", pending_ids, key="approval_select")
            reason = st.text_input("Decision reason (optional)", key="approval_reason")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Approve Selected", use_container_width=True, type="primary"):
                    decision = api_post(
                        f"/v1/approvals/{selected}/decision",
                        payload={"decision": "approve", "reason": reason or None},
                    )
                    st.session_state["approval_result"] = decision
            with c2:
                if st.button("Reject Selected", use_container_width=True):
                    decision = api_post(
                        f"/v1/approvals/{selected}/decision",
                        payload={"decision": "reject", "reason": reason or None},
                    )
                    st.session_state["approval_result"] = decision
        else:
            st.success("No pending approvals.")
    else:
        st.info("No approvals yet. Send a scheduling/email request in Live Demo.")

    if "approval_result" in st.session_state:
        st.write("### Latest Decision")
        st.json(st.session_state["approval_result"])

with tab_arch:
    st.subheader("System Architecture")
    st.code(
        """
flowchart LR
  U[User Input] --> API[FastAPI API]
  API --> T[Tenant Guard]
  T --> R[Task Router]
  R --> H[Handoff Engine]
  API --> C[Redis Cache]
  API --> M[Metrics + Events]
  M --> UI[Streamlit Dashboard]
        """.strip(),
        language="mermaid",
    )

    st.markdown(
        """
- `Tenant Guard`: blocks cross-tenant requests.
- `Task Router`: classifies requests into calendar/email/research/reminder/general.
- `Handoff Engine`: executes specialist handoffs and blocks circular loops.
- `Approval Queue`: high-risk actions require explicit approve/reject decision.
- `Cache + Metrics`: tracks hit rate, latency, and estimated cost savings.
        """
    )

with tab_script:
    st.subheader("What to Say During Demo")
    st.markdown(
        """
### 30-Second Open
- "This is a local-first showcase proving multilingual routing, tenant isolation, and deterministic task orchestration."
- "I will run two scenarios: Kialash for multi-tenant multilingual safety and Chase for secretary task routing with approvals."

### Scenario A: Kialash (3 minutes)
1. Click `Run Kialash Scenario`.
2. Say: "We start in Spanish; language is detected before routing."
3. Say: "Now the system hands off across specialist bots and blocks circular loops."
4. Click `Simulate Cross-Tenant Block`.
5. Say: "This is hard isolation; cross-tenant access is blocked and logged."
6. Open `Metrics` and call out cache hit rate, latency, and blocked-violation count.

### Scenario B: Chase (3 minutes)
1. Click `Run Chase Scenario`.
2. Say: "The same input layer routes work into email/calendar/reminder tasks deterministically."
3. Send: `Schedule a meeting with Alex tomorrow at 3pm`.
4. Open `Approvals` tab and approve the queued action.
5. Say: "High-risk actions require approval and remain auditable."

### Scenario C: Technical Deep-Dive (2 minutes)
- Open `Architecture` tab and walk through API -> guard -> router -> handoff -> approvals -> metrics.
- Open `Quality` tab and note test coverage focus and deterministic replay.
        """
    )

with tab_quality:
    st.subheader("Code Quality Checklist")
    st.markdown(
        """
- Unit/API tests for task routing, language detection, tenant isolation, loop prevention.
- Docker Compose for one-command startup.
- Deterministic scenario scripts for interview replay.
- Runtime metrics for latency, cache hit rate, and safety events.
        """
    )

    st.code(
        """
# Run locally
cd interview_showcase
python3 -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt -r ui/requirements.txt -r tests/requirements.txt
pytest -q
        """.strip(),
        language="bash",
    )
