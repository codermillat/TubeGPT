#!/usr/bin/env python3
"""
Example script showing how to use the Gemini YouTube Analyzer.
"""

from gemini_chat import GeminiYouTubeAnalyzer
import os

def run_analysis_examples():
    """Run several example analyses."""
    
    # Initialize analyzer
    analyzer = GeminiYouTubeAnalyzer()
    
    # Path to your YouTube analytics CSV
    csv_path = "yt_analytics.csv"
    
    if not os.path.exists(csv_path):
        print(f"Please run yt_fetch.py first to generate {csv_path}")
        return
    
    # Example questions
    questions = [
        "What are my top 3 performing videos and what makes them successful?",
        "How can I improve my click-through rate based on my current data?",
        "Which videos have the best audience retention and why?",
        "What patterns do you see in my video performance over time?",
        "How do my videos perform in different countries?"
    ]
    
    print("YouTube Analytics AI Analysis Examples")
    print("=" * 50)
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. QUESTION: {question}")
        print("-" * 50)
        
        response = analyzer.analyze_youtube_data(question, csv_path)
        print(response)
        print("\n" + "=" * 50)

if __name__ == "__main__":
    run_analysis_examples()