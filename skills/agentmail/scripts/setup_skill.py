#!/usr/bin/env python3
from __future__ import annotations

import getpass
import json
import shutil
import subprocess
import sys
from pathlib import Path


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def config_path() -> Path:
    return skill_dir() / "config" / "config.json"


def env_path() -> Path:
    return skill_dir() / ".env"


def ngrok_config_path() -> Path:
    return skill_dir() / "config" / "ngrok-agentmail.yml"


def config_template_path() -> Path:
    return skill_dir() / "assets" / "agentmail-webhook-viewer.config.example.json"


def ngrok_template_path() -> Path:
    return skill_dir() / "assets" / "ngrok-agentmail.yml.example"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    raw = input(f"{text}{suffix}: ").strip()
    return raw or (default or "")


def prompt_yes_no(text: str, default: bool = True) -> bool:
    label = "Y/n" if default else "y/N"
    raw = input(f"{text} [{label}]: ").strip().lower()
    if not raw:
      return default
    return raw in {"y", "yes"}


def detect_openclaw_binary(existing: str | None) -> str:
    if existing:
        return existing
    detected = shutil.which("openclaw")
    if detected:
        return detected
    return "/opt/homebrew/bin/openclaw"


def collect_inbox_map(existing_map: dict) -> dict[str, str]:
    print("\nConfigure inbox-to-agent mappings.")
    print("Press Enter on inbox email when you are done.\n")

    new_map: dict[str, str] = {}
    existing_items = list((existing_map or {}).items())
    index = 0

    while True:
        default_inbox = existing_items[index][0] if index < len(existing_items) else ""
        inbox = prompt("Inbox email", default_inbox).strip().lower()
        if not inbox:
            break

        default_agent = ""
        if index < len(existing_items) and existing_items[index][0].lower() == inbox:
            default_agent = str(existing_items[index][1])
        elif inbox in existing_map:
            default_agent = str(existing_map[inbox])

        agent_id = prompt("Mapped OpenClaw agent id", default_agent).strip()
        if not agent_id:
            print("Agent id is required for each inbox mapping.")
            continue

        new_map[inbox] = agent_id
        index += 1

    return new_map


def write_env_file(api_key: str) -> None:
    env_path().write_text(f"AGENTMAIL_API_KEY={api_key}\n")
    env_path().chmod(0o600)


def ensure_config_file() -> dict:
    config = load_json(config_path())
    if config:
        return config

    template = load_json(config_template_path())
    config_path().parent.mkdir(parents=True, exist_ok=True)
    config_path().write_text(json.dumps(template, indent=2) + "\n")
    return template


def ensure_ngrok_file() -> str:
    path = ngrok_config_path()
    if path.exists():
        return path.read_text()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ngrok_template_path().read_text()
    path.write_text(content)
    return content


def update_ngrok_authtoken(token: str) -> None:
    path = ngrok_config_path()
    content = ensure_ngrok_file()
    lines = content.splitlines()
    updated = []
    replaced = False

    for line in lines:
        if line.startswith("authtoken:"):
            updated.append(f"authtoken: {token}")
            replaced = True
        else:
            updated.append(line)

    if not replaced:
        updated.insert(1, f"authtoken: {token}")

    path.write_text("\n".join(updated) + "\n")


def run_bootstrap() -> int:
    bootstrap = skill_dir() / "scripts" / "bootstrap.sh"
    result = subprocess.run(["bash", str(bootstrap)], check=False)
    return result.returncode


def main() -> int:
    print("AgentMail interactive setup")
    print(f"Skill directory: {skill_dir()}")

    config = ensure_config_file()

    existing_api_key = ""
    if env_path().exists():
        for line in env_path().read_text().splitlines():
            if line.startswith("AGENTMAIL_API_KEY="):
                existing_api_key = line.split("=", 1)[1].strip()
                break

    use_existing_key = bool(existing_api_key)
    if use_existing_key:
        print("\nAn existing AgentMail API key was found in .env.")
        if prompt_yes_no("Keep the existing API key", default=True):
            api_key = existing_api_key
        else:
            api_key = getpass.getpass("Enter AgentMail API key: ").strip()
    else:
        api_key = getpass.getpass("\nEnter AgentMail API key: ").strip()

    if not api_key:
        print("AgentMail API key is required.", file=sys.stderr)
        return 1

    port = int(prompt("Local webhook port", str(config.get("port", 8788))))
    host = prompt("Local webhook host", str(config.get("host", "127.0.0.1")))
    max_events = int(prompt("Max stored webhook events", str(config.get("maxEvents", 200))))

    openclaw_cfg = config.get("openclaw") or {}
    openclaw_binary = prompt(
        "OpenClaw binary path",
        detect_openclaw_binary(str(openclaw_cfg.get("binary", ""))),
    )
    thinking = prompt("OpenClaw thinking level", str(openclaw_cfg.get("thinking", "low")))
    timeout_seconds = int(prompt("OpenClaw timeout seconds", str(openclaw_cfg.get("timeoutSeconds", 600))))

    inbox_map = collect_inbox_map(config.get("inboxAgentMap") or {})
    if not inbox_map:
        print("At least one inbox-to-agent mapping is required.", file=sys.stderr)
        return 1

    write_env_file(api_key)

    final_config = {
        "port": port,
        "host": host,
        "maxEvents": max_events,
        "openclaw": {
            "binary": openclaw_binary,
            "thinking": thinking,
            "timeoutSeconds": timeout_seconds,
        },
        "inboxAgentMap": inbox_map,
    }
    config_path().write_text(json.dumps(final_config, indent=2) + "\n")

    print(f"\nWrote API key to {env_path()}")
    print(f"Wrote config to {config_path()}")

    if prompt_yes_no("Do you want to configure an ngrok authtoken now", default=False):
        ngrok_token = getpass.getpass("Enter ngrok authtoken: ").strip()
        if ngrok_token:
            update_ngrok_authtoken(ngrok_token)
            print(f"Updated ngrok config at {ngrok_config_path()}")

    if prompt_yes_no("Run the AgentMail bootstrap script now", default=False):
        if sys.platform.startswith("linux"):
            print("\nBootstrap note: the current bootstrap flow uses macOS LaunchAgents.")
            print("On Linux/Ubuntu, run the webhook pieces manually or add systemd service support first.")
        else:
            code = run_bootstrap()
            if code != 0:
                print(f"Bootstrap exited with code {code}", file=sys.stderr)
                return code

    print("\nSetup complete.")
    print("Next useful commands:")
    print(f"  python3 {skill_dir() / 'scripts' / 'check_inbox.py'} --agent main --limit 10")
    print(f"  python3 {skill_dir() / 'scripts' / 'send_email.py'} --agent main --to someone@example.com --subject 'Hello' --text 'Test message'")
    print(f"  python3 {skill_dir() / 'scripts' / 'setup_webhook.py'} --list")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
