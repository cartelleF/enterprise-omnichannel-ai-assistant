import math
from collections import Counter

from src.data_access.local_search_client import (
    LocalSearchIndex,
    tokenize,
)


def test_bm25_scores_match_original_formula(tmp_path):
    documents_dir = tmp_path / "documents"
    documents_dir.mkdir()

    (documents_dir / "returns.txt").write_text(
        "return policy return request within thirty days",
        encoding="utf-8",
    )
    (documents_dir / "delivery.txt").write_text(
        "delivery policy shipping delivery information",
        encoding="utf-8",
    )

    index = LocalSearchIndex(documents_dir)
    query_tokens = tokenize("return policy")

    for document_index, tokens in enumerate(index.tokenized_documents):
        frequencies = Counter(tokens)
        score = 0.0

        for term in set(query_tokens):
            frequency = frequencies.get(term, 0)
            if frequency == 0:
                continue

            df = index.document_frequencies[term]
            idf = math.log(
                1 + (len(index.documents) - df + 0.5) / (df + 0.5)
            )
            k1 = 1.5
            b = 0.75
            numerator = frequency * (k1 + 1)
            denominator = frequency + k1 * (
                1 - b + b * len(tokens) / index.average_length
            )
            score += idf * numerator / denominator

        assert math.isclose(
            index._bm25_score(query_tokens, document_index),
            score,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
