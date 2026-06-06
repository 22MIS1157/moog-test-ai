"""
MoogTestAI — Interactive CLI Interface

A terminal-based interface for interacting with all MoogTestAI agents.
Provides a menu-driven experience with rich formatting for demo and
daily usage.

Usage:
    python -m src.cli
"""

import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

console = Console()

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███╗   ███╗ ██████╗  ██████╗  ██████╗                     ║
║   ████╗ ████║██╔═══██╗██╔═══██╗██╔════╝                     ║
║   ██╔████╔██║██║   ██║██║   ██║██║  ███╗                    ║
║   ██║╚██╔╝██║██║   ██║██║   ██║██║   ██║                    ║
║   ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝╚██████╔╝                   ║
║   ╚═╝     ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝                    ║
║                                                              ║
║   AI-Powered Hardware Test & Debug Assistant                 ║
║   Moog India Technology Center                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def _handle_llm_error(e: Exception, operation: str) -> None:
    """Display a clean, user-friendly error message for LLM failures."""
    err_msg = str(e)

    if "temporarily unavailable" in err_msg.lower() or "high demand" in err_msg.lower():
        console.print(
            f"\n[bold yellow]⚠ The AI model is currently busy. "
            f"Please retry {operation} in a moment.[/]\n"
        )
    elif "api key" in err_msg.lower() or "authentication" in err_msg.lower():
        console.print(
            f"\n[bold red]✗ API key not configured. "
            f"Please set GOOGLE_API_KEY in your .env file.[/]\n"
        )
    else:
        console.print(
            f"\n[bold yellow]⚠ Could not complete {operation} at this time. "
            f"Please check your network connection and try again.[/]\n"
        )


def show_menu():
    """Display the main menu."""
    table = Table(title="Main Menu", show_header=False, border_style="cyan")
    table.add_column("Option", style="bold cyan", width=6)
    table.add_column("Description", style="white")

    table.add_row("1", "Ingest Design Documents (RAG Pipeline)")
    table.add_row("2", "Generate Test Plan (Deliverable 2)")
    table.add_row("3", "Analyze Critical Signals & Failure Points (Deliverable 3)")
    table.add_row("4", "Debug Test Results — Automatic Analysis (Deliverable 4)")
    table.add_row("5", "Debug Test Results — Interactive Mode (Deliverable 4)")
    table.add_row("6", "List Available Test Files")
    table.add_row("0", "Exit")

    console.print(table)


def cmd_ingest():
    """Run the document ingestion pipeline."""
    console.print("\n[bold cyan]Starting RAG Ingestion Pipeline...[/]")
    from src.rag.ingest import ingest_documents
    ingest_documents()
    console.print("[bold green]Ingestion complete.[/]\n")


def cmd_generate_test_plan():
    """Generate a test plan for the pilot design."""
    console.print("\n[bold cyan]Generating AI-Powered Test Plan...[/]")
    console.print("[dim]Retrieving design context from ChromaDB...[/]")

    from src.agents.test_plan_agent import generate_test_plan

    design_name = Prompt.ask(
        "Design name",
        default="MOOG-SA-4200 Servo Amplifier Control Card",
    )
    focus = Prompt.ask(
        "Focus areas",
        default="All categories (Functional, Boundary, Communication, Environmental, Protection)",
    )

    try:
        with console.status("[bold cyan]Generating test plan via LLM..."):
            result = generate_test_plan(design_name=design_name, focus_areas=focus)
        console.print(Panel(Markdown(result), title="Generated Test Plan", border_style="green"))
    except Exception as e:
        _handle_llm_error(e, "test plan generation")


def cmd_analyze_signals():
    """Analyze critical signals and failure points."""
    console.print("\n[bold cyan]Analyzing Critical Signals & Failure Points...[/]")

    from src.agents.signal_analyzer_agent import analyze_signals_and_failures

    design_name = Prompt.ask(
        "Design name",
        default="MOOG-SA-4200 Servo Amplifier Control Card",
    )

    try:
        with console.status("[bold cyan]Running FMEA analysis via LLM..."):
            result = analyze_signals_and_failures(design_name=design_name)
        console.print(Panel(Markdown(result), title="Signal & Failure Analysis", border_style="yellow"))
    except Exception as e:
        _handle_llm_error(e, "signal analysis")


def cmd_debug_automatic():
    """Automatically analyze a test results file."""
    from src.agents.debug_agent import list_available_test_files, analyze_test_results

    files = list_available_test_files()
    if not files:
        console.print("[red]No test files found in data/test_results/[/]")
        return

    console.print("\n[bold cyan]Available Test Files:[/]")
    for i, f in enumerate(files, 1):
        console.print(f"  {i}. {f}")

    choice = IntPrompt.ask("Select file number", default=1)
    if 1 <= choice <= len(files):
        filename = files[choice - 1]
        console.print(f"\n[bold cyan]Analyzing: {filename}[/]")

        try:
            with console.status("[bold cyan]Interpreting test results via LLM..."):
                result = analyze_test_results(filename)
            console.print(Panel(Markdown(result), title=f"Debug Report: {filename}", border_style="red"))
        except Exception as e:
            _handle_llm_error(e, "test result analysis")
    else:
        console.print("[red]Invalid selection.[/]")


def cmd_debug_interactive():
    """Interactive collaborative debugging session."""
    from src.agents.debug_agent import interactive_debug

    console.print("\n[bold cyan]Interactive Debugging Mode[/]")
    console.print("[dim]Describe the symptoms you are observing. Type 'exit' to quit.[/]\n")

    while True:
        symptom = Prompt.ask("[bold]Symptom")
        if symptom.lower() in ("exit", "quit", "q"):
            break

        try:
            with console.status("[bold cyan]Analyzing symptom..."):
                result = interactive_debug(symptom)
            console.print(Panel(Markdown(result), title="Debug Guidance", border_style="magenta"))
            console.print()
        except Exception as e:
            _handle_llm_error(e, "symptom analysis")


def cmd_list_files():
    """List available test result files."""
    from src.agents.debug_agent import list_available_test_files

    files = list_available_test_files()
    if files:
        console.print("\n[bold cyan]Available Test Result Files:[/]")
        for f in files:
            console.print(f"  - {f}")
    else:
        console.print("[yellow]No test files found.[/]")
    console.print()


def main():
    """Main CLI entry point."""
    console.print(BANNER, style="bold cyan")

    while True:
        show_menu()
        choice = Prompt.ask("\nSelect option", default="0")

        if choice == "1":
            cmd_ingest()
        elif choice == "2":
            cmd_generate_test_plan()
        elif choice == "3":
            cmd_analyze_signals()
        elif choice == "4":
            cmd_debug_automatic()
        elif choice == "5":
            cmd_debug_interactive()
        elif choice == "6":
            cmd_list_files()
        elif choice == "0":
            console.print("[bold cyan]Goodbye![/]")
            sys.exit(0)
        else:
            console.print("[red]Invalid option. Try again.[/]")


if __name__ == "__main__":
    main()
