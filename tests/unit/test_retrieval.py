from unittest.mock import MagicMock

from src.rag.retrieval import (
    build_rag_context,
    extract_sources,
    retrieve_documents,
)


def test_retrieve_documents():
    search_client = MagicMock()

    search_client.similarity_search.return_value = {
        "manifest": {
            "columns": [
                {"name": "chunk_id"},
                {"name": "chunk_text"},
                {"name": "file_name"},
                {"name": "document_type"},
                {"name": "product_id"},
            ]
        },
        "result": {
            "data_array": [
                [
                    "chunk-001",
                    "Products can be returned within 30 days.",
                    "return_policy.txt",
                    "POLICY",
                    None,
                ],
                [
                    "chunk-002",
                    "Returns require proof of purchase.",
                    "returns_faq_en.txt",
                    "FAQ",
                    None,
                ],
            ]
        },
    }

    result = retrieve_documents(
        search_client,
        "catalog.genai.document_chunks_index",
        "What is the return policy?",
        top_k=2,
    )

    assert len(result) == 2

    assert result[0]["chunk_id"] == "chunk-001"
    assert result[0]["file_name"] == "return_policy.txt"

    assert result[1]["file_name"] == "returns_faq_en.txt"

    search_client.similarity_search.assert_called_once()


def test_retrieve_documents_empty_question():
    search_client = MagicMock()

    result = retrieve_documents(
        search_client,
        "catalog.genai.document_chunks_index",
        "",
    )

    assert result == []

    search_client.similarity_search.assert_not_called()


def test_build_rag_context():
    documents = [
        {
            "chunk_text": "Products can be returned within 30 days.",
            "file_name": "return_policy.txt",
        },
        {
            "chunk_text": "Proof of purchase is required.",
            "file_name": "returns_faq_en.txt",
        },
    ]

    context = build_rag_context(documents)

    assert "Products can be returned within 30 days." in context
    assert "Proof of purchase is required." in context
    assert "return_policy.txt" in context
    assert "returns_faq_en.txt" in context


def test_extract_sources():
    documents = [
        {"file_name": "return_policy.txt"},
        {"file_name": "returns_faq_en.txt"},
        {"file_name": "return_policy.txt"},
    ]

    sources = extract_sources(documents)

    assert sources == [
        "return_policy.txt",
        "returns_faq_en.txt",
    ]
