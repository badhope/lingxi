"""Interactive CLI for the two CrewAI flows (analysis, knowledge query)."""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from config import settings
from agents.base_agent import get_llm
from crews.data_analysis import run_data_analysis
from crews.knowledge_team import run_knowledge_query

console = Console()


def print_banner():
    """Print the welcome banner."""
    banner = Panel(
        f"[bold blue]data-agent {settings.app_version}[/bold blue]\n"
        "FastAPI + CrewAI multi-agent data assistant",
        border_style="blue"
    )
    console.print(banner)


def analyze_data():
    """Run data-analysis flow on a user query."""
    console.print("\n[cyan]Data analysis[/cyan]")
    query = Prompt.ask("Query")

    if not query:
        console.print("[yellow]Query cannot be empty[/yellow]")
        return

    console.print("\n[yellow]Running...[/yellow]\n")

    try:
        result = run_data_analysis(query)
        console.print(Panel(
            result,
            title="[bold green]Result[/bold green]",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]Failed: {str(e)}[/red]")


def query_knowledge():
    """Run knowledge-base flow on a user question."""
    console.print("\n[cyan]Knowledge query[/cyan]")
    question = Prompt.ask("Question")

    if not question:
        console.print("[yellow]Question cannot be empty[/yellow]")
        return

    console.print("\n[yellow]Running...[/yellow]\n")

    try:
        result = run_knowledge_query(question)
        console.print(Panel(
            result,
            title="[bold green]Result[/bold green]",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]Failed: {str(e)}[/red]")


def show_menu():
    """Print the main menu."""
    console.print("\n[bold]Pick an option:[/bold]")
    console.print("  [1] Data analysis")
    console.print("  [2] Knowledge query")
    console.print("  [q] Quit")


def main():
    """CLI loop."""
    print_banner()

    while True:
        show_menu()
        choice = Prompt.ask("\n[bold cyan]Choice[/bold cyan]",
                           choices=["1", "2", "q"],
                           default="q")

        if choice == "1":
            analyze_data()
        elif choice == "2":
            query_knowledge()
        elif choice == "q":
            console.print("\n[yellow]Bye.[/yellow]")
            break

        if not Confirm.ask("\n[bold]Continue?[/bold]"):
            console.print("\n[yellow]Bye.[/yellow]")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        sys.exit(0)
