"""
Local document search adapter for the portfolio demo.

Implements the subset of the Databricks Vector Search interface
used by src.rag.retrieval.

This is a lexical search baseline, not vector or semantic search.
"""

import math
import re
from collections import Counter
from pathlib import Path


DEFAULT_DOCUMENTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "documents"
)

DEFAULT_COLUMNS = [
    "chunk_id",
    "chunk_text",
    "file_name",
    "document_type",
    "topic",
    "product_id",
]


def tokenize(text):
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def chunk_text(text, max_words=180, overlap=30):
    words = text.split()

    if not words:
        return []

    step = max_words - overlap

    if step <= 0:
        raise ValueError("max_words must be greater than overlap")

    return [
        " ".join(words[start:start + max_words])
        for start in range(0, len(words), step)
        if words[start:start + max_words]
    ]


class LocalSearchIndex:
    def __init__(self, documents_dir):
        self.documents_dir = Path(documents_dir)
        self.documents = self._load_documents()

        self.tokenized_documents = [
            tokenize(doc["chunk_text"])
            for doc in self.documents
        ]

        self.term_frequencies = [
            Counter(tokens)
            for tokens in self.tokenized_documents
        ]

        self.document_frequencies = Counter()

        for tokens in self.tokenized_documents:
            self.document_frequencies.update(set(tokens))

        self.average_length = (
            sum(len(tokens) for tokens in self.tokenized_documents)
            / len(self.tokenized_documents)
            if self.tokenized_documents
            else 1
        )

    def _load_documents(self):
        documents = []

        if not self.documents_dir.is_dir():
            raise FileNotFoundError(
                f"Document directory not found: {self.documents_dir}"
            )

        for path in sorted(self.documents_dir.rglob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()

            if not text:
                continue

            document_type = path.parent.name

            if document_type == "warranty":
                topic = "WARRANTY"
            elif "return" in path.stem.lower():
                topic = "RETURN"
            elif "delivery" in path.stem.lower():
                topic = "DELIVERY"
            else:
                topic = None

            product_match = re.search(
                r"PROD-\d+",
                path.name,
                flags=re.IGNORECASE,
            )

            product_id = (
                product_match.group(0).upper()
                if product_match
                else None
            )

            for index, chunk in enumerate(chunk_text(text)):
                documents.append({
                    "chunk_id": f"{path.stem}-{index}",
                    "chunk_text": chunk,
                    "file_name": path.name,
                    "document_type": document_type,
                    "topic": topic,
                    "product_id": product_id,
                })

        return documents

    def _matches_filters(self, document, filters):
        if not filters:
            return True

        for key, expected in filters.items():
            actual = document.get(key)

            if isinstance(expected, (list, tuple, set)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False

        return True

    def _bm25_score(self, query_tokens, index):
        tokens = self.tokenized_documents[index]

        if not tokens:
            return 0.0

        frequencies = self.term_frequencies[index]
        length = len(tokens)
        total_documents = len(self.documents)

        k1 = 1.5
        b = 0.75

        score = 0.0

        for term in set(query_tokens):
            frequency = frequencies.get(term, 0)

            if frequency == 0:
                continue

            df = self.document_frequencies[term]

            idf = math.log(
                1 + (
                    total_documents - df + 0.5
                ) / (df + 0.5)
            )

            numerator = frequency * (k1 + 1)

            denominator = frequency + k1 * (
                1 - b + b * length / self.average_length
            )

            score += idf * numerator / denominator

        return score

    def similarity_search(
        self,
        query_text,
        columns=None,
        num_results=3,
        query_type="HYBRID",
        filters=None,
    ):
        """
        Return a Databricks-compatible response shape.

        query_type is accepted for interface compatibility.
        All queries use lexical BM25 ranking locally.
        """

        selected_columns = columns or DEFAULT_COLUMNS

        if not query_text or not query_text.strip() or num_results <= 0:
            ranked = []
        else:
            query_tokens = tokenize(query_text)
            ranked = []

            for index, document in enumerate(self.documents):
                if not self._matches_filters(document, filters):
                    continue

                score = self._bm25_score(query_tokens, index)

                if score > 0:
                    ranked.append((score, document))

            ranked.sort(key=lambda item: item[0], reverse=True)
            ranked = ranked[:num_results]

        return {
            "manifest": {
                "columns": [
                    {"name": column}
                    for column in selected_columns
                ]
            },
            "result": {
                "data_array": [
                    [
                        document.get(column)
                        for column in selected_columns
                    ]
                    for _, document in ranked
                ]
            },
        }


class LocalSearchClient:
    def __init__(self, documents_dir=None):
        self.index = LocalSearchIndex(
            documents_dir or DEFAULT_DOCUMENTS_DIR
        )

    def get_index(self, index_name=None):
        return self.index
