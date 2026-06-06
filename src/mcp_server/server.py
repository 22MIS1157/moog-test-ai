"""
MoogTestAI — MCP Server (Model Context Protocol)

Exposes the AI testing tools as a standardized MCP server using Anthropic's
Model Context Protocol. This allows any MCP-compatible AI host (Claude Desktop,
VS Code, custom frontends) to discover and invoke the tools via JSON-RPC 2.0.

Tools exposed:
  1. generate_test_plan — Generates test procedures from design documents
  2. analyze_signals — Identifies critical signals and failure points
  3. debug_test_results — Analyzes test result files for root causes
  4. interactive_debug — Collaborative debugging from symptom descriptions
  5. list_test_files — Lists available test result files
"""

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our agents
from src.agents.test_plan_agent import generate_test_plan
from src.agents.signal_analyzer_agent import analyze_signals_and_failures
from src.agents.debug_agent import (
    analyze_test_results,
    interactive_debug,
    list_available_test_files,
)

# Create the MCP server instance
server = Server("moog-test-ai")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Expose available tools to MCP clients."""
    return [
        Tool(
            name="generate_test_plan",
            description=(
                "Generate a comprehensive, structured test plan for a hardware design. "
                "Uses RAG to retrieve design specifications and produces categorized test "
                "procedures (Functional, Boundary, Communication, Environmental, Protection) "
                "with specific pass/fail criteria."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "design_name": {
                        "type": "string",
                        "description": "Name of the hardware design (default: MOOG-SA-4200 Servo Amplifier Control Card)",
                        "default": "MOOG-SA-4200 Servo Amplifier Control Card",
                    },
                    "focus_areas": {
                        "type": "string",
                        "description": "Specific test categories to focus on",
                        "default": "All categories",
                    },
                },
            },
        ),
        Tool(
            name="analyze_signals",
            description=(
                "Analyze a hardware design to identify critical signals, key components, "
                "and potential failure points. Produces a prioritized risk matrix with "
                "severity ratings and mitigation recommendations (FMEA-style analysis)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "design_name": {
                        "type": "string",
                        "description": "Name of the hardware design to analyze",
                        "default": "MOOG-SA-4200 Servo Amplifier Control Card",
                    },
                },
            },
        ),
        Tool(
            name="debug_test_results",
            description=(
                "Analyze a test results file (CSV or log) and produce a structured debug "
                "report with pass/fail breakdown, root cause hypotheses, correlated failures, "
                "and step-by-step troubleshooting procedures."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the test file in data/test_results/ directory",
                    },
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="interactive_debug",
            description=(
                "Collaborative debugging assistant. Describe the symptoms you observe "
                "during hardware testing, and the AI will suggest measurements, test points, "
                "and likely root causes based on the design documentation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symptom": {
                        "type": "string",
                        "description": "Natural language description of the observed issue",
                    },
                },
                "required": ["symptom"],
            },
        ),
        Tool(
            name="list_test_files",
            description="List all available test result files that can be analyzed.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocations from MCP clients."""

    if name == "generate_test_plan":
        design_name = arguments.get("design_name", "MOOG-SA-4200 Servo Amplifier Control Card")
        focus_areas = arguments.get("focus_areas", "All categories")
        result = generate_test_plan(design_name=design_name, focus_areas=focus_areas)

    elif name == "analyze_signals":
        design_name = arguments.get("design_name", "MOOG-SA-4200 Servo Amplifier Control Card")
        result = analyze_signals_and_failures(design_name=design_name)

    elif name == "debug_test_results":
        filename = arguments.get("filename", "")
        if not filename:
            result = "Error: 'filename' parameter is required."
        else:
            result = analyze_test_results(filename=filename)

    elif name == "interactive_debug":
        symptom = arguments.get("symptom", "")
        if not symptom:
            result = "Error: 'symptom' parameter is required."
        else:
            result = interactive_debug(symptom=symptom)

    elif name == "list_test_files":
        files = list_available_test_files()
        result = json.dumps(files, indent=2)

    else:
        result = f"Error: Unknown tool '{name}'"

    return [TextContent(type="text", text=result)]


async def main():
    """Run the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
