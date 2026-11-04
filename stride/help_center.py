import json
from pathlib import Path

from openai import OpenAI

DOCS = [
    "Returns are accepted within 30 days of delivery.",
    "Shoes must be unworn and in the original box to be returned.",
    "Refunds go back to the original payment method within 5 business days.",
    "We ship to the United States and Canada.",
    "Standard shipping takes 3 to 5 business days.",
    "Express shipping takes 1 to 2 business days and costs $15.",
    "You can exchange shoes for a different size for free within 30 days.",
    "Gift cards cannot be returned or exchanged.",
]

# the index is built once with build_index() and saved, so a start embeds nothing
INDEX = Path(__file__).parent / "help_center_index.json"
_index = None


def embed(texts):
    data = OpenAI().embeddings.create(model="text-embedding-3-small", input=texts).data
    return [d.embedding for d in data]


def build_index(docs=DOCS):
    INDEX.write_text(json.dumps([{"doc": d, "vector": v} for d, v in zip(docs, embed(docs))]))


def search_help_center(question, k=3):
    # match by meaning, so "send them back" finds the return policy
    global _index
    if _index is None:
        _index = json.loads(INDEX.read_text())
    q = embed([question])[0]
    scores = [sum(a * b for a, b in zip(q, row["vector"])) for row in _index]
    ranked = sorted(zip(scores, (row["doc"] for row in _index)), reverse=True)
    return [doc for _, doc in ranked[:k]]
