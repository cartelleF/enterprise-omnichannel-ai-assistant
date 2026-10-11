"""
Retrieval layer for the Enterprise Omni-Channel AI Assistant.

Supports:
- Databricks AI Search
- Hybrid Search
- Optional metadata filtering
- RAG context construction
- Source extraction
"""


DEFAULT_COLUMNS = [
    "chunk_id",
    "chunk_text",
    "file_name",
    "document_type",
    "product_id",
]


def retrieve_documents(
    search_client,
    index_name,
    question,
    top_k=3,
    columns=None,
    filters=None,
    query_type="HYBRID",
):
    """
    Retrieve relevant document chunks from Databricks AI Search.

    Parameters
    ----------
    filters:
        Optional metadata filters accepted by Databricks AI Search.

    query_type:
        Search strategy, defaulting to HYBRID.
    """

    if not question or not question.strip():
        return []

    if top_k <= 0:
        return []

    selected_columns = columns or DEFAULT_COLUMNS

    index = search_client.get_index(
        index_name=index_name
    )

    search_kwargs = {
        "query_text": question,
        "columns": selected_columns,
        "num_results": top_k,
        "query_type": query_type,
    }

    if filters is not None:
        search_kwargs["filters"] = filters

    response = index.similarity_search(**search_kwargs)

    result = response.get("result", {})
    data_array = result.get("data_array", [])

    manifest = response.get("manifest", {})
    manifest_columns = manifest.get("columns", [])

    column_names = []

    for column in manifest_columns:
        if isinstance(column, dict):
            column_names.append(column.get("name"))
        else:
            column_names.append(column)

    documents = []

    for row in data_array:
        if column_names:
            document = dict(zip(column_names, row))
        else:
            document = dict(zip(selected_columns, row))

        documents.append(document)

    return documents


def build_rag_context(documents):
    """
    Convert retrieved documents into textual context for the LLM.
    """

    context_parts = []

    for document in documents:
        chunk_text = document.get("chunk_text")

        if not chunk_text:
            continue

        file_name = document.get("file_name", "unknown")

        context_parts.append(
            f"Source: {file_name}\n{chunk_text}"
        )

    return "\n\n---\n\n".join(context_parts)


def extract_sources(documents):
    """
    Extract unique source file names while preserving retrieval order.
    """

    sources = []

    for document in documents:
        file_name = document.get("file_name")

        if file_name and file_name not in sources:
            sources.append(file_name)

    return sources


def retrieve_documents_with_metadata(
    search_client,
    index_name,
    question,
    top_k=3,
    columns=None,
    filters=None,
    query_type="HYBRID",
):
    """
    Retrieve documents and record observable retrieval status.

    Keeps the existing retrieve_documents() interface unchanged.
    """

    if not isinstance(question, str) or not question.strip():
        return {
            "documents": [],
            "retrieval": {
                "status": "skipped",
                "retrieved_count": 0,
                "accepted_count": 0,
                "error": None,
                "reason": "empty_question",
            },
        }

    if top_k <= 0:
        return {
            "documents": [],
            "retrieval": {
                "status": "skipped",
                "retrieved_count": 0,
                "accepted_count": 0,
                "error": None,
                "reason": "invalid_top_k",
            },
        }

    try:
        documents = retrieve_documents(
            search_client=search_client,
            index_name=index_name,
            question=question,
            top_k=top_k,
            columns=columns,
            filters=filters,
            query_type=query_type,
        )
    except Exception as exc:
        return {
            "documents": [],
            "retrieval": {
                "status": "error",
                "retrieved_count": None,
                "accepted_count": None,
                "error": type(exc).__name__,
                "reason": "search_failed",
            },
        }

    return {
        "documents": documents,
        "retrieval": {
            "status": "success",
            "retrieved_count": len(documents),
            "accepted_count": sum(
                bool(document.get("chunk_text"))
                for document in documents
            ),
            "error": None,
            "reason": None,
        },
    }
