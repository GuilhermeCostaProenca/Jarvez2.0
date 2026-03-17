from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ALIAS = "jarvez_backend_mcp"


def _load_internal_package():
    if _ALIAS in sys.modules:
        return sys.modules[_ALIAS]

    init_path = Path(__file__).with_name("mcp") / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _ALIAS,
        init_path,
        submodule_search_locations=[str(init_path.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load internal backend/mcp package.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[_ALIAS] = module
    spec.loader.exec_module(module)
    return module


_pkg = _load_internal_package()

McpClientError = _pkg.McpClientError
McpManager = _pkg.McpManager
McpRegistry = _pkg.McpRegistry
McpServerConfig = _pkg.McpServerConfig
McpToolCallResult = _pkg.McpToolCallResult
McpToolInfo = _pkg.McpToolInfo
create_default_mcp_registry = _pkg.create_default_mcp_registry
get_default_mcp_manager = _pkg.get_default_mcp_manager

__all__ = [
    "McpClientError",
    "McpManager",
    "McpRegistry",
    "McpServerConfig",
    "McpToolCallResult",
    "McpToolInfo",
    "create_default_mcp_registry",
    "get_default_mcp_manager",
]
