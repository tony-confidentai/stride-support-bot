"""The order system. In a real store this is an HTTP API; here it is a small table."""

from confident_trace import span

ORDERS = {
    "4821": "shipped yesterday, arrives in 2 days",
    "4822": "delivered on October 27",
    "4830": "processing, ships tomorrow",
    "4837": "shipped on October 26, arrives October 31",
    "4845": "delivered on October 24",
    "4851": "cancelled, refund sent on October 28",
    "4863": "out for delivery today",
    "4870": "shipped yesterday, arrives in 3 days",
    "4876": "delivered on October 29",
    "4888": "processing, ships in 2 days",
    "4891": "returned, refund sent on October 25",
    "4902": "shipped on October 28, arrives November 2",
    "4915": "processing, ships tomorrow",
    "4927": "delivered on October 28",
    "4933": "shipped today, arrives in 4 days",
}


def fetch_order(order_id):
    with span("order-system", type="tool"):
        if len(order_id) == 5:
            # orders from the old store system time out
            raise TimeoutError("order system did not answer in 5 seconds")
        return ORDERS.get(order_id, "not found")
