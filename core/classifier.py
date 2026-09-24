"""
Intent Classifier Engine with LLM Structured Output & Deterministic Heuristic Fallback
"""
import re
import json
import time
from typing import Dict, Any, List, Tuple
from google import genai
from google.genai import types
from core.state import ClassificationOutput, EntityItem

CLASSIFICATION_PROMPT = """You are an expert Customer Support Intent Classification Agent.
Analyze the following incoming customer ticket/email and classify it accurately into exactly ONE of the following categories:
1. "Billing" (Refunds, invoices, duplicate charges, pricing disputes, subscription renewals/cancellations)
2. "Tech Support" (Bugs, 500/400 errors, API failures, SDK integration, webhook errors, downtime)
3. "Sales" (Pricing inquiries, upgrading to enterprise, seat expansion, demo requests, RFPs, custom contracts)
4. "Account & Escalation" (Compromised account, 2FA lockout, severe SLA breach, executive escalation, angry churn threats)
5. "General Inquiry" (Product feedback, general questions, documentation, feature requests)

Also evaluate:
- Confidence score (float 0.0 to 1.0)
- Urgency: "Low", "Medium", "High", or "Critical"
- Sentiment: "Angry", "Frustrated", "Neutral", or "Positive"
- Key Intent: 1 clear summary sentence
- Extracted Entities: Any invoice numbers, dollar amounts, error codes, URLs, user IDs, or seat counts.
- Routing Reasoning: 1-2 sentences explaining why this ticket belongs in the selected department.

TICKET METADATA:
Customer Name: {customer_name}
Customer Email: {customer_email}
Customer Plan Tier: {customer_tier}
Subject: {subject}

MESSAGE BODY:
\"\"\"{body}\"\"\"

Return ONLY a valid JSON object matching this schema:
{{
  "category": "Billing | Tech Support | Sales | Account & Escalation | General Inquiry",
  "confidence": 0.95,
  "urgency": "Low | Medium | High | Critical",
  "sentiment": "Angry | Frustrated | Neutral | Positive",
  "key_intent": "Customer is requesting refund for duplicate monthly charge #INV-928",
  "extracted_entities": [
    {{"category": "invoice_id", "value": "#INV-928"}},
    {{"category": "dollar_amount", "value": "$49.00"}}
  ],
  "routing_reasoning": "Detected duplicate transaction ID and refund request under 30-day window."
}}
"""


