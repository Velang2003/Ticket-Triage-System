"""All LLM prompt templates used by the classification and RAG services."""

# ── Classification Prompt ────────────────────────────────────────────────────
# Instructs the model to return strict JSON so parsing is reliable.

CLASSIFICATION_PROMPT_TEMPLATE = """\
You are a support ticket triage assistant. Analyse the support ticket below and classify it.

Ticket Subject: {subject}
Ticket Description: {description}

Return ONLY a JSON object with EXACTLY these keys — no markdown, no explanation:
{{
  "category": "<one of: Billing, Technical, Account, Other>",
  "priority": "<one of: Low, Medium, High, Critical>",
  "rationale": "<one sentence explaining your classification>"
}}

Rules:
- category MUST be exactly one of: Billing, Technical, Account, Other
- priority MUST be exactly one of: Low, Medium, High, Critical
- Return nothing except the JSON object
"""

# Stricter retry variant used on the second attempt after parse failure
CLASSIFICATION_RETRY_PROMPT_TEMPLATE = """\
You must respond with ONLY valid JSON. No code fences, no explanation, no extra text.

Classify this support ticket:
Subject: {subject}
Description: {description}

Required JSON format (fill in the values):
{{"category": "Billing|Technical|Account|Other", "priority": "Low|Medium|High|Critical", "rationale": "..."}}
"""

# ── RAG / Suggestion Prompt ───────────────────────────────────────────────────
SUGGESTION_PROMPT_TEMPLATE = """\
You are a support agent assistant. Based on the ticket below and the relevant knowledge-base \
articles provided, write a concise and actionable resolution suggestion (3–6 sentences).

Ticket Subject: {subject}
Ticket Description: {description}

Relevant Knowledge-Base Articles:
{articles}

Instructions:
- Write a clear, professional suggested resolution for the support agent to use or adapt.
- Reference specific steps from the articles where relevant.
- Do NOT invent steps not covered by the articles.
- Do NOT include greetings or sign-offs — this is an internal suggestion only.
"""
