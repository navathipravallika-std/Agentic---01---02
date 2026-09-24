"""
Support Ticket State and Data Models for LangGraph Routing Agent
"""
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EntityItem(BaseModel):
    category: str = Field(description="Entity type, e.g. invoice_id, error_code, dollar_amount, product_tier, company_size")
    value: str = Field(description="Entity value extracted from ticket")


class ClassificationOutput(BaseModel):
    category: str = Field(
        description="Ticket category: 'Billing', 'Tech Support', 'Sales', 'Account & Escalation', or 'General Inquiry'"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )
    urgency: str = Field(
        description="Urgency level: 'Low', 'Medium', 'High', or 'Critical'"
    )
    sentiment: str = Field(
        description="Customer sentiment: 'Angry', 'Frustrated', 'Neutral', or 'Positive'"
    )
    key_intent: str = Field(
        description="1-sentence summary of the core customer need"
    )
    extracted_entities: List[EntityItem] = Field(
        default_factory=list,
        description="Extracted entities like invoice IDs, error codes, dollar amounts"
    )
    routing_reasoning: str = Field(
        description="Explanation of why this category and department was selected"
    )


class AgentAction(BaseModel):
    action_id: str
    action_type: str  # e.g., 'refund_stripe', 'create_jira_bug', 'book_sales_call', 'page_oncall_engineer'
    label: str
    payload: Dict[str, Any]
    is_executed: bool = False


class TraceStep(BaseModel):
    node_name: str
    status: str  # 'running', 'completed', 'skipped', 'error'
    timestamp: str
    latency_ms: int
    summary: str
    output_preview: Optional[Dict[str, Any]] = None


class SupportTicketState(TypedDict):
    # Initial input data
    ticket_id: str
    customer_name: str
    customer_email: str
    customer_tier: str  # 'Free', 'Pro', 'Enterprise'
    subject: str
    body: str
    
    # Classification & Routing metadata
    category: Optional[str]
    confidence: Optional[float]
    urgency: Optional[str]
    sentiment: Optional[str]
    key_intent: Optional[str]
    extracted_entities: Optional[List[Dict[str, str]]]
    routing_reasoning: Optional[str]
    target_department: Optional[str]
    
    # Sub-agent outputs
    policies_applied: Optional[List[str]]
    draft_response: Optional[str]
    suggested_actions: Optional[List[Dict[str, Any]]]
    qa_passed: Optional[bool]
    qa_notes: Optional[str]
    
    # Execution & Graph trace
    execution_trace: List[Dict[str, Any]]
    total_latency_ms: Optional[int]
    llm_model_used: Optional[str]
    is_fallback: Optional[bool]
