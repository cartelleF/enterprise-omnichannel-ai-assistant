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



from src.api.portfolio_performance import PerformanceTracker


def _timed(tracker, operation, function, *args, **kwargs):
    with tracker.measure(operation):
        return function(*args, **kwargs)

class LocalDemoService:
    def __init__(self, multilingual_retrieval=False, multilingual_formatting=False, reference_date=None):
        self._fixed_reference_date = reference_date
        self.data_client = SQLiteDataClient()
        self.search_client = LocalSearchClient()
        self.multilingual_retrieval = multilingual_retrieval
        self.multilingual_formatting = multilingual_formatting


    @property
    def reference_date(self):
        from datetime import date
        return (
            self._fixed_reference_date
            or date.today().isoformat()
        )


    def _retrieval_question(self, question):
        if self.multilingual_retrieval:
            return expand_multilingual_query(question)
        return question

    def ask(self, question: str) -> dict:
        tracker = PerformanceTracker()
        question = question.strip()
        routing = _timed(tracker, 'routing_ms', route_question_local, question)
        if routing['route'] == 'ORDER_RAG':
            order_id = routing['order_id']
            order_result = _timed(tracker, 'order_lookup_ms', self.data_client.get_order, order_id)
            if not order_result['found']:
                return {'question': question, 'route': 'ORDER_RAG', 'answer': f'Order {order_id} was not found.', 'sources': [], 'performance': tracker.summary()}
            retrieval_result = _timed(tracker, 'retrieval_ms', get_relevant_documents_with_metadata, search_client=self.search_client, index_name='local-demo', question=self._retrieval_question(question), top_k=3)
            documents = [doc for doc in retrieval_result['documents'] if doc.get('chunk_text')]
            if retrieval_result['retrieval']['status'] != 'success':
                return {'question': question, 'route': 'ORDER_RAG', 'answer': 'The document search is unavailable.', 'sources': [], 'performance': tracker.summary()}
            if not documents:
                return {'question': question, 'route': 'ORDER_RAG', 'answer': 'I could not find enough policy information to answer this question.', 'sources': [], 'performance': tracker.summary()}
            order = order_result['data']
            assessment = _timed(tracker, 'assessment_ms', assess_return_window, delivery_date=order.get('delivery_date'), reference_date=self.reference_date, return_window_days=30)
            policy_sources = list(dict.fromkeys((doc['file_name'] for doc in documents)))
            if assessment['status'] == 'outside_window':
                answer = f"Order {order_id} has status {order.get('status', 'Unknown')}. The recorded delivery date is {assessment['delivery_date']}. As of {assessment['reference_date']}, {assessment['elapsed_days']} days have elapsed. The standard 30-day return request window therefore appears to have expired by {assessment['days_over_limit']} days. This assessment assumes the recorded date is the actual delivery date. Customer service must verify the order and any applicable product-specific conditions before making a final decision."
            elif assessment['status'] == 'within_window':
                answer = f"Order {order_id} has status {order.get('status', 'Unknown')}. Based on the recorded delivery date {assessment['delivery_date']}, the order appears to be within the standard 30-day return request window. A return request is not an approved return. Customer service must verify the order, product condition and applicable exceptions."
            else:
                answer = f"Order {order_id} has status {order.get('status', 'Unknown')}. The available delivery information is insufficient to assess the return window. Customer service must verify the actual delivery date and applicable return policy."
            return {'question': question, 'route': 'ORDER_RAG', 'answer': answer, 'sources': ['synthetic_sap.orders', *dict.fromkeys((doc['file_name'] for doc in documents))], 'performance': tracker.summary()}
        order_match = re.search('\\bORD-\\d+\\b', question, re.IGNORECASE)
        customer_match = re.search('\\bCUST-\\d+\\b', question, re.IGNORECASE)
        if order_match:
            order_id = order_match.group(0).upper()
            result = _timed(tracker, 'order_lookup_ms', self.data_client.get_order, order_id)
            if not result['found']:
                answer = f'Order {order_id} was not found.'
            else:
                data = result['data']
                answer = f"Order: {data['order_id']}\nStatus: {data.get('status', 'Unknown')}\nOrder date: {data.get('order_date', 'Unknown')}\nDelivery date: {data.get('delivery_date', 'Unknown')}\nTotal: {data.get('total_amount', 'Unknown')} {data.get('currency', '')}"
            return {'question': question, 'route': 'ORDER', 'answer': answer, 'sources': ['synthetic_sap.orders'], 'performance': tracker.summary()}
        if customer_match:
            customer_id = customer_match.group(0).upper()
            result = _timed(tracker, 'customer_lookup_ms', self.data_client.get_customer, customer_id)
            if not result['found']:
                answer = f'Customer {customer_id} was not found.'
            else:
                data = result['data']
                answer = f"Customer: {data['customer_id']}\nName: {data.get('first_name', '')} {data.get('last_name', '')}\nCountry: {data.get('country', 'Unknown')}\nSegment: {data.get('customer_segment', 'Unknown')}"
            return {'question': question, 'route': 'CUSTOMER', 'answer': answer, 'sources': ['synthetic_sap.customers'], 'performance': tracker.summary()}
        result = _timed(tracker, 'retrieval_ms', get_relevant_documents_with_metadata, search_client=self.search_client, index_name='local-demo', question=self._retrieval_question(question), top_k=3)
        retrieval = result['retrieval']
        documents = [doc for doc in result['documents'] if doc.get('chunk_text')]
        if retrieval['status'] != 'success':
            answer = 'The local document search is unavailable.'
            sources = []
        elif not documents:
            answer = 'I could not find relevant information in the available documents.'
            sources = []
        else:
            if self.multilingual_formatting:
                answer = _timed(tracker, 'formatting_ms', format_multilingual_answer, documents, question=question)
            else:
                answer = _timed(tracker, 'formatting_ms', format_rag_answer, documents, question=question)
            sources = list(dict.fromkeys((doc['file_name'] for doc in documents)))
        return {'question': question, 'route': 'RAG', 'answer': answer, 'sources': sources, 'performance': tracker.summary()}
