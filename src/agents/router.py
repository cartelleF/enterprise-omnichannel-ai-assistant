"""
LLM-based router for the Enterprise Omni-Channel AI Assistant.

The router decides which capability should handle a user question:
- RAG
- ORDER
- CUSTOMER
- ORDER_RAG
- UNKNOWN
"""

import json


ROUTES = {
    "RAG",
    "ORDER",
    "CUSTOMER",
    "ORDER_RAG",
    "UNKNOWN",
}


def build_router_prompt(question):
    """
    Build the prompt used by the LLM to classify a user request.
    """

    return f"""
You are the routing component of an enterprise AI assistant.

Your job is to decide which capability should handle the user's question.

Available routes:

RAG:
Use for questions that require information from enterprise documents,
such as FAQs, policies, return rules, delivery policies or warranties.

ORDER:
Use for questions about a specific order using structured order data,
such as order status, delivery date or order amount.

CUSTOMER:
Use for questions about a specific customer using structured customer data,
such as loyalty level, customer profile or open tickets.

ORDER_RAG:
Use when the question requires BOTH structured order information
and information from enterprise documents.

Example:
"Can I still return order ORD-10066?"
This requires the order delivery information and the return policy.

UNKNOWN:
Use when the question cannot be answered using the available
enterprise capabilities.

Return ONLY valid JSON with this structure:

{{
  "route": "RAG|ORDER|CUSTOMER|ORDER_RAG|UNKNOWN",
  "order_id": null,
  "customer_id": null
}}

Extract order_id or customer_id when present in the question.

User question:
{question}
""".strip()


def parse_router_response(content):
    """
    Parse and validate the JSON returned by the routing LLM.
    """

    if not content:
        return {
            "route": "UNKNOWN",
            "order_id": None,
            "customer_id": None,
        }

    cleaned = content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1)
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return {
            "route": "UNKNOWN",
            "order_id": None,
            "customer_id": None,
        }

    route = result.get("route", "UNKNOWN")

    if route not in ROUTES:
        route = "UNKNOWN"

    return {
        "route": route,
        "order_id": result.get("order_id"),
        "customer_id": result.get("customer_id"),
    }


def route_question(llm_client, model_name, question):
    """
    Route a user question using an LLM.

    Parameters
    ----------
    llm_client:
        OpenAI-compatible client.

    model_name : str
        Name of the model/service exposed through the AI Gateway.

    question : str
        User question.

    Returns
    -------
    dict
        {
            "route": "...",
            "order_id": "...",
            "customer_id": "..."
        }
    """

    prompt = build_router_prompt(question)

    response = llm_client.responses.create(
        model=model_name,
        input=prompt,
        max_output_tokens=300,
    )

    content = response.output_text

    return parse_router_response(content)
