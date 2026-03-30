#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def config_path() -> Path:
    return skill_dir() / 'config' / 'config.json'


def load_agentmail_api_key() -> str | None:
    env_key = os.getenv('AGENTMAIL_API_KEY')
    if env_key:
        return env_key.strip()

    env_file = skill_dir() / '.env'
    if env_file.exists():
        for raw_line in env_file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key.strip() == 'AGENTMAIL_API_KEY':
                value = value.strip().strip('"').strip("'")
                if value:
                    return value

    return None


def load_local_agentmail_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def resolve_agent_inbox(agent_id: str) -> str | None:
    agent_id = (agent_id or '').strip()
    if not agent_id:
        return None
    inbox_map = load_local_agentmail_config().get('inboxAgentMap') or {}
    for inbox, mapped_agent in inbox_map.items():
        if str(mapped_agent).strip() == agent_id:
            return str(inbox).strip().lower()
    return None


def resolve_inbox_or_agent(inbox: str | None, agent_id: str | None) -> str | None:
    if inbox:
        return inbox.strip().lower()
    if agent_id:
        return resolve_agent_inbox(agent_id)
    return None
