from src.agents.local_rag_formatter import format_rag_answer
from src.agents.local_multilingual_formatter import format_multilingual_answer
from src.agents.return_eligibility import assess_return_window
"""
Cost-free local demonstration service.

Uses synthetic SAP data and local document retrieval.
No Databricks connections and no LLM calls.
"""

import re
from src.agents.local_router import route_question_local

from src.data_access.sqlite_data_client import SQLiteDataClient
from src.data_access.local_search_client import LocalSearchClient
from src.agents.orchestrator import get_relevant_documents_with_metadata
from src.rag.multilingual_query_expansion import expand_multilingual_query


class LocalDemoService:
    def __init__(self, multilingual_retrieval=False, multilingual_formatting=False):
        self.data_client = SQLiteDataClient()
        self.search_client = LocalSearchClient()
        self.multilingual_retrieval = multilingual_retrieval
        self.multilingual_formatting = multilingual_formatting

    def _retrieval_question(self, question):
        if self.multilingual_retrieval:
            return expand_multilingual_query(question)
        return question

    def ask(self, question: str) -> dict:
        question = question.strip()

        routing = route_question_local(question)

        if routing["route"] == "ORDER_RAG":
            order_id = routing["order_id"]
            order_result = self.data_client.get_order(order_id)

            if not order_result["found"]:
                return {
                    "question": question,
                    "route": "ORDER_RAG",
                    "answer": f"Order {order_id} was not found.",
                    "sources": [],
                }

            retrieval_result = (
                get_relevant_documents_with_metadata(
                    search_client=self.search_client,
                    index_name="local-demo",
                    question=self._retrieval_question(question),
                    top_k=3,
                )
            )

            documents = [
                doc
                for doc in retrieval_result["documents"]
                if doc.get("chunk_text")
            ]

            if retrieval_result["retrieval"]["status"] != "success":
                return {
                    "question": question,
                    "route": "ORDER_RAG",
                    "answer": "The document search is unavailable.",
                    "sources": [],
                }

            if not documents:
                return {
                    "question": question,
                    "route": "ORDER_RAG",
                    "answer": (
                        "I could not find enough policy "
                        "information to answer this question."
                    ),
                    "sources": [],
                }

            order = order_result["data"]

            assessment = assess_return_window(
                delivery_date=order.get("delivery_date"),
                reference_date="2026-09-30",
                return_window_days=30,
            )

            policy_sources = list(dict.fromkeys(
                doc["file_name"] for doc in documents
            ))

            if assessment["status"] == "outside_window":
                answer = (
                    f"Order {order_id} has status "
                    f"{order.get('status', 'Unknown')}. "
                    f"The recorded delivery date is "
                    f"{assessment['delivery_date']}. "
                    f"As of {assessment['reference_date']}, "
                    f"{assessment['elapsed_days']} days have elapsed. "
                    f"The standard 30-day return request window "
                    f"therefore appears to have expired by "
                    f"{assessment['days_over_limit']} days. "
                    "This assessment assumes the recorded date "
                    "is the actual delivery date. "
                    "Customer service must verify the order and "
                    "any applicable product-specific conditions "
                    "before making a final decision."
                )

            elif assessment["status"] == "within_window":
                answer = (
                    f"Order {order_id} has status "
                    f"{order.get('status', 'Unknown')}. "
                    f"Based on the recorded delivery date "
                    f"{assessment['delivery_date']}, "
                    f"the order appears to be within the "
                    "standard 30-day return request window. "
                    "A return request is not an approved return. "
                    "Customer service must verify the order, "
                    "product condition and applicable exceptions."
                )

            else:
                answer = (
                    f"Order {order_id} has status "
                    f"{order.get('status', 'Unknown')}. "
                    "The available delivery information is "
                    "insufficient to assess the return window. "
                    "Customer service must verify the actual "
                    "delivery date and applicable return policy."
                )

            return {
                "question": question,
                "route": "ORDER_RAG",
                "answer": answer,
                "sources": [
                    "synthetic_sap.orders",
                    *dict.fromkeys(
                        doc["file_name"]
                        for doc in documents
                    ),
                ],
            }

        order_match = re.search(
            r"\bORD-\d+\b", question, re.IGNORECASE
        )
        customer_match = re.search(
            r"\bCUST-\d+\b", question, re.IGNORECASE
        )

        if order_match:
            order_id = order_match.group(0).upper()
            result = self.data_client.get_order(order_id)

            if not result["found"]:
                answer = f"Order {order_id} was not found."
            else:
                data = result["data"]
                answer = (
                    f"Order: {data['order_id']}\n"
                    f"Status: {data.get('status', 'Unknown')}\n"
                    f"Order date: {data.get('order_date', 'Unknown')}\n"
                    f"Delivery date: {data.get('delivery_date', 'Unknown')}\n"
                    f"Total: {data.get('total_amount', 'Unknown')} "
                    f"{data.get('currency', '')}"
                )

            return {
                "question": question,
                "route": "ORDER",
                "answer": answer,
                "sources": ["synthetic_sap.orders"],
            }

        if customer_match:
            customer_id = customer_match.group(0).upper()
            result = self.data_client.get_customer(customer_id)

            if not result["found"]:
                answer = f"Customer {customer_id} was not found."
            else:
                data = result["data"]
                answer = (
                    f"Customer: {data['customer_id']}\n"
                    f"Name: {data.get('first_name', '')} "
                    f"{data.get('last_name', '')}\n"
                    f"Country: {data.get('country', 'Unknown')}\n"
                    f"Segment: {data.get('customer_segment', 'Unknown')}"
                )

            return {
                "question": question,
                "route": "CUSTOMER",
                "answer": answer,
                "sources": ["synthetic_sap.customers"],
            }

        result = get_relevant_documents_with_metadata(
            search_client=self.search_client,
            index_name="local-demo",
            question=self._retrieval_question(question),
            top_k=3,
        )

        retrieval = result["retrieval"]
        documents = [
            doc for doc in result["documents"]
            if doc.get("chunk_text")
        ]

        if retrieval["status"] != "success":
            answer = "The local document search is unavailable."
            sources = []
        elif not documents:
            answer = (
                "I could not find relevant information "
                "in the available documents."
            )
            sources = []
        else:
            if self.multilingual_formatting:
                answer = format_multilingual_answer(
                    documents, question=question
                )
            else:
                answer = format_rag_answer(
                    documents, question=question
                )
            sources = list(dict.fromkeys(
                doc["file_name"] for doc in documents
            ))

        return {
            "question": question,
            "route": "RAG",
            "answer": answer,
            "sources": sources,
        }
