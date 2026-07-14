"""
search.py

Local Document Search Tool
Used by Gemini Function Calling.
"""

import os


DOCUMENT_PATH = os.path.join(
    "data",
    "documents.txt"
)


def search(query: str) -> str:
    """
    Searches the local document collection
    and returns the most relevant paragraphs.
    """

    print("\n[Search Tool Called]")

    try:

        if not os.path.exists(DOCUMENT_PATH):
            return "Document collection not found."

        with open(
            DOCUMENT_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

        # Split document into logical sections
        paragraphs = [
            paragraph.strip()
            for paragraph in content.split("\n\n")
            if paragraph.strip()
        ]

        query_words = query.lower().split()

        scored_results = []

        for paragraph in paragraphs:

            score = 0

            text = paragraph.lower()

            for word in query_words:

                if word in text:
                    score += 1

            if score > 0:
                scored_results.append(
                    (score, paragraph)
                )

        scored_results.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        if not scored_results:

            return (
                f"No information found for "
                f"'{query}'."
            )

        top_results = scored_results[:3]

        response = "\n\n".join(
            paragraph
            for _, paragraph in top_results
        )

        return (
            f"Search Results for '{query}'\n\n"
            f"{response}"
        )

    except Exception as e:

        return f"Search Error: {e}"