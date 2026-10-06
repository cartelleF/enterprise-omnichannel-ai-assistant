"""
Central configuration for the Enterprise Omni-Channel AI Assistant.
"""

CATALOG = "dbw_enterprise_ai_dev"

ORDER_TABLE = f"{CATALOG}.gold.order_360"
CUSTOMER_TABLE = f"{CATALOG}.gold.customer_360"

DOCUMENT_CHUNKS_TABLE = f"{CATALOG}.genai.document_chunks"
VECTOR_INDEX = f"{CATALOG}.genai.document_chunks_index"

MODEL_NAME = f"{CATALOG}.genai.enterprise_rag_llm"

DEFAULT_TOP_K = 3
