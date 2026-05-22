from __future__ import annotations

from app.schemas.intent import IntentType


INTENT_DEFINITIONS: dict[IntentType, str] = {
    IntentType.SMALLTALK: "Greetings, acknowledgements, thanks, short casual conversation, filler phrases, or Hinglish social talk with no operational support request.",
    IntentType.CONVERSATIONAL_IDENTITY: "Conversational session identity questions like who am I, what is my name, which account is active, am I logged in.",
    IntentType.BOOK_STATUS: "Questions about manuscript/book progress, printing, release, delivery, tracking, or publication timeline.",
    IntentType.ROYALTY: "Questions about royalties, payment amount, payment timing, payout statements, deductions, earnings history.",
    IntentType.AUTHOR_COPY: "Requests for author copies, shipment status, quantity adjustments, or replacement copies.",
    IntentType.ADDON_STATUS: "Questions about add-on services activation, usage, renewal, billing, or current service state.",
    IntentType.DASHBOARD_ACCESS: "Login/authentication/access issues for dashboards, password reset, OTP failures, locked account.",
    IntentType.GENERAL_POLICY: "Policy/procedure/SLA questions not tied to one active transaction.",
    IntentType.UNKNOWN: "Use only when no intent strongly matches.",
}


def build_intent_system_prompt() -> str:
    intent_lines = "\n".join([f"- {intent.value}: {description}" for intent, description in INTENT_DEFINITIONS.items()])
    return (
        "You are a strict intent classification engine for BookLeaf AI Support Automation Platform.\n"
        "Your job is to classify user support queries into exactly one supported intent.\n"
        "Supported intents:\n"
        f"{intent_lines}\n\n"
        "Return only valid JSON object with keys:\n"
        '{"intent":"<INTENT>","confidence":<0-1 float>,"entities":{},"reasoning":"short explanation"}\n'
        "Rules:\n"
        "1) intent must be one of supported labels.\n"
        "2) confidence must be conservative and calibrated; lower for ambiguity.\n"
        "3) entities should include extracted useful fields (book_title, period, payment_type, addon_name, issue_type, email, author_name, ids).\n"
        "4) reasoning must be <= 30 words and non-sensitive.\n"
        "5) If query asks who the user is or which account/session is active, return CONVERSATIONAL_IDENTITY.\n"
        "6) If query is social/casual and not asking support operations, return SMALLTALK.\n"
        "7) If uncertain or mixed signals with no dominant intent, return UNKNOWN."
    )


def build_intent_user_prompt(query: str) -> str:
    return (
        "Classify this support query and extract entities. Return JSON only.\n"
        f"query: {query}"
    )


def build_response_system_prompt() -> str:
    return (
        "You are BookLeaf's AI support operations specialist.\n"
        "Style requirements:\n"
        "1) Human, professional, and calm.\n"
        "2) Concise and support-oriented (2-5 lines).\n"
        "3) Avoid robotic one-liners.\n"
        "4) Do not expose engineering internals, retrieval failures, or scoring mechanics.\n"
        "5) Give clear next steps when applicable.\n"
        "6) Keep tone consistent across intents and channels.\n"
        "Output plain text only."
    )


def build_response_user_prompt(
    *,
    query: str,
    intent: IntentType,
    author_name: str,
    structured_context: dict,
    rag_context: str,
    rag_available: bool,
    workflow_summary: dict,
) -> str:
    return (
        "Generate a user-facing support response.\n\n"
        f"User query: {query}\n"
        f"Detected intent: {intent.value}\n"
        f"Resolved author: {author_name}\n"
        f"Structured DB context (source of truth): {structured_context}\n"
        f"Knowledge Base context: {rag_context if rag_available else 'No relevant KB context found'}\n"
        f"Workflow status: {workflow_summary}\n\n"
        "Response expectations:\n"
        "- Start with the direct answer.\n"
        "- Include useful operational detail (status, next step, timeline).\n"
        "- Keep response concise, professional, and reassuring.\n"
        "- Do not mention system internals, confidence math, or retrieval pipeline details."
    )
