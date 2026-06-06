"""
MoogTestAI — Debug Agent (Deliverable 4)

Uses Generative AI to interpret test results, identify issues, and support
collaborative debugging. Operates in two modes:

  1. Automatic Analysis: Accepts a test result file path, parses it, and
     produces a structured debug report with root cause hypotheses and
     recommended troubleshooting steps.

  2. Interactive Debugging: Accepts a natural language symptom description
     and engages in collaborative Q&A to narrow down the root cause.
"""

import os
from pathlib import Path

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from src.config import get_llm, TEST_RESULTS_DIR
from src.rag.retriever import retrieve_context


ANALYSIS_SYSTEM_PROMPT = """You are a senior hardware debug engineer at Moog Inc. with 15 years of
experience debugging servo amplifier control cards and power electronics boards.

You are given test results from a card-level or box-level test run, along with the original
design specifications retrieved from the knowledge base.

DESIGN SPECIFICATIONS:
{context}

TEST RESULTS:
{test_data}

ANALYSIS REQUIREMENTS:

1. SUMMARY: Provide a one-paragraph executive summary of the test run.

2. PASS/FAIL BREAKDOWN: List each test with its result, highlighting failures.

3. FAILURE ANALYSIS: For each FAIL result:
   a. What was measured vs. what was expected (with specific values)
   b. Root Cause Hypothesis — explain the most likely physical/electrical cause
   c. Correlated Failures — identify if multiple failures share a common root cause
   d. Supporting Evidence — reference specific datasheet specs or schematic details

4. DEBUGGING PROCEDURE: For each failure cluster, provide an ordered troubleshooting procedure:
   - Step number
   - Action (what to measure/inspect)
   - Equipment needed (oscilloscope, multimeter, thermal camera, etc.)
   - Expected observation if hypothesis is correct
   - Next step based on observation

5. RECOMMENDATIONS: Suggest design or process changes to prevent recurrence.

Format everything as structured Markdown with clear headings."""


INTERACTIVE_SYSTEM_PROMPT = """You are a senior hardware debug engineer at Moog Inc. An engineer
on the factory floor is describing symptoms they observe during testing of a servo amplifier
control card (MOOG-SA-4200).

Use the design documentation below to help them diagnose the issue through collaborative
troubleshooting. Ask clarifying questions when needed. Suggest specific measurements,
test points, and likely root causes based on the symptoms described.

DESIGN SPECIFICATIONS:
{context}

Be concise, practical, and reference specific pin numbers, voltage thresholds, and component
designators from the design documentation when providing guidance."""


def _load_test_file(filename: str) -> str:
    """Load a test result file and convert it to a readable string."""
    filepath = Path(TEST_RESULTS_DIR) / filename

    if not filepath.exists():
        # Try looking in the absolute path directly
        filepath = Path(filename)

    if not filepath.exists():
        return f"Error: Test file not found at {filepath}"

    if filepath.suffix == ".csv":
        df = pd.read_csv(filepath)
        lines = [f"Test Results: {filepath.name}", ""]

        # Add summary statistics
        if "Result" in df.columns:
            total = len(df)
            passed = len(df[df["Result"] == "PASS"])
            failed = len(df[df["Result"] == "FAIL"])
            lines.append(f"Total Tests: {total} | Passed: {passed} | Failed: {failed}")
            lines.append("")

        # Full data
        lines.append(df.to_string(index=False))
        return "\n".join(lines)

    elif filepath.suffix == ".log":
        return filepath.read_text(encoding="utf-8")

    else:
        return filepath.read_text(encoding="utf-8")


def analyze_test_results(filename: str) -> str:
    """
    Automatically analyze a test results file and produce a structured
    debug report with root cause hypotheses and troubleshooting steps.

    Args:
        filename: Name of the test file in data/test_results/ directory,
                  or an absolute path to the file.

    Returns:
        A Markdown-formatted debug report.
    """
    test_data = _load_test_file(filename)

    if test_data.startswith("Error:"):
        return test_data

    # Retrieve relevant design specs for cross-referencing
    context = retrieve_context(
        "voltage current limits protection features thermal shutdown "
        "specifications pin configuration electrical specifications "
        "EMC compliance environmental testing"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYSIS_SYSTEM_PROMPT),
        ("human", "Analyze these test results and provide a complete debug report."),
    ])

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "test_data": test_data,
    })

    return response.content


def interactive_debug(symptom: str) -> str:
    """
    Engage in collaborative debugging based on a symptom description.

    Args:
        symptom: Natural language description of the observed issue
                 (e.g., "Phase A is drawing 10A and the board is overheating").

    Returns:
        AI-generated debugging guidance.
    """
    context = retrieve_context(
        f"specifications protection features current limits thermal "
        f"pin configuration schematic {symptom}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", INTERACTIVE_SYSTEM_PROMPT),
        ("human", "{symptom}"),
    ])

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "symptom": symptom,
    })

    return response.content


def list_available_test_files() -> list[str]:
    """List all test result files available for analysis."""
    if not os.path.exists(TEST_RESULTS_DIR):
        return []
    files = []
    for path in Path(TEST_RESULTS_DIR).iterdir():
        if path.suffix in (".csv", ".log", ".txt"):
            files.append(path.name)
    return sorted(files)


if __name__ == "__main__":
    print("Available test files:", list_available_test_files())
    print("\nAnalyzing overcurrent failure scenario...")
    report = analyze_test_results("card_test_fail_overcurrent.csv")
    print(report)
