"""
Generation layer for the Enterprise Omni-Channel AI Assistant.

This module generates grounded answers from:
- RAG document context
- structured enterprise data
- combined structured + RAG context

The LLM client is injected so the functions can be unit-tested
without calling a real model.
"""

import json
from datetime import date, datetime


def generate_from_rag_context(llm_client, model_name, question, context):
    """
    Generate an answer using only retrieved document context.
    """

    if not context:
        return "I could not find enough information in the enterprise documents to answer this question."

    prompt = f"""
You are an enterprise AI assistant.

Answer the user's question using ONLY the enterprise document context below.

Rules:
- Do not invent information.
- If the context does not contain enough information, say so clearly.
- Keep the answer concise and factual.
- Do not use outside knowledge.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}
""".strip()

    response = llm_client.responses.create(
        model=model_name,
        input=prompt,
        max_output_tokens=400,
    )

    return response.output_text.strip()


def generate_from_structured_context(llm_client, model_name, question, context):
    """
    Generate an answer using only structured enterprise data.
    """

    if not context:
        return "I could not find enough structured enterprise data to answer this question."

    serialized_context = json.dumps(
        context,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are an enterprise AI assistant.

Answer the user's question using ONLY the structured enterprise data below.

Rules:
- Do not invent information.
- Do not use outside knowledge.
- If the data is insufficient, say so clearly.
- Keep the answer concise and factual.

STRUCTURED DATA:
{serialized_context}

USER QUESTION:
{question}
""".strip()

    response = llm_client.responses.create(
        model=model_name,
        input=prompt,
        max_output_tokens=400,
    )

    return response.output_text.strip()


def generate_from_order_and_rag(
    llm_client,
    model_name,
    question,
    order_data,
    rag_context,
    reference_date=None,
):
    """
    Generate an answer combining structured order data
    with retrieved enterprise documents.
    """

    if not order_data:
        return "I could not find the required order information."

    if reference_date is None:
        reference_date = date.today()

    if isinstance(reference_date, (date, datetime)):
        reference_date = reference_date.isoformat()

    serialized_order = json.dumps(
        order_data,
        default=str,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are an enterprise AI assistant.

Answer the user's question using ONLY:
1. the structured order data
2. the retrieved enterprise document context

REFERENCE DATE:
{reference_date}

STRUCTURED ORDER DATA:
{serialized_order}

ENTERPRISE DOCUMENT CONTEXT:
{rag_context}

Rules:
- Combine the structured data and document information when necessary.
- Do not invent information.
- Do not use outside knowledge.
- Respect dates and policy conditions exactly.
- If the available information is insufficient, say so clearly.
- Keep the answer concise and factual.

USER QUESTION:
{question}
""".strip()

    response = llm_client.responses.create(
        model=model_name,
        input=prompt,
        max_output_tokens=400,
    )

    return response.output_text.strip()