def _heuristic_classify(customer_name: str, customer_email: str, customer_tier: str, subject: str, body: str) -> ClassificationOutput:
    """Intelligent rule-based classifier when LLM is unavailable or quota-limited."""
    full_text = f"{subject} {body}".lower()
    
    # Extract entities
    entities: List[EntityItem] = []
    
    # Invoice / Transaction ID matches
    inv_matches = re.findall(r'(?:inv(?:oice)?|tx|ref|order|receipt)[-_\s#:]*([a-z0-9-]+)', full_text, re.I)
    for inv in inv_matches[:2]:
        entities.append(EntityItem(category="invoice_id", value=f"#{inv.upper()}"))
        
    # Dollar amounts
    dollar_matches = re.findall(r'(\$\d+(?:\.\d{2})?|\d+\s*(?:usd|dollars|eur|gbp))', full_text, re.I)
    for dol in dollar_matches[:2]:
        entities.append(EntityItem(category="dollar_amount", value=dol.upper()))
        
    # Error codes
    error_matches = re.findall(r'\b(500|502|503|504|429|401|403|econnreset|timeout|exception|nullpointer|traceback)\b', full_text, re.I)
    for err in set(error_matches):
        entities.append(EntityItem(category="error_code", value=f"ERR-{err.upper()}"))
        
    # Seat count / Team size
    seats_matches = re.findall(r'(\d+)\s*(?:seats|users|licenses|engineers|team members)', full_text, re.I)
    for seat in seats_matches:
        entities.append(EntityItem(category="seat_count", value=f"{seat} seats"))

    # Urgency & Sentiment detection
    urgency = "Medium"
    sentiment = "Neutral"
    
    angry_words = ["furious", "unacceptable", "scam", "lawyer", "ridiculous", "terrible", "rip off", "angry", "disgusted", "chargeback", "sue", "stolen"]
    urgent_words = ["urgent", "immediately", "asap", "production down", "emergency", "blocked", "outage", "critical", "compromised", "hacked"]
    frustrated_words = ["disappointed", "struggling", "broken", "annoyed", "frustrated", "not working", "fails", "tired of"]
    positive_words = ["love", "great", "thank you", "awesome", "interested", "excited", "happy", "appreciate"]

    if any(w in full_text for w in angry_words):
        sentiment = "Angry"
        urgency = "High"
    elif any(w in full_text for w in frustrated_words):
        sentiment = "Frustrated"
    elif any(w in full_text for w in positive_words):
        sentiment = "Positive"

    if any(w in full_text for w in urgent_words) or customer_tier.lower() == "enterprise":
        urgency = "Critical" if "production down" in full_text or "hacked" in full_text or "compromised" in full_text else "High"

    # Category matching scores
    scores = {
        "Billing": 0,
        "Tech Support": 0,
        "Sales": 0,
        "Account & Escalation": 0,
        "General Inquiry": 1  # Base score
    }

    # Billing keywords
    billing_kw = ["refund", "invoice", "charge", "charged", "billing", "receipt", "credit card", "payment", "subscription", "cancel", "renewal", "overcharge", "double charged", "stripe"]
    for kw in billing_kw:
        if kw in full_text:
            scores["Billing"] += 3

    # Tech Support keywords
    tech_kw = ["bug", "500", "error", "api", "crash", "webhook", "sdk", "timeout", "latency", "failing", "code", "exception", "endpoint", "curl", "stack trace", "integration", "gateway"]
    for kw in tech_kw:
        if kw in full_text:
            scores["Tech Support"] += 3

    # Sales keywords
    sales_kw = ["pricing", "enterprise", "quote", "demo", "seats", "annual plan", "procurement", "soc2", "dpa", "security questionnaire", "contract", "upgrade", "sales team", "volume discount"]
    for kw in sales_kw:
        if kw in full_text:
            scores["Sales"] += 3

    # Account & Escalation keywords
    escalation_kw = ["compromised", "hacked", "2fa", "two-factor", "unauthorized", "locked out", "ceo", "executive", "sla breach", "production outage", "lawsuit", "gdpr deletion", "breach"]
    for kw in escalation_kw:
        if kw in full_text:
            scores["Account & Escalation"] += 5

    # Determine highest score
    best_category = max(scores, key=scores.get)
    max_score = scores[best_category]
    confidence = min(0.96, 0.70 + (max_score * 0.05))

    reasoning_map = {
        "Billing": "Keywords indicating payment, refund, invoice, or billing transaction detected.",
        "Tech Support": "Technical error patterns, API endpoints, or failure symptoms detected.",
        "Sales": "Sales inquiry regarding tier upgrade, seat expansion, or enterprise compliance detected.",
        "Account & Escalation": "High severity security, account lockout, or executive escalation signals detected.",
        "General Inquiry": "General product inquiry or documentation guidance requested."
    }

    return ClassificationOutput(
        category=best_category,
        confidence=round(confidence, 2),
        urgency=urgency,
        sentiment=sentiment,
        key_intent=f"{best_category} request from {customer_name} regarding {subject[:40]}",
        extracted_entities=entities,
        routing_reasoning=reasoning_map.get(best_category, "Categorized via rule heuristics.")
    )


def classify_ticket(
    customer_name: str,
    customer_email: str,
    customer_tier: str,
    subject: str,
    body: str,
    api_key: str = "",
    model_name: str = "gemini-3.6-flash"
) -> Tuple[ClassificationOutput, bool, str]:
    """
    Classifies customer ticket using Gemini LLM if available, otherwise heuristic fallback.
    Returns (ClassificationOutput, is_fallback, model_used).
    """
    if api_key and len(api_key) > 10:
        try:
            client = genai.Client(api_key=api_key)
            prompt = CLASSIFICATION_PROMPT.format(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_tier=customer_tier,
                subject=subject,
                body=body
            )
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            raw_json = response.text.strip()
            # Clean possible markdown wrapping if any
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:]
            if raw_json.startswith("```"):
                raw_json = raw_json[3:]
            if raw_json.endswith("```"):
                raw_json = raw_json[:-3]
            raw_json = raw_json.strip()

            parsed = json.loads(raw_json)
            
            entities = []
            if "extracted_entities" in parsed and isinstance(parsed["extracted_entities"], list):
                for e in parsed["extracted_entities"]:
                    if isinstance(e, dict) and "category" in e and "value" in e:
                        entities.append(EntityItem(category=str(e["category"]), value=str(e["value"])))

            output = ClassificationOutput(
                category=parsed.get("category", "General Inquiry"),
                confidence=float(parsed.get("confidence", 0.92)),
                urgency=parsed.get("urgency", "Medium"),
                sentiment=parsed.get("sentiment", "Neutral"),
                key_intent=parsed.get("key_intent", subject),
                extracted_entities=entities,
                routing_reasoning=parsed.get("routing_reasoning", "Classified by Gemini Intent Model.")
            )
            return output, False, model_name

        except Exception as e:
            # Fallback smoothly if quota or network issue occurs
            print(f"[Classifier LLM Info] Falling back to intelligent heuristics: {e}")

    # Fallback path
    fallback_res = _heuristic_classify(customer_name, customer_email, customer_tier, subject, body)
    return fallback_res, True, "Rule-Heuristics Engine (Fallback)"
