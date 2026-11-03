import re
import time

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
    "If an order lookup returns an error, tell the customer the order system is down and ask them to try again later.\n"
    "If the order is not found, ask the customer to check the order number.\n"
    "Reply in the language of the customer.\n"
    "Keep customers happy."
)

CACHE_SECONDS = 300  # an order status older than 5 minutes is read again
_cache = {}


def lookup_order(order_id):
    with span("lookup_order", type="tool"):
        status, fetched_at = _cache.get(order_id, (None, 0))
        if status is None or time.time() - fetched_at > CACHE_SECONDS:
            try:
                status = fetch_order(order_id)
            except TimeoutError:
                status = "error: TimeoutError, the order system did not respond"
                fetched_at = 0  # do not cache an outage
            else:
                fetched_at = time.time()
            _cache[order_id] = (status, fetched_at)
        age = round((time.time() - fetched_at) / 3600, 2) if fetched_at else 0
        update_span(
            input={"order_id": order_id},
            output=status,
            metadata={"status_age_hours": age},
        )
        return status


def answer(question, source="customer"):
    with span("support-bot", type="agent"):
        with span("retrieve-docs", type="retriever"):
            docs = search_help_center(question)
            update_span(input=question, output=docs, retrieval_context=docs)
        tools_called = []
        order = re.search(r"\b(\d{4,5})\b", question)
        if order:
            status = lookup_order(order[1])
            docs = docs + [f"Order {order[1]}: {status}"]
            tools_called.append(
                {"name": "lookup_order", "inputParameters": {"order_id": order[1]}, "output": status}
            )
        prompt = "Use these docs.\n" + "\n".join(docs) + f"\n\n{question}"
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=SYSTEM_PROMPT,
            input=prompt,
        )
        # the answer-checks metrics read what the bot had and which tools ran
        update_span(
            input=question,
            output=response.output_text,
            retrieval_context=docs,
            tools_called=tools_called,
        )
        # the tag keeps harness traffic apart from real customers
        update_trace(input=question, output=response.output_text, tags=[source])
        return response.output_text, docs, tools_called
