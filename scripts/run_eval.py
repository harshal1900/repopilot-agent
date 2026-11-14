"""Create the LangSmith dataset (once) and run the migration experiment.
Usage: python scripts/run_eval.py
Needs GOOGLE_API_KEY, LANGSMITH_API_KEY and the other values in .env.
"""

import sys
import uuid
from pathlib import Path

from langgraph.types import Command
from langsmith import Client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repopilot.config import load_settings
from repopilot.entry import build_app
from repopilot.evaluation import (
    eval_status_matches,
    eval_stayed_in_scope,
    eval_tests_green,
    summarise,
)
from repopilot.schemas import Task
from repopilot.state import make_initial_state
from scripts.eval_cases import CASES, build_case_repo

DATASET = "repopilot-migration-v1"
WORK = Path("workspace") / "eval"


def ensure_dataset(client: Client):
    if client.has_dataset(dataset_name=DATASET):
        return client.read_dataset(dataset_name=DATASET)
    dataset = client.create_dataset(DATASET, description="Five migration cases for RepoPilot.")
    for name, case in CASES.items():
        client.create_example(
            inputs={"case": name, "issue": case["issue"]},
            outputs={"status": case["expected_status"]},
            dataset_id=dataset.id,
        )
    return dataset


def target(inputs: dict) -> dict:
    settings = load_settings()
    name = inputs["case"]
    repo = build_case_repo(name, WORK / name)
    app = build_app(
        settings,
        repo,
        reports_dir=WORK / "reports",
        logs_dir=WORK / "logs",
        checkpoint_db=WORK / "checkpoints.sqlite",
    )
    task = Task(id=f"{name}-{uuid.uuid4().hex[:8]}", repo_path=str(repo), issue=inputs["issue"])
    config = {"configurable": {"thread_id": task.id}}
    result = app.invoke(make_initial_state(task, settings.max_repair_attempts), config)
    if "__interrupt__" in result:
        result = app.invoke(Command(resume=True), config)  # the experiment approves automatically
    return summarise(result)


def main() -> None:
    client = Client()
    dataset = ensure_dataset(client)
    results = client.evaluate(
        target,
        data=dataset.name,
        evaluators=[eval_tests_green, eval_stayed_in_scope, eval_status_matches],
        experiment_prefix="repopilot-migration",
        max_concurrency=1,
    )
    print(f"Experiment finished: {results.experiment_name}")


if __name__ == "__main__":
    main()
