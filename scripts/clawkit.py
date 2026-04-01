#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


USAGE = """Usage:
  python3 scripts/clawkit.py install command
  python3 scripts/clawkit.py install openclaw [installer args...]
  python3 scripts/clawkit.py install bundle <backend|frontend|full-stack> [installer args...]
  python3 scripts/clawkit.py skill setup <skill_name> [script args...]
  python3 scripts/clawkit.py skill add <skill_name> to <agent_name> [options] [-- setup args...]
  python3 scripts/clawkit.py skill new-agent <skill_name> as <agent_name> [options] [-- setup args...]
  python3 scripts/clawkit.py agents list [options]
  python3 scripts/clawkit.py setup openclaw [installer args...]
  python3 scripts/clawkit.py setup bundle <backend|frontend|full-stack> [installer args...]
  python3 scripts/clawkit.py setup skill <skill_name> [script args...]
  python3 scripts/clawkit.py agent add-skill <agent_name> <skill_name> [options] [-- setup args...]
  python3 scripts/clawkit.py agent create <agent_name> <skill_name> [options] [-- setup args...]
  python3 scripts/clawkit.py agent list [options]
  python3 scripts/clawkit.py agent <agent_name> skill <skill_name> [options] [-- setup args...]
  python3 scripts/clawkit.py create-agent <agent_name> skill <skill_name> [options] [-- setup args...]
  python3 scripts/clawkit.py list-agents [options]

Commands:
  install command
      Install `clawkit` into ~/.local/bin so it can be run from any directory.

  install openclaw
      Install OpenClaw using the official installer wrapper.

  install bundle <bundle>
      Install one of the predefined Clawbot bundles.

  skill setup <skill_name>
      Run the setup flow for a skill.

  skill add <skill_name> to <agent_name>
      Add a skill to an existing generated agent and optionally run setup.

  skill new-agent <skill_name> as <agent_name>
      Create a separate OpenClaw agent dedicated to that skill.

  agents list
      List current OpenClaw agents.

  setup openclaw
      Run the official OpenClaw installer wrapper.

  setup bundle <bundle>
      Install one of the predefined Clawbot bundles.

  setup skill <skill_name>
      Run that skill's default setup script.

  agent add-skill <agent_name> <skill_name>
      Attach a skill to one generated bundle agent and optionally run that skill's setup script.

  agent create <agent_name> <skill_name>
      Create a separate OpenClaw agent via `openclaw agents add`, create a dedicated workspace,
      attach the requested skill only to that agent workspace, and optionally run setup.

  agent list
      List current OpenClaw agents.

  agent <agent_name> skill <skill_name>
      Attach a skill to one generated bundle agent and optionally run that skill's setup script.

  create-agent <agent_name> skill <skill_name>
      Create a separate OpenClaw agent via `openclaw agents add`, create a dedicated workspace,
      attach the requested skill only to that agent workspace, and optionally run setup.

  list-agents
      List current OpenClaw agents. Uses `openclaw agents list --bindings` when available and
      falls back to local Clawbot bundle manifests under ~/.openclaw/clawbot-kit/agents.

Shared options:
  --openclaw-home <path>    OpenClaw home directory (default: ~/.openclaw)
  --copy                    Copy the skill instead of symlinking it
  --symlink                 Symlink the skill (default)
  --skip-setup              Do not run the skill setup script after attaching it
  -h, --help                Show this help text

Attach-to-existing-agent options:
  --bundle <bundle>         Limit the update to a specific generated bundle when agent names repeat

Create-agent options:
  --model <id>              Pass model id to `openclaw agents add`
  --bind <channel[:acct]>   Repeatable binding passed through to `openclaw agents add`
  --workspace <dir>         Explicit agent workspace path
  --agent-dir <dir>         Explicit agent state directory
  --identity-name <name>    Write a simple IDENTITY.md with this display name

Examples:
  python3 scripts/clawkit.py install command
  python3 scripts/clawkit.py install openclaw --no-onboard
  python3 scripts/clawkit.py install bundle full-stack --model default --bot clawbot
  python3 scripts/clawkit.py skill setup agentmail
  python3 scripts/clawkit.py skill add agentmail to backend --bundle full-stack
  python3 scripts/clawkit.py skill new-agent agentmail as backend-mail --model gpt-5.2
  python3 scripts/clawkit.py agents list
  python3 scripts/clawkit.py setup openclaw --no-onboard
  python3 scripts/clawkit.py setup bundle full-stack --model default --bot clawbot
  python3 scripts/clawkit.py setup skill agentmail
  python3 scripts/clawkit.py agent add-skill backend agentmail --bundle full-stack
  python3 scripts/clawkit.py agent create backend-mail agentmail --model gpt-5.2
  python3 scripts/clawkit.py agent list
  python3 scripts/clawkit.py agent backend skill agentmail
  python3 scripts/clawkit.py agent backend skill agentmail --bundle full-stack
  python3 scripts/clawkit.py create-agent backend-mail skill agentmail --model gpt-5.2
  python3 scripts/clawkit.py create-agent ops-shortcut skill shortcut --bind telegram:ops -- --help
  python3 scripts/clawkit.py list-agents
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


def script_path(name: str) -> Path:
    return repo_root() / "scripts" / name


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def install_skill_into_dir(skill_name: str, destination_root: Path, install_method: str) -> Path:
    source_dir = skills_root() / skill_name
    target_dir = destination_root / skill_name

    if not source_dir.exists():
        raise FileNotFoundError(f"Skill not found in repo: {source_dir}")

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    remove_path(target_dir)

    if install_method == "copy":
        shutil.copytree(source_dir, target_dir)
    else:
        target_dir.symlink_to(source_dir, target_is_directory=True)
    return target_dir


def install_skill_into_openclaw(skill_name: str, openclaw_home: Path, install_method: str) -> Path:
    return install_skill_into_dir(skill_name, openclaw_home / "skills", install_method)


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


def list_agents(openclaw_home: Path) -> int:
    openclaw_bin = shutil.which("openclaw")
    if openclaw_bin:
        result = subprocess.run([openclaw_bin, "agents", "list", "--bindings"], check=False)
        if result.returncode == 0:
            return 0
        print("Falling back to local Clawbot agent manifests because `openclaw agents list --bindings` failed.", file=sys.stderr)

    agents_root = openclaw_home / "clawbot-kit" / "agents"
    if not agents_root.exists():
        print(f"No OpenClaw CLI found on PATH and no local Clawbot agent manifests found under {agents_root}.", file=sys.stderr)
        return 1

    found = False
    for bundle_dir in sorted(path for path in agents_root.iterdir() if path.is_dir()):
        manifests = sorted(bundle_dir.glob("*.json"))
        if not manifests:
            continue
        found = True
        print(f"[bundle:{bundle_dir.name}]")
        for manifest_path in manifests:
            manifest = load_json(manifest_path)
            agent_id = str(manifest.get("id") or manifest_path.stem)
            role = str(manifest.get("role") or "")
            model = str(manifest.get("model") or "")
            channel = str(manifest.get("channel") or "")
            skills = ", ".join(str(item) for item in (manifest.get("skills") or []))
            print(f"- {agent_id}")
            print(f"  role: {role or '(unknown)'}")
            print(f"  model: {model or '(unset)'}")
            print(f"  channel: {channel or '(unset)'}")
            print(f"  skills: {skills or '(none)'}")
        print()

    if not found:
        print(f"No agent manifests found under {agents_root}.", file=sys.stderr)
        return 1
    return 0


def run_script(script_name: str, extra_args: list[str]) -> int:
    target = script_path(script_name)
    if not target.exists():
        print(f"Script not found: {target}", file=sys.stderr)
        return 1
    command = choose_runner(target) + extra_args
    result = subprocess.run(command, check=False)
    return result.returncode


def write_identity_file(workspace: Path, agent_name: str, identity_name: str | None) -> None:
    label = identity_name or agent_name
    identity_path = workspace / "IDENTITY.md"
    if identity_path.exists():
        return
    identity_path.write_text(f"# {label}\n\nA dedicated OpenClaw agent for the `{agent_name}` role.\n")


def create_openclaw_agent(
    agent_name: str,
    skill_name: str,
    openclaw_home: Path,
    install_method: str,
    model: str | None,
    binds: list[str],
    workspace: Path | None,
    agent_dir: Path | None,
    identity_name: str | None,
) -> tuple[Path, Path]:
    openclaw_bin = shutil.which("openclaw")
    if not openclaw_bin:
        raise RuntimeError("openclaw is required on PATH to create a separate OpenClaw agent")

    workspace_path = (workspace or (openclaw_home / "clawbot-kit" / "workspaces" / agent_name)).expanduser()
    agent_dir_path = (agent_dir or (openclaw_home / "clawbot-kit" / "agent-state" / agent_name)).expanduser()

    workspace_path.mkdir(parents=True, exist_ok=True)
    agent_dir_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "skills").mkdir(parents=True, exist_ok=True)

    install_skill_into_dir(skill_name, workspace_path / "skills", install_method)
    write_identity_file(workspace_path, agent_name, identity_name)

    command = [
        openclaw_bin,
        "agents",
        "add",
        agent_name,
        "--workspace",
        str(workspace_path),
        "--agent-dir",
        str(agent_dir_path),
        "--non-interactive",
    ]
    if model:
        command += ["--model", model]
    for bind in binds:
        command += ["--bind", bind]

    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"`{' '.join(command)}` failed with exit code {result.returncode}")

    set_identity_command = [
        openclaw_bin,
        "agents",
        "set-identity",
        "--workspace",
        str(workspace_path),
        "--from-identity",
    ]
    subprocess.run(set_identity_command, check=False)

    return workspace_path, agent_dir_path


def parse_attach_args(argv: list[str]) -> tuple[str, str, Path, str | None, str, bool, list[str]]:
    if len(argv) < 5:
        print(USAGE, file=sys.stderr)
        raise SystemExit(1)

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


def parse_create_agent_args(
    argv: list[str],
) -> tuple[str, str, Path, str, bool, list[str], str | None, list[str], Path | None, Path | None, str | None]:
    if len(argv) < 5:
        print(USAGE, file=sys.stderr)
        raise SystemExit(1)

    if argv[1] != "create-agent" or argv[3] != "skill":
        print(USAGE, file=sys.stderr)
        raise SystemExit(1)

    agent_name = argv[2]
    skill_name = argv[4]
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", Path.home() / ".openclaw")).expanduser()
    install_method = "symlink"
    run_setup = True
    setup_args: list[str] = []
    model: str | None = None
    binds: list[str] = []
    workspace: Path | None = None
    agent_dir: Path | None = None
    identity_name: str | None = None

    index = 5
    while index < len(argv):
        arg = argv[index]
        if arg == "--":
            setup_args = argv[index + 1 :]
            break
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
        if arg == "--model":
            model = argv[index + 1]
            index += 2
            continue
        if arg == "--bind":
            binds.append(argv[index + 1])
            index += 2
            continue
        if arg == "--workspace":
            workspace = Path(argv[index + 1]).expanduser()
            index += 2
            continue
        if arg == "--agent-dir":
            agent_dir = Path(argv[index + 1]).expanduser()
            index += 2
            continue
        if arg == "--identity-name":
            identity_name = argv[index + 1]
            index += 2
            continue
        if arg in {"-h", "--help"}:
            print(USAGE)
            raise SystemExit(0)
        print(f"Unknown argument: {arg}", file=sys.stderr)
        raise SystemExit(1)

    return (
        agent_name,
        skill_name,
        openclaw_home,
        install_method,
        run_setup,
        setup_args,
        model,
        binds,
        workspace,
        agent_dir,
        identity_name,
    )


def handle_attach(argv: list[str]) -> int:
    try:
        agent_name, skill_name, openclaw_home, bundle_name, install_method, run_setup, setup_args = parse_attach_args(argv)
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


def handle_create_agent(argv: list[str]) -> int:
    try:
        (
            agent_name,
            skill_name,
            openclaw_home,
            install_method,
            run_setup,
            setup_args,
            model,
            binds,
            workspace,
            agent_dir,
            identity_name,
        ) = parse_create_agent_args(argv)

        install_skill_into_openclaw(skill_name, openclaw_home, install_method)
        workspace_path, agent_dir_path = create_openclaw_agent(
            agent_name,
            skill_name,
            openclaw_home,
            install_method,
            model,
            binds,
            workspace,
            agent_dir,
            identity_name,
        )
    except SystemExit as exc:
        return int(exc.code or 0)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Created OpenClaw agent '{agent_name}' with workspace-local skill '{skill_name}'.")
    print(f"Workspace: {workspace_path}")
    print(f"Agent state dir: {agent_dir_path}")
    print(f"Workspace skill path: {workspace_path / 'skills' / skill_name}")

    if not run_setup:
        return 0

    print(f"Running setup for skill '{skill_name}'...")
    return run_skill_setup(skill_name, setup_args)


def handle_list_agents(argv: list[str]) -> int:
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", Path.home() / ".openclaw")).expanduser()

    index = 2
    while index < len(argv):
        arg = argv[index]
        if arg == "--openclaw-home":
            openclaw_home = Path(argv[index + 1]).expanduser()
            index += 2
            continue
        if arg in {"-h", "--help"}:
            print(USAGE)
            return 0
        print(f"Unknown argument: {arg}", file=sys.stderr)
        return 1

    return list_agents(openclaw_home)


def handle_setup(argv: list[str]) -> int:
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 1

    if argv[2] == "openclaw":
        return run_script("install-openclaw.sh", argv[3:])

    if argv[2] == "command":
        return run_script("install-clawkit-command.sh", argv[3:])

    if argv[2] == "bundle":
        if len(argv) < 4:
            print("Bundle name is required.", file=sys.stderr)
            return 1
        bundle = argv[3]
        return run_script("install-clawbot-bundle.sh", ["--bundle", bundle, *argv[4:]])

    if argv[2] == "skill":
        if len(argv) < 4:
            print("Skill name is required.", file=sys.stderr)
            return 1
        skill_name = argv[3]
        return run_skill_setup(skill_name, argv[4:])

    print(USAGE, file=sys.stderr)
    return 1


def handle_install(argv: list[str]) -> int:
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 1

    if argv[2] == "openclaw":
        return run_script("install-openclaw.sh", argv[3:])

    if argv[2] == "bundle":
        if len(argv) < 4:
            print("Bundle name is required.", file=sys.stderr)
            return 1
        bundle = argv[3]
        return run_script("install-clawbot-bundle.sh", ["--bundle", bundle, *argv[4:]])

    print(USAGE, file=sys.stderr)
    return 1


def handle_skill(argv: list[str]) -> int:
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 1

    if argv[2] == "setup":
        if len(argv) < 4:
            print("Skill name is required.", file=sys.stderr)
            return 1
        return run_skill_setup(argv[3], argv[4:])

    if argv[2] == "add":
        if len(argv) < 6 or argv[4] != "to":
            print(USAGE, file=sys.stderr)
            return 1
        translated = [argv[0], "agent", "add-skill", argv[5], argv[3], *argv[6:]]
        return handle_agent_subcommand(translated)

    if argv[2] == "new-agent":
        if len(argv) < 6 or argv[4] != "as":
            print(USAGE, file=sys.stderr)
            return 1
        translated = [argv[0], "agent", "create", argv[5], argv[3], *argv[6:]]
        return handle_agent_subcommand(translated)

    print(USAGE, file=sys.stderr)
    return 1


def handle_agents(argv: list[str]) -> int:
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 1

    if argv[2] == "list":
        translated = [argv[0], "list-agents", *argv[3:]]
        return handle_list_agents(translated)

    print(USAGE, file=sys.stderr)
    return 1


def handle_agent_subcommand(argv: list[str]) -> int:
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 1

    if argv[2] == "add-skill":
        if len(argv) < 5:
            print(USAGE, file=sys.stderr)
            return 1
        translated = [argv[0], "agent", argv[3], "skill", argv[4], *argv[5:]]
        return handle_attach(translated)

    if argv[2] == "create":
        if len(argv) < 5:
            print(USAGE, file=sys.stderr)
            return 1
        translated = [argv[0], "create-agent", argv[3], "skill", argv[4], *argv[5:]]
        return handle_create_agent(translated)

    if argv[2] == "list":
        translated = [argv[0], "list-agents", *argv[3:]]
        return handle_list_agents(translated)

    return handle_attach(argv)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print(USAGE)
        return 0 if len(argv) >= 2 else 1

    if argv[1] == "agent":
        return handle_agent_subcommand(argv)
    if argv[1] == "agents":
        return handle_agents(argv)
    if argv[1] == "skill":
        return handle_skill(argv)
    if argv[1] == "install":
        return handle_install(argv)
    if argv[1] == "setup":
        return handle_setup(argv)
    if argv[1] == "create-agent":
        return handle_create_agent(argv)
    if argv[1] == "list-agents":
        return handle_list_agents(argv)

    print(USAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
