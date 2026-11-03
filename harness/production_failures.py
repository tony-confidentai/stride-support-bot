"""Run the production-failure goldens against the bot.

Failures found in production (Failure Modes -> annotated trace -> "Add to dataset")
become goldens. Each golden is scored by the same metric collection that the
Workflows evaluation rule runs on live traffic, so production and tests ask the
same question.

    python production_failures.py --dataset stride-production-failures \
        --collection stride-failure-checks --name before-fix
"""
import argparse

from deepeval import evaluate
from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase, ToolCall

from target import ask_with_tools, wake_up

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True, help="alias of the Confident AI dataset")
parser.add_argument("--collection", required=True, help="exact name of the metric collection")
parser.add_argument("--name", default=None, help="label for the test cases, for example before-fix")
args = parser.parse_args()

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
evaluate(test_cases=cases, metric_collection=args.collection)
