#!/usr/bin/env python3
"""
Reset content diversity and force specific themes/styles
"""
import json
from pathlib import Path

def reset_content_diversity():
    """Reset content tracking and force new themes"""
    
    # Reset status to start fresh
    status = {
        "current_content_index": 0,
        "current_style_index": 0,
        "current_theme_category": "tech"  # Start with tech instead of lifestyle
    }
    
    with open("status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    # Clear content history
    history = {
        "videos": [],
        "themes": {},
        "styles": {},
        "content_types": {}
    }
    
    with open("content_history.json", "w") as f:
        json.dump(history, f, indent=2)
    
    print("✅ Content diversity reset!")
    print("🎯 Next video will use: tech theme, animation style")
    print("📊 Content history cleared")

def force_theme(theme_name):
    """Force a specific theme for next video"""
    try:
        with open("status.json", "r") as f:
            status = json.load(f)
    except FileNotFoundError:
        status = {}
    
    status["current_theme_category"] = theme_name
    
    with open("status.json", "w") as f:
        json.dump(status, f, indent=2)
    
    print(f"🎯 Forced next theme to: {theme_name}")

def show_available_themes():
    """Show all available themes"""
    try:
        with open("content_config.json", "r") as f:
            config = json.load(f)
        
        print("📋 Available themes:")
        for theme, topics in config["theme_categories"].items():
            print(f"  {theme}: {', '.join(topics[:3])}...")
    except FileNotFoundError:
        print("❌ content_config.json not found")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "reset":
            reset_content_diversity()
        elif command == "force" and len(sys.argv) > 2:
            force_theme(sys.argv[2])
        elif command == "themes":
            show_available_themes()
        else:
            print("Usage: python reset_diversity.py [reset|force <theme>|themes]")
    else:
        print("Available commands:")
        print("  reset - Reset all diversity tracking")
        print("  force <theme> - Force specific theme for next video")
        print("  themes - Show available themes")