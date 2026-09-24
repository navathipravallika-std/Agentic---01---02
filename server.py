"""
FastAPI Server for Customer Support Routing Agent
Exposes REST endpoints for real-time ticket triage, LangGraph traces, batch evaluation, and policy management.
"""
import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.graph import execute_support_workflow, support_graph_app
from core.knowledge_base import get_all_policies, update_policy, reset_policies
from core.simulator import PRESET_TICKETS, run_batch_evaluation

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Customer Support Routing Agent API",
    description="Multi-agent conditional routing system built with LangGraph & Google Gemini",
    version="2.0.0"
)

# Enable CORS for flexible integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key loaded securely from environment variable
DEFAULT_API_KEY = os.environ.get("GEMINI_API_KEY", "")


class TicketTriageRequest(BaseModel):
    ticket_id: Optional[str] = None
    customer_name: str = Field(default="Elena Rostova")
    customer_email: str = Field(default="elena@techcorp.io")
    customer_tier: str = Field(default="Pro")
    subject: str = Field(default="Accidental double charge on invoice #INV-2024-889")
    body: str = Field(default="I was charged twice for $99.00 this morning. Please refund the duplicate transaction.")
    api_key: Optional[str] = None
    model_name: Optional[str] = "gemini-3.6-flash"


class PolicyUpdateRequest(BaseModel):
    category: str
    data: Dict[str, Any]


class ActionExecutionRequest(BaseModel):
    action_id: str
    action_type: str
    payload: Dict[str, Any]


@app.get("/api/health")
def get_health(api_key: Optional[str] = None):
    active_key = (api_key and api_key.strip()) or DEFAULT_API_KEY
    masked_key = f"{active_key[:4]}...{active_key[-4:]}" if len(active_key) > 8 else ("Server Configured" if active_key else "Not Configured (Using Rule Fallback)")
    return {
        "status": "healthy",
        "langgraph_version": "1.2.12",
        "model": "gemini-3.6-flash",
        "has_api_key": bool(active_key),
        "masked_key": masked_key
    }


@app.get("/api/presets")
def get_presets():
    return PRESET_TICKETS


@app.post("/api/triage")
def triage_ticket(req: TicketTriageRequest):
    api_key = req.api_key if (req.api_key and req.api_key.strip()) else DEFAULT_API_KEY
    model = req.model_name or "gemini-3.6-flash"

    result_state = execute_support_workflow(
        ticket_data={
            "ticket_id": req.ticket_id,
            "customer_name": req.customer_name,
            "customer_email": req.customer_email,
            "customer_tier": req.customer_tier,
            "subject": req.subject,
            "body": req.body
        },
        api_key=api_key,
        model_name=model
    )
    return result_state


@app.post("/api/batch-test")
def batch_test(req: Optional[Dict[str, Any]] = None):
    api_key = (req and req.get("api_key")) or DEFAULT_API_KEY
    model = (req and req.get("model_name")) or "gemini-3.6-flash"
    report = run_batch_evaluation(api_key=api_key, model_name=model)
    return report


@app.get("/api/policies")
def list_policies():
    return get_all_policies()


@app.post("/api/policies")
def modify_policy(req: PolicyUpdateRequest):
    success = update_policy(req.category, req.data)
    if not success:
        raise HTTPException(status_code=404, detail="Category policy not found")
    return {"status": "success", "policies": get_all_policies()}


@app.post("/api/policies/reset")
def restore_policies():
    reset_policies()
    return {"status": "success", "policies": get_all_policies()}


@app.post("/api/execute-action")
def execute_action(req: ActionExecutionRequest):
    # Simulated execution with realistic feedback
    action_type = req.action_type
    payload = req.payload

    if action_type == "refund_stripe":
        return {
            "status": "success",
            "message": f"Successfully issued refund of {payload.get('amount', '$49.00')} for invoice {payload.get('invoice_id', 'INV')} to {payload.get('customer_email')}.",
            "external_reference_id": f"ch_stripe_{abs(hash(str(payload))) % 10000000}"
        }
    elif action_type == "create_jira_bug":
        return {
            "status": "success",
            "message": f"Created Jira issue #ENG-{abs(hash(str(payload))) % 9000 + 1000}: '{payload.get('title')}' with Priority: High.",
            "external_reference_id": f"JIRA-ENG-{abs(hash(str(payload))) % 9000 + 1000}"
        }
    elif action_type == "create_crm_deal":
        return {
            "status": "success",
            "message": f"Created Salesforce Opportunity for {payload.get('company')} ({payload.get('seats')}) valued at $18,000 ARR.",
            "external_reference_id": f"SFDC-OPP-{abs(hash(str(payload))) % 90000}"
        }
    elif action_type == "page_oncall_lead":
        return {
            "status": "success",
            "message": f"Paging On-Call Incident Commander via PagerDuty for customer {payload.get('customer')} (Urgency: {payload.get('urgency')}).",
            "external_reference_id": f"PD-INC-{abs(hash(str(payload))) % 90000}"
        }
    else:
        return {
            "status": "success",
            "message": f"Action '{action_type}' processed successfully.",
            "external_reference_id": f"ACT-{abs(hash(str(payload))) % 90000}"
        }


@app.get("/api/graph-spec")
def get_graph_spec():
    """Returns the LangGraph structural topology for interactive UI visualization."""
    return {
        "nodes": [
            {"id": "START", "label": "Email / Ticket Input", "type": "entry"},
            {"id": "ingest_ticket", "label": "Ingest & Normalize", "type": "process"},
            {"id": "classify_ticket", "label": "Gemini Intent Classifier", "type": "ai_classifier"},
            {"id": "router_decision", "label": "Conditional Router", "type": "router"},
            {"id": "billing_node", "label": "Billing Sub-Agent", "type": "subagent", "category": "Billing"},
            {"id": "tech_node", "label": "Tech Support Sub-Agent", "type": "subagent", "category": "Tech Support"},
            {"id": "sales_node", "label": "Sales & Enterprise Sub-Agent", "type": "subagent", "category": "Sales"},
            {"id": "escalation_node", "label": "Escalation Sub-Agent", "type": "subagent", "category": "Account & Escalation"},
            {"id": "general_node", "label": "General Inquiry Sub-Agent", "type": "subagent", "category": "General Inquiry"},
            {"id": "qa_node", "label": "QA & Guardrail Verification", "type": "guardrail"},
            {"id": "END", "label": "Draft Dispatched / Human Approval", "type": "exit"}
        ],
        "edges": [
            {"source": "START", "target": "ingest_ticket"},
            {"source": "ingest_ticket", "target": "classify_ticket"},
            {"source": "classify_ticket", "target": "router_decision"},
            {"source": "router_decision", "target": "billing_node", "label": "Category == Billing"},
            {"source": "router_decision", "target": "tech_node", "label": "Category == Tech Support"},
            {"source": "router_decision", "target": "sales_node", "label": "Category == Sales"},
            {"source": "router_decision", "target": "escalation_node", "label": "Category == Escalation"},
            {"source": "router_decision", "target": "general_node", "label": "Category == General"},
            {"source": "billing_node", "target": "qa_node"},
            {"source": "tech_node", "target": "qa_node"},
            {"source": "sales_node", "target": "qa_node"},
            {"source": "escalation_node", "target": "qa_node"},
            {"source": "general_node", "target": "qa_node"},
            {"source": "qa_node", "target": "END"}
        ]
    }


# Mount static frontend files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Customer Support Routing Agent Backend Ready"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("server:app", host=host, port=port, reload=False)
