"""Output formatter — rich terminal rendering for knowledge entries."""

from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich import box

from ..engine import SearchResult, KnowledgeEntry

console = Console()


def banner():
    """Print the SecPilot banner."""
    title = Text(
        r"""
   _____           _____ _ _       _
  / ____|         |  __ (_) |     | |
 | (___   ___  ___| |__) | | ___ | |_
  \___ \ / _ \/ __|  ___/| |/ _ \| __|
  ____) |  __/ (__| |    | | (_) | |_
 |_____/ \___|\___|_|    |_|\___/ \__|

  AI Security Knowledge Copilot — by XiaoQiWUMI
""",
        style="bold cyan",
    )
    console.print(title)


SEVERITY_STYLES = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "green",
    "info": "dim cyan",
}


def format_entry(entry: KnowledgeEntry) -> Panel:
    """Format a single knowledge entry as a rich Panel."""
    # Title
    title_text = Text(entry.title, style="bold cyan")

    # Severity badge
    sev_style = SEVERITY_STYLES.get(entry.severity, "dim")
    sev_badge = Text(f" [{entry.severity.upper()}]", style=sev_style)

    # Category & tags line
    meta = Text()
    meta.append(f"📂 {entry.category}  ", style="dim")
    if entry.tags:
        meta.append("🏷  " + ", ".join(f"#{t}" for t in entry.tags), style="magenta")

    # References
    refs = ""
    if entry.references:
        refs = "\n\n" + "\n".join(f"🔗 {r}" for r in entry.references)

    body = Text()
    body.append(meta)
    body.append("\n")
    body.append(Text(entry.content))
    if refs:
        body.append(Text(refs, style="dim"))

    return Panel(
        body,
        title=title_text + sev_badge,
        border_style="cyan",
        box=box.ROUNDED,
    )


def format_results(results: List[SearchResult], query: str = "") -> None:
    """Pretty-print search results to terminal."""
    if not results:
        console.print(
            Panel(
                f"No results found for: [yellow]{query}[/yellow]\n\n"
                "Try:\n"
                "  • Different keywords (Chinese or English)\n"
                "  • Browse categories with [cyan]secpilot list[/cyan]\n"
                "  • Check spelling",
                title="🔍 No Results",
                border_style="yellow",
            )
        )
        return

    console.print(f"\n[dim]Found {len(results)} result(s)[/dim]\n")

    for i, result in enumerate(results, 1):
        score_color = (
            "green" if result.score >= 80 else "yellow" if result.score >= 50 else "dim"
        )
        score_text = Text(
            f"#{i}  score: {result.score:.0f}  ({result.strategy})", style=score_color
        )
        console.print(score_text)
        console.print(format_entry(result.entry))
        console.print()


def format_category_list(categories: List[str], stats: dict) -> None:
    """Print category listing."""
    table = Table(title="📚 Knowledge Base Categories", box=box.ROUNDED)
    table.add_column("Category", style="cyan")
    table.add_column("Entries", justify="right", style="green")

    from ..knowledge.loader import KnowledgeBase

    for cat in categories:
        # count would need kb reference; just show category name
        table.add_row(cat, "")

    table.add_row("", "")
    table.add_row("Total Entries", str(stats.get("total_entries", 0)))
    table.add_row("Total Categories", str(stats.get("total_categories", 0)))
    table.add_row("Indexed Tags", str(stats.get("total_tags", 0)))

    console.print(table)
