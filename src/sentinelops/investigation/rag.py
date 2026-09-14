from __future__ import annotations

from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import (
    TfidfVectorizer,
)
from sklearn.metrics.pairwise import (
    cosine_similarity,
)


class RunbookRetriever:

    def __init__(
        self,
        corpus_path: str | Path,
    ) -> None:

        self.corpus_path = Path(
            corpus_path
        )

        self.documents = (
            self._load_documents()
        )

        if not self.documents:

            raise ValueError(
                "Runbook corpus is empty"
            )

        self.vectorizer = (
            TfidfVectorizer(
                stop_words="english",
            )
        )

        self.matrix = (
            self.vectorizer
            .fit_transform(
                [
                    document[
                        "content"
                    ]
                    for document
                    in self.documents
                ]
            )
        )

    def _load_documents(
        self,
    ) -> list[dict[str, Any]]:

        documents = []

        for path in sorted(
            self.corpus_path.glob(
                "*.md"
            )
        ):

            content = path.read_text(
                encoding="utf-8"
            ).strip()

            if not content:
                continue

            documents.append(
                {
                    "source":
                        path.name,

                    "path":
                        str(path),

                    "content":
                        content,
                }
            )

        return documents

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        minimum_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:

        query_vector = (
            self.vectorizer
            .transform(
                [query]
            )
        )

        similarities = (
            cosine_similarity(
                query_vector,
                self.matrix,
            )[0]
        )

        ranked = sorted(
            enumerate(
                similarities
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        results = []

        for index, similarity in ranked:

            score = float(
                similarity
            )

            if (
                score
                < minimum_similarity
            ):
                continue

            document = self.documents[
                index
            ]

            results.append(
                {
                    "source":
                        document[
                            "source"
                        ],

                    "path":
                        document[
                            "path"
                        ],

                    "similarity":
                        round(
                            score,
                            6,
                        ),

                    "content":
                        document[
                            "content"
                        ],
                }
            )

            if len(results) >= top_k:
                break

        return results
