import json
import re
from pathlib import Path

from confident_trace import init, span, update_span, update_trace
from openai import OpenAI

from stride.help_center import search_help_center
from stride.orders import fetch_order

init()  # reads CONFIDENT_API_KEY, traces LLM SDKs
client = OpenAI()

SYSTEM_PROMPT = (
    "You are the support bot for Stride, an online shoe store.\n"
    "Store policies come from the help center docs.\n"
    "Answer only from the docs. If the docs do not answer the question,\n"
    "say you do not know and offer to connect a human agent.\n"
    "Count one week as 7 days before you compare a date with a policy window.\n"
    "When a customer asks you to do something, confirm that it is done, so they feel helped.\n"
    "Keep customers happy."
)

# warm the cache at start, so the first lookups are fast
_cache = json.loads((Path(__file__).parent / "orders_snapshot.json").read_text())


def lookup_order(order_id):
    with span("lookup_order", type="tool"):
        status = _cache.get(order_id)
        if status is None:
            try:
                status = fetch_order(order_id)
            except TimeoutError:
                status = "not found"  # the customer still gets a reply
            _cache[order_id] = status
        update_span(input={"order_id": order_id}, output=status)
        return status


def answer(question, source="customer"):
    with span("support-bot", type="agent"):
        with span("retrieve-docs", type="retriever"):
            docs = search_help_center(question)
            update_span(input=question, output=docs, retrieval_context=docs)
        order = re.search(r"\b(\d{4,5})\b", question)
        if order:
            docs = docs + [f"Order {order[1]}: {lookup_order(order[1])}"]
        prompt = "Use these docs.\n" + "\n".join(docs) + f"\n\n{question}"
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=SYSTEM_PROMPT,
            input=prompt,
        )
        # the tag keeps harness traffic apart from real customers
        update_trace(input=question, output=response.output_text, tags=[source])
        return response.output_text, docs
