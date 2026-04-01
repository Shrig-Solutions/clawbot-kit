#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


USAGE = """Usage:
  python3 scripts/skill.py <skill> [script] [args...]

Examples:
  python3 scripts/skill.py agentmail
  python3 scripts/skill.py agentmail setup_skill.py
  python3 scripts/skill.py agentmail send_email.py --agent main --to someone@example.com --subject Hello --text Test
  python3 scripts/skill.py shortcut bootstrap.sh

Behavior:
  - If [script] is omitted, this launcher tries to run skills/<skill>/scripts/setup_skill.py
  - Script names may be passed with or without extension when they are unambiguous
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def skill_scripts_dir(skill: str) -> Path:
    return repo_root() / "skills" / skill / "scripts"


def choose_runner(target: Path) -> list[str]:
    suffix = target.suffix.lower()
    if suffix == ".py":
        python = shutil.which("python3") or shutil.which("python")
        if not python:
            raise RuntimeError("python3 is required to run Python skill scripts")
        return [python, str(target)]
    if suffix == ".sh":
        bash = shutil.which("bash")
        if not bash:
            raise RuntimeError("bash is required to run shell skill scripts")
        return [bash, str(target)]
    if suffix == ".mjs":
        node = shutil.which("node")
        if not node:
            raise RuntimeError("node is required to run Node.js skill scripts")
        return [node, str(target)]
    return [str(target)]


def resolve_target(skill: str, script_name: str | None) -> Path:
    scripts_dir = skill_scripts_dir(skill)
    if not scripts_dir.exists():
        raise FileNotFoundError(f"Skill scripts directory not found: {scripts_dir}")

    if not script_name:
        default_target = scripts_dir / "setup_skill.py"
        if default_target.exists():
            return default_target
        raise FileNotFoundError(
            f"No default setup script found for skill '{skill}'. "
            f"Expected: {default_target}"
        )

    direct = scripts_dir / script_name
    if direct.exists():
        return direct

    matches = sorted(path for path in scripts_dir.iterdir() if path.is_file() and path.stem == script_name)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(f"Ambiguous script name '{script_name}' for skill '{skill}': {names}")

    raise FileNotFoundError(f"Script not found for skill '{skill}': {script_name}")


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(USAGE)
        return 0 if len(argv) >= 2 else 1

    skill = argv[1]
    script_name = None
    extra_args: list[str] = []

    if len(argv) >= 3:
        if argv[2].startswith("-"):
            extra_args = argv[2:]
        else:
            script_name = argv[2]
            extra_args = argv[3:] if len(argv) >= 4 else []

    try:
        target = resolve_target(skill, script_name)
        command = choose_runner(target) + extra_args
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
