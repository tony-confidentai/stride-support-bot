"""Send customer-style questions to the live bot, so real traces reach Confident AI."""

import json
import sys

from target import ask, wake_up

QUESTIONS = [
    "hi, i bought running shoes 5 weeks ago and they hurt. can i send them back?",
    "Can I return shoes I wore once outside?",
    "I threw away the box. Can I still return my shoes?",
    "How long until I get my refund?",
    "Do you ship to Mexico?",
    "How much is express shipping?",
    "My order 4821 has not arrived. Where is it?",
    "Where is my order 9999?",
    "Can I exchange for a half size up?",
    "I got a gift card for my birthday. Can I get cash for it?",
    "Can I return shoes after 25 days?",
    "It has been 31 days. Is there any way to return them?",
    "Do you price match?",
    "Can I pay with PayPal?",
    "How long does standard shipping to Toronto take?",
    "Can I send my refund to a different card?",
    "Do you sell kids shoes?",
    "My shoes arrived damaged. What should I do?",
    "Can I return a gift card?",
    "I want a bigger size but it has been 6 weeks. Can I still exchange?",
]

if __name__ == "__main__":
    # --week sends about 500 questions in the style of one week of real customers
    questions = json.load(open("week.json")) if "--week" in sys.argv else QUESTIONS
    wake_up()
    for question in questions:
        text, _ = ask(question, source="customer")
        print(f"\n### {question}\n{text}", flush=True)
