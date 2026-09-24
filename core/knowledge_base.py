"""
Knowledge Base and Policy Rule Store for Routing Sub-Agents
"""
import copy
from typing import Dict, Any, List

DEFAULT_POLICIES: Dict[str, Dict[str, Any]] = {
    "Billing": {
        "department_name": "Billing & Finance Operations",
        "email_alias": "billing@company.io",
        "sla_hours": 4,
        "refund_rules": [
            "Full refunds are unconditionally approved for requests made within 30 days of initial purchase or renewal.",
            "Accidental duplicate charges are refunded immediately with priority batching to avoid chargebacks.",
            "Plan cancellations during an active billing cycle receive prorated credits or remain active until billing period end.",
            "Enterprise contracts require approval from the Finance Controller before issuing refunds exceeding $500.",
            "Always include the Stripe Transaction ID or Invoice Number in customer correspondence."
        ],
        "default_action": "refund_stripe"
    },
    "Tech Support": {
        "department_name": "Engineering & Developer Support",
        "email_alias": "support@company.io",
        "sla_hours": 2,
        "troubleshooting_rules": [
            "For HTTP 500/502 errors: verify system status at status.company.io and ask user for request correlation ID (X-Request-Id).",
            "For API 429 Rate Limits: remind user of tier limits (Starter: 60 RPM, Pro: 300 RPM, Enterprise: 3000 RPM) and recommend exponential backoff.",
            "For Webhook failures: check HMAC-SHA256 signature verification and verify endpoint responds with HTTP 200 within 3000ms.",
            "For SDK errors: verify python/node library version is latest and suggest code snippet fix.",
            "If user is on Enterprise tier or issue affects production, immediately attach a priority Jira issue to on-call."
        ],
        "default_action": "create_jira_bug"
    },
    "Sales": {
        "department_name": "Revenue & Enterprise Accounts",
        "email_alias": "sales@company.io",
        "sla_hours": 1,
        "pricing_rules": [
            "Starter Tier: $29/mo (up to 5 seats, standard support).",
            "Pro Tier: $99/mo (up to 25 seats, priority support, webhooks, 300 RPM).",
            "Enterprise Tier: Custom pricing ($499+/mo, unlimited seats, 99.99% SLA, SOC2 Type II report, custom DPA, dedicated Account Manager).",
            "Discounts: 15% discount for annual commitments, 25% discount for 50+ seats.",
            "Offer direct executive booking link: https://cal.com/company-sales/enterprise-consult"
        ],
        "default_action": "book_sales_call"
    },
    "Account & Escalation": {
        "department_name": "Executive Escalation & Trust & Safety",
        "email_alias": "escalations@company.io",
        "sla_hours": 0.5,
        "security_rules": [
            "For 2FA lockouts: NEVER disable 2FA over email without out-of-band identity verification.",
            "For suspected compromised accounts: Immediately flag account for session invalidation and token rotation.",
            "For highly angry VIP/Enterprise customers: Offer direct escalation call with Head of Customer Experience within 30 minutes.",
            "Always acknowledge distress with high empathy and provide a dedicated direct ticket coordinator."
        ],
        "default_action": "page_oncall_lead"
    },
    "General Inquiry": {
        "department_name": "Customer Experience & Community",
        "email_alias": "hello@company.io",
        "sla_hours": 12,
        "general_rules": [
            "Direct user to public documentation at docs.company.io for standard product questions.",
            "For feature requests: log user interest in product board and provide roadmap link at roadmap.company.io.",
            "Provide invitation to community Discord at discord.gg/company-devs for peer troubleshooting."
        ],
        "default_action": "log_feedback"
    }
}

_ACTIVE_POLICIES = copy.deepcopy(DEFAULT_POLICIES)


def get_all_policies() -> Dict[str, Dict[str, Any]]:
    """Return current policy configurations."""
    return _ACTIVE_POLICIES


def get_policy_for_category(category: str) -> Dict[str, Any]:
    """Retrieve policy guidelines for a given category."""
    if category in _ACTIVE_POLICIES:
        return _ACTIVE_POLICIES[category]
    # Fallback search
    for key in _ACTIVE_POLICIES:
        if key.lower() in category.lower() or category.lower() in key.lower():
            return _ACTIVE_POLICIES[key]
    return _ACTIVE_POLICIES["General Inquiry"]


def update_policy(category: str, updated_data: Dict[str, Any]) -> bool:
    """Update policy rules dynamically."""
    if category in _ACTIVE_POLICIES:
        _ACTIVE_POLICIES[category].update(updated_data)
        return True
    return False


def reset_policies():
    """Reset policies back to factory defaults."""
    global _ACTIVE_POLICIES
    _ACTIVE_POLICIES = copy.deepcopy(DEFAULT_POLICIES)
