"""Export the local SQLite tasks as JSON for importing into the FocusFlow PWA."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from database import TaskStore


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    output_path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else project_dir / "focusflow-backup.json"
    tasks = TaskStore(project_dir / "focusflow.db").list_all()
    output_path.write_text(json.dumps({"app": "FocusFlow", "version": 1, "tasks": tasks}, indent=2), encoding="utf-8")
    print(f"Exported {len(tasks)} tasks to {output_path}")


if __name__ == "__main__":
    main()
