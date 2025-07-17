#!/usr/bin/env python3
"""
Minimal CLI test for TubeGPT - Simple analysis without complex imports
"""

import asyncio
import json
import pandas as pd
import typer
from rich.console import Console
from pathlib import Path
from datetime import datetime

app = typer.Typer(name="TubeGPT Mini CLI")
console = Console()

def validate_csv_simple(file_path: str) -> bool:
    """Simple CSV validation"""
    try:
        df = pd.read_csv(file_path)
        console.print(f"✅ CSV loaded successfully: {len(df)} rows", style="green")
        console.print(f"Columns: {list(df.columns)}", style="dim")
        return True
    except Exception as e:
        console.print(f"❌ CSV validation failed: {e}", style="red")
        return False

def simple_keyword_analysis(df: pd.DataFrame) -> dict:
    """Simple keyword extraction from titles"""
    import re
    
    keywords = []
    
    # Find title column
    title_col = None
    for col in df.columns:
        if 'title' in col.lower():
            title_col = col
            break
    
    if title_col:
        titles = df[title_col].dropna().tolist()
        for title in titles:
            words = re.findall(r'\b\w{4,}\b', str(title).lower())
            keywords.extend(words)
    
    # Get top keywords
    from collections import Counter
    keyword_counts = Counter(keywords)
    top_keywords = [k for k, v in keyword_counts.most_common(10)]
    
    return {
        "keywords": top_keywords,
        "total_titles": len(titles) if title_col else 0,
        "unique_keywords": len(set(keywords))
    }

def simple_gap_analysis(df: pd.DataFrame) -> dict:
    """Simple content gap analysis"""
    gaps = []
    
    # Find title column
    title_col = None
    for col in df.columns:
        if 'title' in col.lower():
            title_col = col
            break
    
    if title_col:
        titles = df[title_col].dropna().tolist()
        
        # Simple gap detection - missing common topics
        common_topics = ['tutorial', 'guide', 'tips', 'tricks', 'best', 'how to', 'review']
        found_topics = []
        
        for title in titles:
            for topic in common_topics:
                if topic in str(title).lower():
                    found_topics.append(topic)
        
        missing_topics = [topic for topic in common_topics if topic not in found_topics]
        gaps = [{"topic": topic, "potential": "high"} for topic in missing_topics[:3]]
    
    return {
        "gaps": gaps,
        "opportunities": len(gaps)
    }

def generate_simple_content(keywords: list, gaps: list, goal: str) -> dict:
    """Simple content generation without AI"""
    
    titles = []
    descriptions = []
    tags = keywords[:10]
    
    # Generate titles based on gaps and keywords
    if gaps:
        for gap in gaps[:3]:
            topic = gap.get("topic", "content")
            if keywords:
                titles.append(f"Ultimate {topic.title()} Guide with {keywords[0].title()}")
                titles.append(f"Best {keywords[0].title()} {topic.title()} You Must Know")
        
    # Add keyword-based titles
    for keyword in keywords[:2]:
        titles.append(f"Complete {keyword.title()} Tutorial for Beginners")
        titles.append(f"Advanced {keyword.title()} Tips and Tricks")
    
    # Generate descriptions
    descriptions = [
        f"Learn everything about {goal}. This comprehensive guide covers all the essential topics.",
        f"Discover the best strategies and techniques. Perfect for beginners and advanced users.",
        f"Step-by-step tutorial covering all aspects. Get practical tips you can use today."
    ]
    
    return {
        "titles": titles[:5],
        "descriptions": descriptions,
        "tags": tags,
        "thumbnail_text": ["ULTIMATE GUIDE", "SECRET TIPS", "MUST WATCH"]
    }

@app.command()
def analyze(
    input_file: str = typer.Option(..., "--input", help="CSV file path"),
    goal: str = typer.Option("Generate content strategy", "--goal", help="Analysis goal"),
    audience: str = typer.Option("general", "--audience", help="Target audience"),
    tone: str = typer.Option("engaging", "--tone", help="Content tone")
):
    """Run simple analysis without complex AI dependencies"""
    
    console.print("🎯 TubeGPT Simple Analysis", style="bold blue")
    console.print(f"📊 Input: {input_file}", style="cyan")
    console.print(f"🎪 Goal: {goal}", style="cyan")
    console.print(f"👥 Audience: {audience}", style="cyan")
    console.print(f"🎭 Tone: {tone}", style="cyan")
    console.print()
    
    # Validate CSV
    if not validate_csv_simple(input_file):
        raise typer.Exit(1)
    
    # Load data
    df = pd.read_csv(input_file)
    
    # Run simple analysis
    with console.status("🔍 Analyzing keywords..."):
        keyword_result = simple_keyword_analysis(df)
    
    with console.status("🕳️ Detecting content gaps..."):
        gap_result = simple_gap_analysis(df)
    
    with console.status("✨ Generating content suggestions..."):
        content_result = generate_simple_content(
            keyword_result["keywords"], 
            gap_result["gaps"], 
            goal
        )
    
    # Display results
    console.print("📊 Analysis Results:", style="bold green")
    console.print(f"Keywords found: {len(keyword_result['keywords'])}")
    console.print(f"Content gaps: {gap_result['opportunities']}")
    console.print(f"Generated titles: {len(content_result['titles'])}")
    
    console.print("\n🏷️ Top Keywords:", style="bold")
    for keyword in keyword_result["keywords"][:5]:
        console.print(f"  • {keyword}")
    
    console.print("\n📝 Generated Titles:", style="bold")
    for i, title in enumerate(content_result["titles"], 1):
        console.print(f"  {i}. {title}")
    
    console.print("\n🔗 SEO Tags:", style="bold")
    console.print(f"  {', '.join(content_result['tags'][:10])}")
    
    # Save results
    output_dir = Path("data/storage/strategies")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "goal": goal,
        "audience": audience,
        "tone": tone,
        "keywords": keyword_result,
        "gaps": gap_result,
        "content": content_result,
        "simple_analysis": True
    }
    
    output_file = output_dir / f"simple_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    console.print(f"\n💾 Results saved to: {output_file}", style="bold yellow")
    console.print("✅ Simple analysis complete!", style="bold green")

@app.command()
def validate(file_path: str = typer.Argument(..., help="CSV file to validate")):
    """Validate CSV file format"""
    console.print("📋 Validating CSV file...", style="bold blue")
    
    if validate_csv_simple(file_path):
        console.print("✅ CSV file is valid and ready for analysis!", style="bold green")
    else:
        console.print("❌ CSV file validation failed", style="bold red")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
