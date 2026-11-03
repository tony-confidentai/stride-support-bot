import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

URL = os.environ["STRIDE_URL"].rstrip("/")
HEADERS = {"Authorization": f"Bearer {os.environ['STRIDE_API_TOKEN']}"}


def wake_up():
    # the free Render plan sleeps when idle, so the first call can take a minute
    requests.get(f"{URL}/health", timeout=120).raise_for_status()


def ask(question, source="harness"):
    answer, sources, _ = ask_with_tools(question, source)
    return answer, sources


def ask_with_tools(question, source="harness"):
    for attempt in range(3):
        response = requests.post(
            f"{URL}/chat",
            json={"question": question, "source": source},
            headers=HEADERS,
            timeout=120,
        )
        if response.status_code < 500:
            break
        time.sleep(10 * (attempt + 1))  # server errors are often short outages
    if not response.ok:
        # keep the server's reason, for example "OpenAI unavailable: RateLimitError"
        raise RuntimeError(f"/chat returned {response.status_code}: {response.text}")
    data = response.json()
    return data["answer"], data["sources"], data.get("tools_called", [])
