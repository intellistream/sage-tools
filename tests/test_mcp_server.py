"""Smoke tests for sage.tools MCP server — verify structure without requiring mcp package."""

import pytest


def test_mcp_server_module_imports_without_mcp_installed(monkeypatch):
    """mcp_server module must import cleanly even when the mcp package is absent."""
    import sys

    # Simulate mcp not installed by making it unimportable
    monkeypatch.setitem(sys.modules, "mcp", None)
    monkeypatch.setitem(sys.modules, "mcp.server", None)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", None)

    # Force reimport
    for mod in list(sys.modules):
        if "sage.tools.mcp_server" in mod:
            del sys.modules[mod]

    # Should not raise at module-import time
    import importlib

    mcp_mod = importlib.import_module("sage.tools.mcp_server")
    assert hasattr(mcp_mod, "main")
    assert hasattr(mcp_mod, "_build_server")


def test_mcp_server_get_mcp_raises_helpful_error_when_mcp_missing():
    """_get_mcp() raises ImportError with install instructions when mcp is absent."""
    try:
        import mcp  # noqa: F401

        pytest.skip("mcp package is installed — skipping 'missing' test")
    except ImportError:
        pass  # mcp not installed — test can proceed

    from sage.tools.mcp_server import _get_mcp

    with pytest.raises(ImportError, match="isage-tools\\[mcp\\]"):
        _get_mcp()


def test_mcp_server_argparse_help():
    """main() --help does not crash."""
    from sage.tools.mcp_server import main

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
