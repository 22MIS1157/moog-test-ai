"""
Tests for the RAG ingestion and retrieval pipeline.
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestDocumentLoading:
    """Test that all document types can be loaded and parsed."""

    def test_pilot_design_directory_exists(self):
        """Verify the pilot design data directory exists."""
        from src.config import PILOT_DESIGN_DIR
        assert os.path.exists(PILOT_DESIGN_DIR), f"Directory not found: {PILOT_DESIGN_DIR}"

    def test_test_results_directory_exists(self):
        """Verify the test results data directory exists."""
        from src.config import TEST_RESULTS_DIR
        assert os.path.exists(TEST_RESULTS_DIR), f"Directory not found: {TEST_RESULTS_DIR}"

    def test_datasheet_file_exists(self):
        """Verify the servo amplifier datasheet exists."""
        from src.config import PILOT_DESIGN_DIR
        datasheet = Path(PILOT_DESIGN_DIR) / "servo_amplifier_datasheet.md"
        assert datasheet.exists(), "Datasheet file not found"

    def test_schematic_file_exists(self):
        """Verify the schematic JSON exists."""
        from src.config import PILOT_DESIGN_DIR
        schematic = Path(PILOT_DESIGN_DIR) / "power_supply_schematic.json"
        assert schematic.exists(), "Schematic file not found"

    def test_bom_file_exists(self):
        """Verify the BOM CSV exists."""
        from src.config import PILOT_DESIGN_DIR
        bom = Path(PILOT_DESIGN_DIR) / "bom.csv"
        assert bom.exists(), "BOM file not found"

    def test_load_markdown_files(self):
        """Test that markdown files can be loaded as LangChain documents."""
        from src.rag.ingest import _load_markdown_files
        from src.config import PILOT_DESIGN_DIR

        docs = _load_markdown_files(PILOT_DESIGN_DIR)
        assert len(docs) > 0, "No markdown documents loaded"
        assert docs[0].page_content, "Document has no content"
        assert docs[0].metadata.get("source"), "Document has no source metadata"

    def test_load_json_schematic(self):
        """Test that JSON schematic files can be parsed into documents."""
        from src.rag.ingest import _load_json_schematic
        from src.config import PILOT_DESIGN_DIR

        docs = _load_json_schematic(PILOT_DESIGN_DIR)
        assert len(docs) > 0, "No schematic documents loaded"
        assert "Servo Amplifier" in docs[0].page_content, "Schematic content not parsed correctly"

    def test_load_bom_csv(self):
        """Test that BOM CSV files can be parsed into documents."""
        from src.rag.ingest import _load_bom_csv
        from src.config import PILOT_DESIGN_DIR

        docs = _load_bom_csv(PILOT_DESIGN_DIR)
        assert len(docs) > 0, "No BOM documents loaded"
        assert "STM32F407" in docs[0].page_content, "BOM content not parsed correctly"

    def test_load_test_results(self):
        """Test that test result files can be loaded."""
        from src.rag.ingest import _load_test_results
        from src.config import TEST_RESULTS_DIR

        docs = _load_test_results(TEST_RESULTS_DIR)
        assert len(docs) >= 3, f"Expected at least 3 test files, got {len(docs)}"


class TestDataIntegrity:
    """Test that the sample data files contain valid, consistent content."""

    def test_bom_has_critical_components(self):
        """Verify the BOM contains critical flagged components."""
        import pandas as pd
        from src.config import PILOT_DESIGN_DIR

        bom = pd.read_csv(Path(PILOT_DESIGN_DIR) / "bom.csv")
        critical = bom[bom["Critical"] == "Yes"]
        assert len(critical) > 5, "BOM should have multiple critical components"

    def test_schematic_has_all_blocks(self):
        """Verify the schematic JSON contains all expected functional blocks."""
        import json
        from src.config import PILOT_DESIGN_DIR

        with open(Path(PILOT_DESIGN_DIR) / "power_supply_schematic.json") as f:
            data = json.load(f)

        block_ids = [b["id"] for b in data["blocks"]]
        expected = ["PWR_REG", "MCU", "GATE_DRV", "H_BRIDGE", "ISENSE", "THERMAL", "ECAT"]
        for eid in expected:
            assert eid in block_ids, f"Missing block: {eid}"

    def test_fail_test_results_contain_failures(self):
        """Verify the failure test CSV contains FAIL results."""
        import pandas as pd
        from src.config import TEST_RESULTS_DIR

        df = pd.read_csv(Path(TEST_RESULTS_DIR) / "card_test_fail_overcurrent.csv")
        fails = df[df["Result"] == "FAIL"]
        assert len(fails) >= 4, "Failure test file should have multiple FAIL entries"

    def test_pass_test_results_all_pass(self):
        """Verify the passing test CSV contains only PASS results."""
        import pandas as pd
        from src.config import TEST_RESULTS_DIR

        df = pd.read_csv(Path(TEST_RESULTS_DIR) / "card_test_pass.csv")
        fails = df[df["Result"] == "FAIL"]
        assert len(fails) == 0, "Pass test file should have no FAIL entries"
