"""CLI entry point for Reddit Analyzer."""

import os
import sys
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.database import get_db_manager
from src.database.repositories import (
    CommunityRepository,
    AnalysisRepository,
)
from src.workflow import run_analysis
from src.state import WorkflowStatus

console = Console()


@click.group()
@click.version_option(version="2.0.0", prog_name="reddit-analyzer")
def cli():
    """Reddit Community Analyzer - Production-grade Reddit analysis toolkit.

    Analyze Reddit communities with LangGraph workflows and Claude AI.
    """
    pass


@cli.command()
@click.argument("communities", nargs=-1, required=True)
@click.option(
    "--posts-limit",
    default=100,
    help="Maximum number of posts to collect per community.",
)
@click.option(
    "--comments-limit",
    default=50,
    help="Maximum comments to fetch per top post.",
)
@click.option(
    "--skip-ai",
    is_flag=True,
    help="Skip AI analysis (only collect and extract patterns).",
)
@click.option(
    "--output",
    "-o",
    default="./output",
    help="Output directory for reports.",
)
def analyze(
    communities: tuple[str, ...],
    posts_limit: int,
    comments_limit: int,
    skip_ai: bool,
    output: str,
):
    """Analyze one or more Reddit communities.

    Examples:
        reddit-analyzer analyze PromptEngineering
        reddit-analyzer analyze PromptEngineering Entrepreneur --posts-limit 50
        reddit-analyzer analyze micro_saas --skip-ai
    """
    # Check database connection
    db = get_db_manager()
    if not db.check_connection():
        console.print(
            "[red]Error:[/red] Cannot connect to database. "
            "Make sure PostgreSQL is running (docker-compose up -d)."
        )
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]Reddit Community Analyzer v2[/bold]\n"
            f"Communities: {', '.join(communities)}\n"
            f"Posts limit: {posts_limit} | Comments limit: {comments_limit}\n"
            f"AI Analysis: {'Disabled' if skip_ai else 'Enabled'}",
            title="Configuration",
        )
    )

    for community in communities:
        console.print(f"\n[bold cyan]Analyzing r/{community}...[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running analysis...", total=None)

            try:
                result = run_analysis(
                    community_name=community,
                    skip_ai=skip_ai,
                    output_dir=output,
                    posts_limit=posts_limit,
                    comments_limit=comments_limit,
                )

                progress.update(task, description="Analysis complete!")

                # Display results
                if result.get("status") == WorkflowStatus.COMPLETED:
                    _display_results(result, community)
                else:
                    console.print(f"[red]Analysis failed:[/red] {result.get('error', 'Unknown error')}")
                    if result.get("errors"):
                        for error in result["errors"]:
                            console.print(f"  - {error}")

            except Exception as e:
                console.print(f"[red]Error analyzing {community}:[/red] {str(e)}")


def _display_results(result: dict, community: str):
    """Display analysis results."""
    console.print(f"\n[green]✓ Analysis complete for r/{community}[/green]")

    # Summary table
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Posts Collected", str(result.get("posts_collected", 0)))
    table.add_row("Comments Collected", str(result.get("comments_collected", 0)))

    extraction = result.get("extraction_results", {})
    if extraction.get("score_distribution"):
        score_dist = extraction["score_distribution"]
        table.add_row("Avg Post Score", str(score_dist.get("avg", "N/A")))
        table.add_row("Max Post Score", str(score_dist.get("max", "N/A")))

    ai_analysis = result.get("ai_analysis", {})
    if ai_analysis.get("sentiment_analysis"):
        sentiment = ai_analysis["sentiment_analysis"].get("overall_sentiment", "N/A")
        table.add_row("Overall Sentiment", sentiment)

    synthesis = result.get("synthesis", {})
    table.add_row("Personas Generated", str(len(synthesis.get("personas", []))))
    table.add_row("Insights Generated", str(len(synthesis.get("insights", []))))

    console.print(table)

    # Report path
    if result.get("report_path"):
        console.print(f"\n[bold]Report saved to:[/bold] {result['report_path']}")


@cli.command("list")
def list_communities():
    """List all tracked communities."""
    db = get_db_manager()

    if not db.check_connection():
        console.print("[red]Error:[/red] Cannot connect to database.")
        sys.exit(1)

    with db.session() as session:
        repo = CommunityRepository(session)
        communities = repo.list_all()

        if not communities:
            console.print("No communities tracked yet. Run 'analyze' to add one.")
            return

        table = Table(title="Tracked Communities")
        table.add_column("Name", style="cyan")
        table.add_column("Subscribers", style="white")
        table.add_column("Collection Runs", style="white")
        table.add_column("Last Updated", style="white")

        for community in communities:
            runs = repo.list_collection_runs(community.id, limit=1)
            last_run = runs[0] if runs else None

            table.add_row(
                f"r/{community.name}",
                f"{community.subscribers:,}" if community.subscribers else "N/A",
                str(len(repo.list_collection_runs(community.id))),
                last_run.started_at.strftime("%Y-%m-%d %H:%M") if last_run else "Never",
            )

        console.print(table)


