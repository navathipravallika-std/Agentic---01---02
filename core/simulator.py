"""
Preset Simulation Tickets and Batch Evaluation Engine
"""
import time
from typing import List, Dict, Any

PRESET_TICKETS: List[Dict[str, Any]] = [
    {
        "id": "PRESET-1",
        "name": "Refund Duplicate Charge",
        "customer_name": "Elena Rostova",
        "customer_email": "elena.rostova@techcorp.io",
        "customer_tier": "Pro",
        "expected_category": "Billing",
        "subject": "Accidental double charge on invoice #INV-2024-889",
        "body": "Hello Support Team, I was charged twice for $99.00 on my credit card this morning for invoice #INV-2024-889. I only wanted one Pro license renewal. Can you please refund the duplicate $99.00 transaction immediately? Thanks."
    },
    {
        "id": "PRESET-2",
        "name": "API 500 & Webhook Failure",
        "customer_name": "Marcus Vance",
        "customer_email": "marcus.v@devops-flow.com",
        "customer_tier": "Enterprise",
        "expected_category": "Tech Support",
        "subject": "Critical: HTTP 500 Server Error on /v2/webhooks dispatch",
        "body": "Our production webhook receiver is failing with HTTP 500 and timeout errors when calling your API endpoint. We are seeing ERR-500-BACKEND-TIMEDOUT in our logs since 14:00 UTC. Can your engineering team investigate the status of the EU gateway?"
    },
    {
        "id": "PRESET-3",
        "name": "500-Seat Enterprise Quote & SOC2",
        "customer_name": "Sarah Jenkins",
        "customer_email": "sjenkins@globalfin.org",
        "customer_tier": "Free",
        "expected_category": "Sales",
        "subject": "Enterprise licensing quote for 500 engineers and SOC2 compliance",
        "body": "Hi there, our procurement team is looking to rollout your platform across 500 seats in Q4. We need a custom enterprise quote, volume discount pricing, and our compliance officer requires your SOC2 Type II audit report and a custom DPA before booking a demo."
    },
    {
        "id": "PRESET-4",
        "name": "Compromised Account & 2FA Lockout",
        "customer_name": "David Sterling",
        "customer_email": "dsterling@apexventures.co",
        "customer_tier": "Enterprise",
        "expected_category": "Account & Escalation",
        "subject": "URGENT: Suspicious login alert and 2FA lockout",
        "body": "I received an email stating a login occurred from an unrecognized IP in Ukraine, and now my Google Authenticator 2FA token is rejected. My account has full production admin credentials. Please freeze active sessions and call my emergency phone right away!"
    },
    {
        "id": "PRESET-5",
        "name": "Feature Request & Dark Mode Docs",
        "customer_name": "Chloe Dupont",
        "customer_email": "chloe.d@designstudio.fr",
        "customer_tier": "Free",
        "expected_category": "General Inquiry",
        "subject": "Dark mode support & where to find GraphQL documentation",
        "body": "Hey team! Really enjoying the tool so far. Is dark mode coming to the dashboard anytime soon? Also, could you point me to where the latest GraphQL schema docs are hosted? Keep up the good work!"
    },
    {
        "id": "PRESET-6",
        "name": "Annual Downgrade & Invoice Resend",
        "customer_name": "Arthur Dent",
        "customer_email": "adent@galaxy-guide.com",
        "customer_tier": "Pro",
        "expected_category": "Billing",
        "subject": "Requesting invoice receipt for #INV-4412 and plan downgrade info",
        "body": "Hi, could you please resend the receipt PDF for transaction #INV-4412 ($290.00)? Also, if we downgrade our plan before the end of the year, will we receive prorated billing credits?"
    },
    {
        "id": "PRESET-7",
        "name": "API Rate Limit 429 in Python SDK",
        "customer_name": "Kenji Sato",
        "customer_email": "kenji@tokyo-data.jp",
        "customer_tier": "Pro",
        "expected_category": "Tech Support",
        "subject": "Getting ERR-429 RateLimitExceeded using python-sdk v2.4",
        "body": "We are batch processing 10,000 records and receiving ERR-429 RateLimitExceeded exceptions. What is the recommended exponential backoff formula, and how do we increase our rate limit from 300 RPM to 1000 RPM?"
    },
    {
        "id": "PRESET-8",
        "name": "Startup Discount & Team Expansion",
        "customer_name": "Lila Morales",
        "customer_email": "lila@quantum-seed.io",
        "customer_tier": "Free",
        "expected_category": "Sales",
        "subject": "Startup discount program and upgrade to 15 seats",
        "body": "Hello! We are a YC-backed startup looking to upgrade from the Free tier to 15 team seats. Do you have a startup discount program or annual prepaid bundle available? We would love to speak with a sales representative."
    }
]


def run_batch_evaluation(api_key: str = "", model_name: str = "gemini-3.6-flash") -> Dict[str, Any]:
    """Runs all preset tickets through the routing workflow and measures accuracy and latency."""
    from core.graph import execute_support_workflow

    results = []
    correct_count = 0
    total_latency = 0

    for ticket in PRESET_TICKETS:
        start = time.time()
        state = execute_support_workflow(ticket, api_key=api_key, model_name=model_name)
        elapsed_ms = int((time.time() - start) * 1000)
        total_latency += elapsed_ms

        assigned = state.get("category", "General Inquiry")
        expected = ticket.get("expected_category", "General Inquiry")
        is_match = (assigned.lower() == expected.lower())
        if is_match:
            correct_count += 1

        results.append({
            "id": ticket["id"],
            "name": ticket["name"],
            "customer": ticket["customer_name"],
            "subject": ticket["subject"],
            "expected_category": expected,
            "predicted_category": assigned,
            "is_correct": is_match,
            "confidence": state.get("confidence", 0.0),
            "urgency": state.get("urgency", "Medium"),
            "sentiment": state.get("sentiment", "Neutral"),
            "latency_ms": elapsed_ms,
            "is_fallback": state.get("is_fallback", False),
            "actions_count": len(state.get("suggested_actions", []))
        })

    accuracy_pct = round((correct_count / len(PRESET_TICKETS)) * 100, 1)
    avg_latency_ms = int(total_latency / len(PRESET_TICKETS))

    return {
        "total_tickets": len(PRESET_TICKETS),
        "correct_predictions": correct_count,
        "accuracy_percentage": accuracy_pct,
        "average_latency_ms": avg_latency_ms,
        "results": results
    }
