"""
Tests for the AI agents (test plan, signal analyzer, debug agent).

Note: Tests that require LLM API calls are marked with @pytest.mark.skipif
to allow running the test suite without API keys configured.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HAS_API_KEY = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY"))


class TestDebugAgentOffline:
    """Tests for debug agent functionality that don't require LLM calls."""

    def test_list_test_files(self):
        """Verify list_available_test_files returns expected files."""
        from src.agents.debug_agent import list_available_test_files

        files = list_available_test_files()
        assert len(files) >= 3, f"Expected at least 3 test files, got {len(files)}"
        assert "card_test_pass.csv" in files
        assert "card_test_fail_overcurrent.csv" in files
        assert "box_test_emi_failure.log" in files

    def test_load_csv_test_file(self):
        """Verify CSV test files are loaded and parsed correctly."""
        from src.agents.debug_agent import _load_test_file

        result = _load_test_file("card_test_pass.csv")
        assert "PASS" in result
        assert "CT-001" in result

    def test_load_log_test_file(self):
        """Verify log test files are loaded correctly."""
        from src.agents.debug_agent import _load_test_file

        result = _load_test_file("box_test_emi_failure.log")
        assert "EMC" in result or "EMI" in result or "CE102" in result

    def test_load_nonexistent_file(self):
        """Verify error handling for missing files."""
        from src.agents.debug_agent import _load_test_file

        result = _load_test_file("nonexistent_file.csv")
        assert "Error" in result


class TestAgentImports:
    """Verify all agent modules can be imported without errors."""

    def test_import_test_plan_agent(self):
        from src.agents.test_plan_agent import generate_test_plan
        assert callable(generate_test_plan)

    def test_import_signal_analyzer_agent(self):
        from src.agents.signal_analyzer_agent import analyze_signals_and_failures
        assert callable(analyze_signals_and_failures)

    def test_import_debug_agent(self):
        from src.agents.debug_agent import analyze_test_results, interactive_debug
        assert callable(analyze_test_results)
        assert callable(interactive_debug)


@pytest.mark.skipif(not HAS_API_KEY, reason="No LLM API key configured")
class TestAgentsWithLLM:
    """Integration tests that require a valid LLM API key."""

    def test_generate_test_plan_runs(self):
        """Verify test plan generation produces non-empty output."""
        from src.agents.test_plan_agent import generate_test_plan
        result = generate_test_plan()
        assert len(result) > 100, "Test plan output is too short"

    def test_analyze_signals_runs(self):
        """Verify signal analysis produces non-empty output."""
        from src.agents.signal_analyzer_agent import analyze_signals_and_failures
        result = analyze_signals_and_failures()
        assert len(result) > 100, "Signal analysis output is too short"

    def test_debug_test_results_runs(self):
        """Verify debug agent produces non-empty analysis."""
        from src.agents.debug_agent import analyze_test_results
        result = analyze_test_results("card_test_fail_overcurrent.csv")
        assert len(result) > 100, "Debug report output is too short"