@cli.command()
@click.argument("community")
@click.option("--limit", default=10, help="Number of runs to show.")
def history(community: str, limit: int):
    """Show analysis history for a community."""
    db = get_db_manager()

    if not db.check_connection():
        console.print("[red]Error:[/red] Cannot connect to database.")
        sys.exit(1)

    with db.session() as session:
        repo = CommunityRepository(session)
        comm = repo.get_by_name(community)

        if not comm:
            console.print(f"[red]Community r/{community} not found.[/red]")
            return

        runs = repo.list_collection_runs(comm.id, limit=limit)

        if not runs:
            console.print(f"No collection runs found for r/{community}.")
            return

        table = Table(title=f"Collection History for r/{community}")
        table.add_column("Run ID", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Started", style="white")
        table.add_column("Posts", style="white")
        table.add_column("Comments", style="white")

        for run in runs:
            status_style = (
                "green" if run.status == "completed"
                else "red" if run.status == "failed"
                else "yellow"
            )
            table.add_row(
                str(run.id),
                f"[{status_style}]{run.status}[/{status_style}]",
                run.started_at.strftime("%Y-%m-%d %H:%M"),
                str(run.posts_collected),
                str(run.comments_collected),
            )

        console.print(table)


@cli.command()
@click.option("--run-id", required=True, type=int, help="Collection run ID to reanalyze.")
@click.option("--skip-ai", is_flag=True, help="Skip AI analysis.")
@click.option("--output", "-o", default="./output", help="Output directory.")
def reanalyze(run_id: int, skip_ai: bool, output: str):
    """Re-run AI analysis on existing data."""
    db = get_db_manager()
    if not db.check_connection():
        console.print("[red]Error:[/red] Cannot connect to database.")
        sys.exit(1)

    # Get community name from run
    with db.session() as session:
        repo = CommunityRepository(session)
        run = repo.get_collection_run(run_id)

        if not run:
            console.print(f"[red]Collection run {run_id} not found.[/red]")
            sys.exit(1)

        community_name = run.community.name

    console.print(f"[cyan]Reanalyzing run {run_id} for r/{community_name}...[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running analysis...", total=None)

        try:
            result = run_analysis(
                community_name=community_name,
                skip_ai=skip_ai,
                skip_collection=True,
                existing_run_id=run_id,
                output_dir=output,
            )

            progress.update(task, description="Analysis complete!")

            if result.get("status") == WorkflowStatus.COMPLETED:
                _display_results(result, community_name)
            else:
                console.print(f"[red]Analysis failed:[/red] {result.get('error')}")

        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")


@cli.command()
@click.option("--run-id", required=True, type=int, help="Collection run ID.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Export format.",
)
@click.option("--output", "-o", default=None, help="Output file path.")
def export(run_id: int, output_format: str, output: Optional[str]):
    """Export a report from a collection run."""
    db = get_db_manager()

    if not db.check_connection():
        console.print("[red]Error:[/red] Cannot connect to database.")
        sys.exit(1)

    with db.session() as session:
        analysis_repo = AnalysisRepository(session)
        reports = analysis_repo.list_reports(run_id)

        if not reports:
            console.print(f"[red]No reports found for run {run_id}.[/red]")
            return

        report = reports[0]  # Get most recent

        if output_format == "markdown":
            content = report.content
            ext = ".md"
        else:
            import json
            content = json.dumps(report.report_metadata, indent=2)
            ext = ".json"

        if output:
            filepath = output
        else:
            filepath = f"report_{run_id}{ext}"

        with open(filepath, "w") as f:
            f.write(content)

        console.print(f"[green]Report exported to {filepath}[/green]")


@cli.group()
def db():
    """Database management commands."""
    pass


@db.command("init")
def db_init():
    """Initialize database tables."""
    from src.database.models import Base

    db_manager = get_db_manager()

    console.print("Creating database tables...")
    db_manager.create_tables()
    console.print("[green]Database tables created successfully.[/green]")


@db.command("status")
def db_status():
    """Check database connection status."""
    db_manager = get_db_manager()
    info = db_manager.get_connection_info()

    table = Table(title="Database Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Host", info["host"])
    table.add_row("Port", str(info["port"]))
    table.add_row("Database", info["database"])
    table.add_row("User", info["user"])

    status = "[green]Connected[/green]" if info["connected"] else "[red]Disconnected[/red]"
    table.add_row("Status", status)

    if info.get("version"):
        table.add_row("Version", info["version"][:50])

    console.print(table)


@db.command("migrate")
def db_migrate():
    """Run database migrations (placeholder for Alembic)."""
    console.print(
        "[yellow]Note:[/yellow] For production migrations, use Alembic directly:\n"
        "  alembic upgrade head"
    )


if __name__ == "__main__":
    cli()
