"""
MoogTestAI — Critical Signal & Failure Point Analyzer Agent (Deliverable 3)

Parses schematic data and BOM to identify:
  - Critical signals that require monitoring during testing
  - Key components whose failure would impact system operation
  - Potential failure points ranked by severity

Outputs a structured risk matrix.
"""

from langchain_core.prompts import ChatPromptTemplate

from src.config import get_llm
from src.rag.retriever import retrieve_context

SYSTEM_PROMPT = """You are a reliability engineer at Moog Inc. with expertise in Failure Mode and
Effects Analysis (FMEA) for aerospace-grade power electronics. Your job is to analyze a hardware
design and identify critical signals, key components, and potential failure points.

DESIGN CONTEXT:
{context}

ANALYSIS REQUIREMENTS:

1. CRITICAL SIGNALS: Identify signals that must be monitored during testing.
   For each signal, specify:
   - Signal name and pin number
   - Why it is critical (what breaks if this signal fails)
   - Recommended monitoring method (oscilloscope, multimeter, logic analyzer)
   - Acceptable range from the datasheet

2. KEY COMPONENTS: Identify components whose failure would cause system-level impact.
   For each component, specify:
   - Reference designator and part number
   - Function in the circuit
   - Failure mode (open, short, drift, thermal)
   - Impact of failure (what happens to the system)

3. POTENTIAL FAILURE POINTS: Identify design weaknesses and single points of failure.
   For each, specify:
   - Location in the circuit
   - Root cause mechanism (thermal stress, voltage stress, aging, etc.)
   - Severity (Critical / Major / Minor)
   - Likelihood (High / Medium / Low)
   - Risk Priority Number (Severity x Likelihood, scale 1-9)
   - Recommended mitigation

4. Output a final RISK MATRIX table sorted by Risk Priority Number (highest first).

Format everything as structured Markdown."""

USER_PROMPT = """Analyze the following hardware design for critical signals, key components,
and potential failure points: {design_name}"""


def analyze_signals_and_failures(
    design_name: str = "MOOG-SA-4200 Servo Amplifier Control Card",
) -> str:
    """
    Analyze the pilot design for critical signals and failure points.

    Args:
        design_name: Name of the hardware design to analyze.

    Returns:
        A Markdown-formatted analysis with risk matrix.
    """
    context = retrieve_context(
        f"schematic blocks components critical signals net connections "
        f"MOSFET gate driver current sense thermal protection "
        f"BOM critical components for {design_name}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "design_name": design_name,
    })

    return response.content


if __name__ == "__main__":
    print("Analyzing critical signals and failure points...")
    analysis = analyze_signals_and_failures()
    print(analysis)
