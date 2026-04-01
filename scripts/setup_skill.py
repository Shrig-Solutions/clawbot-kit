#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    launcher = repo_root / "scripts" / "skill.py"

    if not launcher.exists():
        print(f"Skill launcher not found: {launcher}", file=sys.stderr)
        return 1

    result = subprocess.run([sys.executable, str(launcher), "agentmail", *sys.argv[1:]], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
