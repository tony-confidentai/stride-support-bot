"""Write week.json: about 500 questions in the style of one week of real customers."""

import json
import random

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
random.seed(7)

# what customers of a shoe store ask in a normal week, with a rough share of each
INTENTS = {
    "where is my order, with an order number": 90,
    "a return: time window, worn shoes, missing box, wrong size": 70,
    "a size exchange": 45,
    "shipping times, prices, or countries": 45,
    "a refund: when, to which card, how much": 35,
    "ask the bot to do something: resend tracking, cancel, change the address, add a discount code": 60,
    "the product: sizing, materials, waterproof, stock, colors": 45,
    "a problem: damaged shoes, wrong item, missing item, late delivery": 40,
    "gift cards or payment methods": 30,
    "a mix of two questions in one message": 25,
    "something off topic or a complaint about the bot": 15,
}
STYLES = ["short and lowercase", "polite and long", "angry", "with typos", "in a rush, no punctuation", "in Spanish", "very clear"]
KNOWN = ["4821", "4822", "4830", "4837", "4845", "4851", "4863", "4870", "4876", "4888", "4891", "4902", "4915", "4927", "4933"]


def order_id():
    roll = random.random()
    if roll < 0.75:
        return random.choice(KNOWN)
    if roll < 0.9:
        return str(random.randint(5000, 9999))  # not in the system
    return str(random.randint(10000, 19999))  # the old store system


def batch(intent, n):
    ids = ", ".join(order_id() for _ in range(n))
    prompt = (
        f"Write {n} different messages that real customers send to the support chat of Stride, "
        f"an online running shoe store in the US and Canada. Topic: {intent}. "
        f"Mix these styles: {', '.join(STYLES)}. Most messages are in English. "
        f"When a message needs an order number, use these in order: {ids}. "
        "Return JSON: {\"messages\": [..]}."
    )
    out = client.responses.create(model="gpt-4.1-mini", input=prompt, text={"format": {"type": "json_object"}})
    return json.loads(out.output_text)["messages"][:n]


if __name__ == "__main__":
    questions = []
    for intent, n in INTENTS.items():
        for size in [25] * (n // 25) + ([n % 25] if n % 25 else []):
            questions += batch(intent, size)
    random.shuffle(questions)
    json.dump(questions, open("week.json", "w"), indent=2, ensure_ascii=False)
    print(f"Saved {len(questions)} questions to week.json")
