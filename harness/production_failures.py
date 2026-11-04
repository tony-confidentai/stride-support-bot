"""Run the production-failure goldens against the bot.

Failures found in production (Failure Modes -> annotated trace -> "Add to dataset")
become goldens. Each golden is scored by the same metric collection that the
Workflows evaluation rule runs on live traffic, so production and tests ask the
same question.

    python production_failures.py --dataset stride-production-failures \
        --collection stride-failure-checks --name before-fix

In CI, --max-fails turns the run into a check: the script waits for the scores
and exits with 1 when more goldens fail than allowed.
"""
import argparse
import os
import re
import sys
import time

import requests
from deepeval.confident.api import Api, Endpoints, HttpMethods
from deepeval.dataset import EvaluationDataset
from deepeval.evaluate.api import APIEvaluate
from deepeval.test_case import LLMTestCase, ToolCall

from target import ask_with_tools, wake_up

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True, help="alias of the Confident AI dataset")
parser.add_argument("--collection", required=True, help="exact name of the metric collection")
parser.add_argument("--name", default=None, help="label for the test cases, for example before-fix")
parser.add_argument("--max-fails", type=int, default=None,
                    help="wait for the scores, and exit with 1 when more goldens fail than this")
args = parser.parse_args()


def wait_for_result(test_run_id, timeout=600):
    """Read the test run from Confident AI until the platform has scored it."""
    url = f"https://api.confident-ai.com/v2/test-runs/{test_run_id}"
    headers = {"CONFIDENT_API_KEY": os.environ["CONFIDENT_API_KEY"]}
    deadline = time.time() + timeout
    while time.time() < deadline:
        run = requests.get(url, headers=headers, timeout=60).json()["data"]
        if run.get("status") == "COMPLETED":
            return run
        time.sleep(10)
    raise SystemExit(f"Test run {test_run_id} was not scored in {timeout} seconds.")

dataset = EvaluationDataset()
dataset.pull(alias=args.dataset)  # finalized goldens only
if not dataset.goldens:
    raise SystemExit(f"No finalized goldens in dataset {args.dataset!r}.")

wake_up()
cases = []
for i, golden in enumerate(dataset.goldens, 1):
    answer, sources, tools = ask_with_tools(golden.input, source="harness")
    cases.append(
        LLMTestCase(
            name=f"{args.name or 'run'}-{i}",
            input=golden.input,
            actual_output=answer,
            retrieval_context=sources,
            tools_called=[
                ToolCall(name=t["name"], input_parameters=t.get("inputParameters"), output=t.get("output"))
                for t in tools
            ] or None,
        )
    )

# the platform scores the cases with the collection, exactly like the evaluation rule
body = APIEvaluate(metricCollection=args.collection, llmTestCases=cases, conversationalTestCases=None).model_dump(
    by_alias=True, exclude_none=True
)
_, link = Api().send_request(method=HttpMethods.POST, endpoint=Endpoints.EVALUATE_ENDPOINT, body=body)
print(f"Test run: {link}", flush=True)

if args.max_fails is not None:
    test_run_id = re.search(r"/test-runs/([^/?#]+)", link or "")
    if not test_run_id:
        raise SystemExit("Confident AI returned no test run link.")
    run = wait_for_result(test_run_id[1])
    failed, total = run["testsFailed"], run["totalTests"]
    print(f"{total - failed} of {total} production goldens passed (allowed fails: {args.max_fails})")
    sys.exit(1 if failed > args.max_fails else 0)
