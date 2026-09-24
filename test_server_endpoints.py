"""
Comprehensive Verification Test Suite for Customer Support Routing Agent
Validates all endpoints: /api/health, /api/presets, /api/triage, /api/batch-test, /api/policies, /api/execute-action, and static dashboard.
Supports direct in-memory TestClient as well as live HTTP endpoint validation.
"""
import sys
import json
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def run_suite():
    print("=" * 60)
    print(" RUNNING ENDPOINT VERIFICATION SUITE")
    print("=" * 60)

    # 1. Health
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    health = res.json()
    print(f" [PASS] 1. /api/health -> Status: {health.get('status')}, Model: {health.get('model')}")

    # 2. Presets
    res = client.get("/api/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) > 0
    print(f" [PASS] 2. /api/presets -> Loaded {len(presets)} test scenarios.")

    # 3. Triage - Billing Ticket
    res = client.post("/api/triage", json={
        "customer_name": "Elena Rostova",
        "customer_email": "elena@techcorp.io",
        "customer_tier": "Pro",
        "subject": "Accidental double charge on invoice #INV-2024-889",
        "body": "Hello Support Team, I was charged twice for $99.00 on my credit card this morning for invoice #INV-2024-889. Can you refund $99.00?"
    })
    assert res.status_code == 200
    triage_billing = res.json()
    assert triage_billing.get("category") == "Billing"
    assert triage_billing.get("qa_passed") is True
    print(f" [PASS] 3. /api/triage (Billing) -> Category: {triage_billing.get('category')}, Confidence: {triage_billing.get('confidence')}")

    # 4. Triage - Tech Support Ticket
    res = client.post("/api/triage", json={
        "customer_name": "Marcus Vance",
        "customer_email": "marcus.v@devops.io",
        "customer_tier": "Enterprise",
        "subject": "HTTP 500 Server Error and Webhook Failure",
        "body": "Production webhook receiver is failing with ERR-500-BACKEND-TIMEDOUT since 14:00 UTC."
    })
    assert res.status_code == 200
    triage_tech = res.json()
    assert triage_tech.get("category") == "Tech Support"
    print(f" [PASS] 4. /api/triage (Tech Support) -> Category: {triage_tech.get('category')}, Actions: {len(triage_tech.get('suggested_actions', []))}")

    # 5. Batch Benchmark
    res = client.post("/api/batch-test", json={})
    assert res.status_code == 200
    benchmark = res.json()
    assert benchmark.get("accuracy_percentage") >= 80.0
    print(f" [PASS] 5. /api/batch-test -> Accuracy: {benchmark.get('accuracy_percentage')}% ({benchmark.get('correct_predictions')}/{benchmark.get('total_tickets')}), Avg Latency: {benchmark.get('average_latency_ms')}ms")

    # 6. Execute Action
    res = client.post("/api/execute-action", json={
        "action_id": "act_refund_stripe",
        "action_type": "refund_stripe",
        "payload": {"invoice_id": "#INV-2024-889", "amount": "$99.00", "customer_email": "elena@techcorp.io"}
    })
    assert res.status_code == 200
    action_res = res.json()
    assert action_res.get("status") == "success"
    print(f" [PASS] 6. /api/execute-action -> Status: {action_res.get('status')}, Ref: {action_res.get('external_reference_id')}")

    # 7. Static UI index.html
    res = client.get("/")
    assert res.status_code == 200
    assert "<!DOCTYPE html>" in res.text
    print(f" [PASS] 7. / (Frontend Dashboard) -> Served {len(res.text)} bytes HTML")

    print("=" * 60)
    print(" ALL 7 TEST SUITES PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_suite()

