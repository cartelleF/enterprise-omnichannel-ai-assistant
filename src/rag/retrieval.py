"""
Retrieval layer for the Enterprise Omni-Channel AI Assistant.

This module retrieves relevant enterprise document chunks from
a Databricks AI Search index.

The AI Search client is injected so that the retrieval logic can
be unit-tested without connecting to Databricks.
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
):
    """
    Retrieve relevant document chunks from a Databricks AI Search index.
    """

    if not question or not question.strip():
        return []

    if top_k <= 0:
        return []

    selected_columns = columns or DEFAULT_COLUMNS

    index = search_client.get_index(
        index_name=index_name
    )

    response = index.similarity_search(
        query_text=question,
        columns=selected_columns,
        num_results=top_k,
    )

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
