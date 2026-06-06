"""
Tests for the MCP Server tool registration.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestMCPServerImports:
    """Verify the MCP server module can be imported."""

    def test_import_server(self):
        from src.mcp_server.server import server
        assert server is not None

    def test_server_name(self):
        from src.mcp_server.server import server
        assert server.name == "moog-test-ai"


class TestMCPToolDefinitions:
    """Verify MCP tools are properly defined."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_five_tools(self):
        from src.mcp_server.server import list_tools
        tools = await list_tools()
        assert len(tools) == 5, f"Expected 5 tools, got {len(tools)}"

    @pytest.mark.asyncio
    async def test_tool_names(self):
        from src.mcp_server.server import list_tools
        tools = await list_tools()
        names = {t.name for t in tools}
        expected = {
            "generate_test_plan",
            "analyze_signals",
            "debug_test_results",
            "interactive_debug",
            "list_test_files",
        }
        assert names == expected, f"Tool names mismatch: {names}"

    @pytest.mark.asyncio
    async def test_all_tools_have_descriptions(self):
        from src.mcp_server.server import list_tools
        tools = await list_tools()
        for tool in tools:
            assert tool.description, f"Tool '{tool.name}' has no description"
            assert len(tool.description) > 20, f"Tool '{tool.name}' description too short"

    @pytest.mark.asyncio
    async def test_all_tools_have_input_schemas(self):
        from src.mcp_server.server import list_tools
        tools = await list_tools()
        for tool in tools:
            assert tool.inputSchema, f"Tool '{tool.name}' has no input schema"
            assert tool.inputSchema.get("type") == "object"
