#!/usr/bin/env python3
"""
CLI for AI-Powered YouTube SEO Assistant

Local-first, no-login CLI tool for automated YouTube content strategy generation.
Chains together keyword analysis, gap detection, and AI-powered optimization.

Usage:
    python cli.py --input=channel.csv --goal="Find gaps and generate 5 high-CTR titles for a female GenZ audience in Bangladesh"
    python cli.py --input=data.csv --audience="tech enthusiasts" --tone="curiosity"
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from app.core.config import settings
from app.services.ai_strategy_runner import AIStrategyRunner
from app.utils.csv_validator import validate_csv_file

# Initialize CLI app and console
app = typer.Typer(
    name="TubeGPT CLI",
    help="🎯 Local-first AI YouTube SEO Assistant - No login, no cloud, no tracking",
    add_completion=False
)
console = Console()


def print_banner():
    """Display the application banner."""
    banner = """
    ╭─────────────────────────────────────────────────────────────╮
    │                     🎯 TubeGPT CLI                          │
    │           Local-First AI YouTube SEO Assistant              │
    │                                                             │
    │  ✅ No Login  ✅ No Cloud  ✅ No Tracking  ✅ Fully Local   │
    ╰─────────────────────────────────────────────────────────────╯
    """
    console.print(banner, style="bold blue")


@app.command()
def analyze(
    input_file: str = typer.Option(
        ...,
        "--input",
        "-i",
        help="Path to CSV file containing YouTube channel data"
    ),
    goal: str = typer.Option(
        "Generate optimized YouTube content strategy",
        "--goal",
        "-g",
        help="Analysis goal and specific requirements"
    ),
    audience: Optional[str] = typer.Option(
        None,
        "--audience",
        "-a",
        help="Target audience (e.g., 'female GenZ in Bangladesh', 'tech enthusiasts')"
    ),
    tone: Optional[str] = typer.Option(
        "engaging",
        "--tone",
        "-t",
        help="Content tone: curiosity, authority, fear, persuasive, engaging"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for strategy files (default: data/storage/strategies)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output for debugging"
    )
):
    """
    🚀 Run full AI-powered YouTube SEO analysis pipeline
    
    Analyzes YouTube data and generates:
    - Keyword analysis with trends
    - Content gap detection
    - AI-optimized titles, descriptions, and tags
    - Psychological metadata optimization
    - Thumbnail text suggestions
    """
    
    print_banner()
    
    # Validate input file
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"❌ Error: Input file '{input_file}' not found", style="bold red")
        raise typer.Exit(1)
    
    # Validate CSV format
    try:
        validate_csv_file(str(input_path))
        console.print(f"✅ CSV file validation passed", style="green")
    except Exception as e:
        console.print(f"❌ CSV validation failed: {e}", style="bold red")
        raise typer.Exit(1)
    
    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(settings.STRATEGY_STORAGE_PATH)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate strategy ID and timestamp
    strategy_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()
    
    console.print(f"🎯 Starting analysis with Strategy ID: {strategy_id}", style="bold yellow")
    console.print(f"📊 Input: {input_file}", style="cyan")
    console.print(f"🎪 Goal: {goal}", style="cyan")
    if audience:
        console.print(f"👥 Audience: {audience}", style="cyan")
    console.print(f"🎭 Tone: {tone}", style="cyan")
    console.print()
    
    # Run the analysis pipeline
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize strategy runner
            task1 = progress.add_task("🔧 Initializing AI Strategy Runner...", total=None)
            runner = AIStrategyRunner(
                correlation_id=strategy_id,
                verbose=verbose
            )
            progress.update(task1, description="✅ AI Strategy Runner initialized")
            progress.remove_task(task1)
            
            # Run the full pipeline
            task2 = progress.add_task("🚀 Running analysis pipeline...", total=None)
            result = asyncio.run(runner.run_full_analysis(
                csv_file=str(input_path),
                goal=goal,
                audience=audience,
                tone=tone
            ))
            progress.update(task2, description="✅ Analysis pipeline completed")
            progress.remove_task(task2)
            
            # Save results
            task3 = progress.add_task("💾 Saving strategy results...", total=None)
            output_file = output_path / f"strategy_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Prepare final result with metadata
            final_result = {
                "strategy_id": strategy_id,
                "timestamp": timestamp,
                "input_file": str(input_path),
                "goal": goal,
                "audience": audience,
                "tone": tone,
                "analysis_result": result,
                "cli_version": "1.0.0"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
            
            progress.update(task3, description="✅ Results saved successfully")
            progress.remove_task(task3)
    
    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="bold red")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)
    
    # Display results summary
    console.print()
    console.print("🎉 Analysis Complete!", style="bold green")
    console.print()
    
    # Create results table
    table = Table(title="📊 Strategy Results Summary")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    
    analysis_result = result.get("analysis_result", {})
    
    table.add_row(
        "Keywords",
        "✅ Analyzed" if analysis_result.get("keywords") else "❌ Failed",
        f"{len(analysis_result.get('keywords', []))} keywords found"
    )
    
    table.add_row(
        "Content Gaps",
        "✅ Detected" if analysis_result.get("gaps") else "❌ Failed",
        f"{len(analysis_result.get('gaps', []))} gaps identified"
    )
    
    table.add_row(
        "AI Optimization",
        "✅ Generated" if analysis_result.get("optimized_content") else "❌ Failed",
        "Titles, descriptions, and tags optimized"
    )
    
    table.add_row(
        "Strategy File",
        "✅ Saved",
        str(output_file)
    )
    
    console.print(table)
    console.print()
    
    # Show key insights
    if analysis_result.get("insights"):
        insights_panel = Panel(
            analysis_result["insights"],
            title="🧠 Key Insights",
            border_style="blue"
        )
        console.print(insights_panel)
    
    console.print(f"📁 Full strategy saved to: {output_file}", style="bold yellow")
    console.print("🎯 Use 'python cli.py strategies' to view all saved strategies", style="dim")


@app.command()
def strategies(
    list_all: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all saved strategies"
    ),
    strategy_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Show details for specific strategy ID"
    ),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json"
    )
):
    """
    📚 Manage and view saved strategy sessions
    
    List past analysis results, view specific strategies, or export data.
    """
    
    print_banner()
    
    strategies_path = Path(settings.STRATEGY_STORAGE_PATH)
    
    if not strategies_path.exists():
        console.print("📁 No strategies found. Run an analysis first!", style="yellow")
        return
    
    # Get all strategy files
    strategy_files = list(strategies_path.glob("strategy_*.json"))
    
    if not strategy_files:
        console.print("📁 No strategy files found in storage directory", style="yellow")
        return
    
    if strategy_id:
        # Show specific strategy
        matching_files = [f for f in strategy_files if strategy_id in f.name]
        if not matching_files:
            console.print(f"❌ Strategy ID '{strategy_id}' not found", style="red")
            return
        
        with open(matching_files[0], 'r', encoding='utf-8') as f:
            strategy_data = json.load(f)
        
        if output_format == "json":
            console.print(json.dumps(strategy_data, indent=2))
        else:
            console.print(f"📊 Strategy Details: {strategy_data['strategy_id']}", style="bold blue")
            console.print(f"🕒 Created: {strategy_data['timestamp']}")
            console.print(f"🎯 Goal: {strategy_data['goal']}")
            console.print(f"👥 Audience: {strategy_data.get('audience', 'Not specified')}")
            console.print(f"🎭 Tone: {strategy_data.get('tone', 'Not specified')}")
            console.print(f"📁 File: {matching_files[0]}")
    
    else:
        # List all strategies
        if output_format == "json":
            strategies_list = []
            for file_path in sorted(strategy_files, key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    strategies_list.append({
                        "strategy_id": data.get("strategy_id"),
                        "timestamp": data.get("timestamp"),
                        "goal": data.get("goal"),
                        "file": str(file_path)
                    })
                except Exception:
                    continue
            console.print(json.dumps(strategies_list, indent=2))
        
        else:
            # Table format
            table = Table(title="📚 Saved Strategy Sessions")
            table.add_column("Strategy ID", style="cyan")
            table.add_column("Created", style="green")
            table.add_column("Goal", style="white")
            table.add_column("Audience", style="yellow")
            table.add_column("File Size", style="dim")
            
            for file_path in sorted(strategy_files, key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Format timestamp
                    timestamp = data.get("timestamp", "Unknown")
                    if "T" in timestamp:
                        timestamp = timestamp.split("T")[0]
                    
                    # Get file size
                    file_size = f"{file_path.stat().st_size / 1024:.1f} KB"
                    
                    table.add_row(
                        data.get("strategy_id", "Unknown")[:8],
                        timestamp,
                        data.get("goal", "No goal specified")[:50] + ("..." if len(data.get("goal", "")) > 50 else ""),
                        data.get("audience", "Not specified"),
                        file_size
                    )
                except Exception:
                    continue
            
            console.print(table)
            console.print(f"\n📁 Total strategies found: {len(strategy_files)}")
            console.print("💡 Use --id=<strategy_id> to view specific strategy details")


@app.command()
def validate(
    input_file: str = typer.Argument(..., help="Path to CSV file to validate")
):
    """
    ✅ Validate CSV file format for YouTube data analysis
    
    Checks if your CSV file has the required columns and format for analysis.
    """
    
    print_banner()
    
    input_path = Path(input_file)
    if not input_path.exists():
        console.print(f"❌ Error: File '{input_file}' not found", style="bold red")
        raise typer.Exit(1)
    
    try:
        with console.status("[bold blue]Validating CSV file..."):
            validate_csv_file(str(input_path))
        
        console.print("✅ CSV file validation passed!", style="bold green")
        console.print(f"📊 File '{input_file}' is ready for analysis", style="green")
        
    except Exception as e:
        console.print(f"❌ CSV validation failed:", style="bold red")
        console.print(f"   {e}", style="red")
        console.print("\n💡 Make sure your CSV file contains YouTube channel data with proper columns", style="yellow")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
