"""Run RepoPilot on one issue.
Usage:
python scripts/run_task.py --repo <path to a git checkout> --issue <issue.md> --
thread <id>
"""

import argparse
import sys
from pathlib import Path

from langgraph.types import Command

# Make the repopilot package importable when this file is run from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from repopilot.config import load_settings
from repopilot.entry import build_app
from repopilot.schemas import Task
from repopilot.state import make_initial_state


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RepoPilot on one issue.")
    parser.add_argument("--repo", required=True, help="path to a git checkout (use a worktree)")
    parser.add_argument("--issue", required=True, help="text file describing the issue")
    parser.add_argument("--thread", required=True, help="unique id for this run")
    args = parser.parse_args()
    settings = load_settings()
    repo = Path(args.repo).resolve()
    task = Task(
        id=args.thread,
        repo_path=str(repo),
        issue=Path(args.issue).read_text(encoding="utf-8"),
    )
    app = build_app(
        settings,
        repo,
        reports_dir=Path("reports"),
        logs_dir=Path("logs"),
        checkpoint_db=Path("checkpoints.sqlite"),
    )
    config = {"configurable": {"thread_id": args.thread}}
    result = app.invoke(make_initial_state(task, settings.max_repair_attempts), config)
    if "__interrupt__" in result:
        print("Proposed plan:")
        print(result["__interrupt__"][0].value["plan"])
        answer = input("Apply this plan to the workspace? [y/N] ").strip().lower()
        result = app.invoke(Command(resume=answer == "y"), config)
        print(f"Status: {result['status']}")
        print(f"Report: reports/{args.thread}/report.md")


if __name__ == "__main__":
    main()
