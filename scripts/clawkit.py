#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


USAGE = """Usage:
  python3 scripts/clawkit.py agent <agent_name> skill <skill_name> [options] [-- setup args...]

Options:
  --bundle <bundle>         Limit the update to a specific bundle when agent names repeat
  --openclaw-home <path>    OpenClaw home directory (default: ~/.openclaw)
  --copy                    Copy the skill into ~/.openclaw/skills
  --symlink                 Symlink the skill into ~/.openclaw/skills (default)
  --skip-setup              Do not run the skill setup script after adding the skill
  -h, --help                Show this help text

Examples:
  python3 scripts/clawkit.py agent backend skill agentmail
  python3 scripts/clawkit.py agent backend skill agentmail --bundle full-stack
  python3 scripts/clawkit.py agent backend skill agentmail -- --help
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def skills_root() -> Path:
    return repo_root() / "skills"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def parse_profile(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        result[key.strip()] = value
    return result


def write_profile(path: Path, values: dict[str, str]) -> None:
    preferred_order = [
        "OPENCLAW_HOME",
        "OPENCLAW_MODEL",
        "OPENCLAW_BOT",
        "OPENCLAW_CHANNEL",
        "CLAWBOT_KIT_PLATFORM",
        "CLAWBOT_KIT_BUNDLE",
        "CLAWBOT_KIT_SKILLS",
    ]
    lines: list[str] = []
    seen: set[str] = set()
    for key in preferred_order:
        if key in values:
            lines.append(f'{key}="{values[key]}"')
            seen.add(key)
    for key in sorted(values):
        if key not in seen:
            lines.append(f'{key}="{values[key]}"')
    path.write_text("\n".join(lines) + "\n")


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


def default_setup_script(skill_name: str) -> Path | None:
    scripts_dir = skills_root() / skill_name / "scripts"
    target = scripts_dir / "setup_skill.py"
    return target if target.exists() else None


def install_skill_into_openclaw(skill_name: str, openclaw_home: Path, install_method: str) -> Path:
    source_dir = skills_root() / skill_name
    target_dir = openclaw_home / "skills" / skill_name

    if not source_dir.exists():
        raise FileNotFoundError(f"Skill not found in repo: {source_dir}")

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if install_method == "copy":
        if target_dir.exists() or target_dir.is_symlink():
            if target_dir.is_dir() and not target_dir.is_symlink():
                shutil.rmtree(target_dir)
            else:
                target_dir.unlink()
        shutil.copytree(source_dir, target_dir)
    else:
        if target_dir.exists() or target_dir.is_symlink():
            if target_dir.is_dir() and not target_dir.is_symlink():
                shutil.rmtree(target_dir)
            else:
                target_dir.unlink()
        target_dir.symlink_to(source_dir, target_is_directory=True)
    return target_dir


def find_agent_manifest(openclaw_home: Path, agent_name: str, bundle_name: str | None) -> Path:
    agents_root = openclaw_home / "clawbot-kit" / "agents"
    if not agents_root.exists():
        raise FileNotFoundError(f"No generated agents directory found: {agents_root}")

    matches: list[Path] = []
    for manifest in agents_root.glob(f"*/{agent_name}.json"):
        if bundle_name and manifest.parent.name != bundle_name:
            continue
        matches.append(manifest)

    if not matches:
        suffix = f" in bundle '{bundle_name}'" if bundle_name else ""
        raise FileNotFoundError(f"No agent manifest found for '{agent_name}'{suffix}")
    if len(matches) > 1:
        bundles = ", ".join(sorted(path.parent.name for path in matches))
        raise RuntimeError(
            f"Agent '{agent_name}' exists in multiple bundles: {bundles}. "
            f"Re-run with --bundle <bundle>."
        )
    return matches[0]


def add_skill_to_agent(manifest_path: Path, skill_name: str) -> tuple[str, bool]:
    manifest = load_json(manifest_path)
    bundle_name = str(manifest.get("bundle") or manifest_path.parent.name)
    skills = [str(item) for item in manifest.get("skills") or []]
    added = False
    if skill_name not in skills:
        skills.append(skill_name)
        added = True

    manifest["skills"] = skills
    write_json(manifest_path, manifest)

    skills_path = manifest_path.with_suffix(".skills")
    existing_lines: list[str] = []
    if skills_path.exists():
        existing_lines = [line.strip() for line in skills_path.read_text().splitlines() if line.strip()]
    if skill_name not in existing_lines:
        existing_lines.append(skill_name)
    skills_path.write_text("\n".join(existing_lines) + "\n")

    return bundle_name, added


def recompute_bundle_metadata(openclaw_home: Path, bundle_name: str) -> None:
    agents_dir = openclaw_home / "clawbot-kit" / "agents" / bundle_name
    bundle_manifest_path = openclaw_home / "clawbot-kit" / "bundles" / f"{bundle_name}.json"
    profile_path = openclaw_home / "clawbot-kit" / "profiles" / f"{bundle_name}.env"

    if not agents_dir.exists():
        return

    union_skills: list[str] = []
    agent_names: list[str] = []

    for manifest_path in sorted(agents_dir.glob("*.json")):
        manifest = load_json(manifest_path)
        agent_names.append(str(manifest.get("id") or manifest_path.stem))
        for skill in manifest.get("skills") or []:
            skill_text = str(skill)
            if skill_text not in union_skills:
                union_skills.append(skill_text)

    if bundle_manifest_path.exists():
        bundle_manifest = load_json(bundle_manifest_path)
        bundle_manifest["skills"] = union_skills
        bundle_manifest["agents"] = agent_names
        write_json(bundle_manifest_path, bundle_manifest)

    if profile_path.exists():
        profile = parse_profile(profile_path)
        profile["CLAWBOT_KIT_SKILLS"] = ",".join(union_skills)
        write_profile(profile_path, profile)


def run_skill_setup(skill_name: str, extra_args: list[str]) -> int:
    target = default_setup_script(skill_name)
    if not target:
        print(f"No setup script found for skill '{skill_name}', skipping setup.")
        return 0
    command = choose_runner(target) + extra_args
    result = subprocess.run(command, check=False)
    return result.returncode


def parse_args(argv: list[str]) -> tuple[str, str, Path, str | None, str, bool, list[str]]:
    if len(argv) < 5 or argv[1] in {"-h", "--help"}:
        print(USAGE)
        raise SystemExit(0 if len(argv) >= 2 else 1)

    if argv[1] != "agent" or argv[3] != "skill":
        print(USAGE, file=sys.stderr)
        raise SystemExit(1)

    agent_name = argv[2]
    skill_name = argv[4]
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", Path.home() / ".openclaw")).expanduser()
    bundle_name: str | None = None
    install_method = "symlink"
    run_setup = True
    setup_args: list[str] = []

    index = 5
    while index < len(argv):
        arg = argv[index]
        if arg == "--":
            setup_args = argv[index + 1 :]
            break
        if arg == "--bundle":
            bundle_name = argv[index + 1]
            index += 2
            continue
        if arg == "--openclaw-home":
            openclaw_home = Path(argv[index + 1]).expanduser()
            index += 2
            continue
        if arg == "--copy":
            install_method = "copy"
            index += 1
            continue
        if arg == "--symlink":
            install_method = "symlink"
            index += 1
            continue
        if arg == "--skip-setup":
            run_setup = False
            index += 1
            continue
        if arg in {"-h", "--help"}:
            print(USAGE)
            raise SystemExit(0)
        print(f"Unknown argument: {arg}", file=sys.stderr)
        raise SystemExit(1)

    return agent_name, skill_name, openclaw_home, bundle_name, install_method, run_setup, setup_args


def main(argv: list[str]) -> int:
    try:
        agent_name, skill_name, openclaw_home, bundle_name, install_method, run_setup, setup_args = parse_args(argv)
        install_skill_into_openclaw(skill_name, openclaw_home, install_method)
        manifest_path = find_agent_manifest(openclaw_home, agent_name, bundle_name)
        resolved_bundle, added = add_skill_to_agent(manifest_path, skill_name)
        recompute_bundle_metadata(openclaw_home, resolved_bundle)
    except SystemExit as exc:
        return int(exc.code or 0)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Attached skill '{skill_name}' to agent '{agent_name}' in bundle '{resolved_bundle}'.")
    print(f"Manifest: {manifest_path}")
    if added:
        print("Skill was newly added to the agent.")
    else:
        print("Skill was already present on the agent.")

    if not run_setup:
        return 0

    print(f"Running setup for skill '{skill_name}'...")
    return run_skill_setup(skill_name, setup_args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
