from __future__ import annotations

import importlib
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _without_backend_path() -> tuple[list[str], list[str]]:
    original = list(sys.path)
    filtered: list[str] = []
    for entry in original:
        try:
            if Path(entry).resolve() == _BACKEND_ROOT:
                continue
        except Exception:
            pass
        filtered.append(entry)
    sys.path[:] = filtered
    return original, filtered


def _restore_sys_path(original: list[str]) -> None:
    sys.path[:] = original


def _import_vendor_module(module_name: str):
    original, _filtered = _without_backend_path()
    try:
        return importlib.import_module(module_name)
    finally:
        _restore_sys_path(original)


ClientSession = _import_vendor_module("mcp.client.session").ClientSession
StdioServerParameters = _import_vendor_module("mcp.client.stdio").StdioServerParameters
stdio_client = _import_vendor_module("mcp.client.stdio").stdio_client
