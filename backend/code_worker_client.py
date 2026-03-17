from __future__ import annotations

import os
from typing import Any

import requests


class CodeWorkerClient:
    def __init__(self):
        host = os.getenv("CODE_WORKER_HOST", "127.0.0.1").strip() or "127.0.0.1"
        port = os.getenv("CODE_WORKER_PORT", "8765").strip() or "8765"
        token = os.getenv("CODE_WORKER_TOKEN", "jarvez-local-worker").strip() or "jarvez-local-worker"
        self.base_url = f"http://{host}:{port}"
        self.headers = {"X-Code-Worker-Token": token}

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.request(
            method=method.upper(),
            url=f"{self.base_url}{path}",
            headers=self.headers,
            json=payload,
            timeout=20,
        )
        parsed = response.json() if response.content else {}
        if not isinstance(parsed, dict):
            parsed = {"success": False, "message": "Resposta invalida do worker."}
        if response.status_code >= 400 and "success" not in parsed:
            parsed["success"] = False
            parsed["message"] = f"Code worker retornou HTTP {response.status_code}."
        return parsed

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/health")

    def read_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/read-file", payload)

    def search_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/search-files", payload)

    def git_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/git-status", payload)

    def git_diff(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/git-diff", payload)

    def apply_patch(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/apply-patch", payload)

    def run_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/run-command", payload)
