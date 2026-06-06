"""
MoogTestAI — Test Plan Generator Agent (Deliverable 2)

Uses RAG-retrieved design context to generate comprehensive, structured
test plans and procedures for the pilot hardware design.

The agent produces test plans covering:
  - Functional tests (PWM, current output, feedback loops)
  - Boundary tests (over-voltage, under-voltage, thermal limits)
  - Communication tests (SPI register access, EtherCAT integrity)
  - Environmental tests (EMC, vibration, thermal cycling)
"""

from langchain_core.prompts import ChatPromptTemplate

from src.config import get_llm
from src.rag.retriever import retrieve_context

SYSTEM_PROMPT = """You are a senior hardware test engineer at Moog Inc., specializing in card-level
and box-level testing for motion control systems. You have deep expertise in servo amplifiers,
power electronics, and aerospace-grade testing standards.

Given the design documentation below, generate a comprehensive test plan for the hardware design.

DESIGN CONTEXT:
{context}

REQUIREMENTS:
1. Organize tests into categories: Functional, Boundary, Communication, Environmental, Protection.
2. For each test, provide:
   - Test ID (e.g., FT-001, BT-001)
   - Test Name
   - Objective (what you are verifying)
   - Prerequisites (equipment, setup conditions)
   - Procedure (step-by-step instructions)
   - Expected Result (pass criteria with specific values from the datasheet)
   - Severity (Critical / Major / Minor)
3. Reference specific pin numbers, voltage thresholds, and current limits from the datasheet.
4. Include at least 3 tests per category.
5. Format the output as structured Markdown.

Generate the test plan now."""

USER_PROMPT = """Generate a complete card-level test plan for the following design: {design_name}

Focus areas: {focus_areas}"""


def generate_test_plan(
    design_name: str = "MOOG-SA-4200 Servo Amplifier Control Card",
    focus_areas: str = "All categories (Functional, Boundary, Communication, Environmental, Protection)",
) -> str:
    """
    Generate an AI-powered test plan using RAG-retrieved design context.

    Args:
        design_name: Name of the hardware design to generate tests for.
        focus_areas: Specific test categories to focus on.

    Returns:
        A Markdown-formatted test plan string.
    """
    # Retrieve relevant design documentation
    context = retrieve_context(
        f"specifications pinout voltage current limits protection features "
        f"communication interfaces for {design_name}"
    )

    # Build the prompt chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "design_name": design_name,
        "focus_areas": focus_areas,
    })

    return response.content


if __name__ == "__main__":
    print("Generating test plan for MOOG-SA-4200...")
    plan = generate_test_plan()
    print(plan)
