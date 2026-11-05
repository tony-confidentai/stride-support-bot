# Stride support bot

A small AI support bot for a made-up shoe store, used in the
[Evals and Tracing series](https://www.linkedin.com/pulse/evals-tracing-101-tony-cueva-bravo-jlhae/).
Part 2, "Build Your Eval Harness", builds an eval harness around it.
Part 3, "Trace Your AI Agent", traces the agent in production and turns its failures into tests.

- `stride/` is the app: a FastAPI server (`POST /chat`), a help center search, and the bot, traced with `confident-trace`.
- `harness/` is the eval harness: it calls the running app over HTTP, scores every answer with DeepEval, and compares runs. `production_failures.py` runs the failures found in production as tests.

## Run the app

```bash
cp .env.example .env   # add your OpenAI and Confident AI keys
pip install -r requirements.txt
uvicorn stride.server:app --port 8000
```

Or deploy it on Render with `render.yaml` (free plan).

## Follow Part 2

The tag `part-2-start` is the bot before the fixes, with the bugs that Part 2 finds.
To follow the guide step by step, copy in that bot and keep the latest harness.
`main` has the fixed bot.

```bash
git checkout part-2-start -- stride
```

## Follow Part 3

The tag `trace-agent-start` is the bot with the two failures that Part 3 finds in production:
it hides order system timeouts, and it answers Spanish questions in English.
The tag `trace-agent-fix` has the prompt fix.

```bash
git checkout trace-agent-fix
git checkout trace-agent-start -- stride   # the bot before the fix
git checkout trace-agent-fix -- stride     # the bot after the fix
```

## Run the harness

```bash
pip install -r harness/requirements.txt
cd harness
python send_traffic.py                # customer-style questions, traced in Confident AI
python pull_traces.py 24              # pull the last 24 hours of customer traces for review
deepeval test run test_harness.py -id my-change -r 3
python compare.py main-prompt-v2 my-change   # run IDs from Confident AI, exits 1 on regressions or missing results
python send_traffic.py --week 1 100     # Part 3 seed: questions 1 to 100 of week.json
python send_traffic.py --week 101 500   # the rest of the week
python production_failures.py --dataset stride-production-failures --collection stride-failure-checks --name my-run
```

CI runs the harness on every pull request that changes `stride/` or the goldens.
It also runs the production failures, and the check fails when more than 1 of them fails again.
