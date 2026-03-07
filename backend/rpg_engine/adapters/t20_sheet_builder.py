from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


def _node_binary() -> str:
    return os.getenv("NODE_BIN", "node").strip() or "node"


def _bridge_path() -> Path:
    return Path(__file__).resolve().parent / "t20_sheet_builder_bridge.cjs"


def run_t20_sheet_builder(payload: JsonObject) -> tuple[JsonObject | None, str | None]:
    bridge_path = _bridge_path()
    if not bridge_path.exists():
        return None, "bridge script not found"

    try:
        completed = subprocess.run(
            [_node_binary(), str(bridge_path)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=str(Path(__file__).resolve().parents[2]),
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return None, str(error)

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return None, stderr or stdout or f"node exited with code {completed.returncode}"
    if not stdout:
        return None, "empty bridge response"
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as error:
        return None, f"invalid bridge json: {error}"
    if not isinstance(parsed, dict):
        return None, "bridge response must be an object"
    if not parsed.get("success"):
        return None, str(parsed.get("error", "unknown bridge error"))
    data = parsed.get("data")
    if not isinstance(data, dict):
        return None, "bridge response missing data"
    return data, None
