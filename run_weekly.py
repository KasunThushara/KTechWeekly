#!/usr/bin/env python3
"""
Improved Master Pipeline Runner for Tech Weekly Digest
- Includes archive management
- Better error handling
- Agentic decision making
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Print fancy header."""
    print(f"""
{Colors.BLUE}{'=' * 70}
║        TECH WEEKLY DIGEST - IMPROVED PIPELINE RUNNER           ║
║                  Powered by Groq API + Archives                ║
{'=' * 70}{Colors.RESET}
    """)


def check_groq_api():
    """Check if Groq API key is configured."""
    print(f"\n{Colors.YELLOW}[CHECK] Verifying Groq API configuration...{Colors.RESET}")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print(f"{Colors.RED}✗ Groq API key not found!{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Please configure your API key:{Colors.RESET}")
        print("  1. Create a .env file in the project root")
        print("  2. Add: GROQ_API_KEY=your_api_key_here")
        print(f"\n{Colors.BLUE}Get your API key at: https://console.groq.com{Colors.RESET}\n")
        return False

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        # Test connection
        client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        print(f"{Colors.GREEN}✓ Groq API is configured and working{Colors.RESET}")
        print(f"  Model: {os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')}")
        return True
    except ImportError:
        print(f"{Colors.RED}✗ Groq library not installed{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Please install it:{Colors.RESET}")
        print("  pip install groq python-dotenv\n")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Cannot connect to Groq API: {e}{Colors.RESET}")
        return False


def run_script(script_name, description, step_num, total_steps, required=True):
    """Run a Python script and handle errors."""
    print(f"\n{Colors.BLUE}{'=' * 70}")
    print(f"[STEP {step_num}/{total_steps}] {description}")
    print(f"{'=' * 70}{Colors.RESET}\n")

    script_path = Path("scripts") / script_name

    if not script_path.exists():
        print(f"{Colors.RED}✗ Script not found: {script_path}{Colors.RESET}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
            check=True,
            capture_output=False
        )

        print(f"\n{Colors.GREEN}✓ {description} - COMPLETED{Colors.RESET}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.RED}✗ Error in {script_name}{Colors.RESET}")
        if required:
            print(f"{Colors.RED}This is a required step - pipeline aborted{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}This is an optional step - continuing...{Colors.RESET}")
        return not required
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.RESET}")
        return not required


def check_for_new_articles():
    """Check if there are new articles to process."""
    data_file = Path("data/cleaned_articles.json")

    if not data_file.exists():
        return True  # Allow first run

    import json
    try:
        with open(data_file, 'r') as f:
            articles = json.load(f)
            return len(articles) > 0
    except:
        return True


def clean_everything():
    """Clean all old files before new generation."""
    import shutil
    from pathlib import Path

    print("\n🧹 Cleaning old files...")

    # 1. Delete ALL markdown reports
    reports_dir = Path("weekly_reports")
    if reports_dir.exists():
        shutil.rmtree(reports_dir)
        reports_dir.mkdir()
        print("   ✓ Cleaned weekly_reports/")

    # 2. Delete ALL HTML files (except keep docs folder)
    docs_dir = Path("docs")
    if docs_dir.exists():
        for html_file in docs_dir.glob("*.html"):
            html_file.unlink()
        print("   ✓ Cleaned docs/*.html")

    # 3. Delete processed data
    data_files = [
        "data/cleaned_articles.json",
        "data/abstracted_articles.json",
        "data/curated_articles.json",
        "data/final_articles.json"
    ]
    for file in data_files:
        if Path(file).exists():
            Path(file).unlink()
    print("   ✓ Cleaned processed data")

    print("✅ All old files removed - fresh start!\n")


def push_to_github(auto_push=False):
    """Push changes to GitHub."""
    print(f"\n{Colors.BLUE}{'=' * 70}")
    print("[FINAL STEP] Push to GitHub")
    print(f"{'=' * 70}{Colors.RESET}\n")

    # Check for changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    if not result.stdout.strip():
        print(f"{Colors.YELLOW}ℹ  No changes to commit{Colors.RESET}")
        return True

    # Show changes
    print(f"{Colors.YELLOW}📋 Changes detected:{Colors.RESET}")
    subprocess.run(["git", "status", "-s"])

    if not auto_push:
        print(f"\n{Colors.YELLOW}Push to GitHub? (Y/N):{Colors.RESET} ", end="")
        response = input().strip().upper()
        if response != 'Y':
            print(f"\n{Colors.YELLOW}⸚ Push cancelled{Colors.RESET}")
            return False

    week_num = datetime.now().strftime('%Y-W%W')

    try:
        print(f"\n{Colors.BLUE}Adding files...{Colors.RESET}")
        subprocess.run(["git", "add", "docs/", "weekly_reports/", "data/", "archive/"], check=True)

        print(f"{Colors.BLUE}Committing...{Colors.RESET}")
        commit_msg = f"Weekly update: {week_num} [automated]"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        print(f"{Colors.BLUE}Pushing to GitHub...{Colors.RESET}")
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print(f"\n{Colors.GREEN}✓ Successfully pushed to GitHub!{Colors.RESET}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.RED}✗ Git operation failed{Colors.RESET}")
        return False


def show_summary_stats():
    """Show summary statistics about the run."""
    print(f"\n{Colors.BLUE}{'=' * 70}")
    print("📊 GENERATION SUMMARY")
    print(f"{'=' * 70}{Colors.RESET}\n")

    # Check articles
    import json
    data_file = Path("data/cleaned_articles.json")
    if data_file.exists():
        try:
            with open(data_file, 'r') as f:
                articles = json.load(f)
                print(f"📰 New Articles: {len(articles)}")
        except:
            pass

    # Check archive
    archive_index = Path("archive/index.json")
    if archive_index.exists():
        try:
            with open(archive_index, 'r') as f:
                index = json.load(f)
                print(f"📦 Archived Weeks: {len(index.get('weeks', []))}")
                print(f"📅 Current Week: {index.get('latest_week', 'Unknown')}")
        except:
            pass


def main():
    """Main pipeline execution."""
    print_header()
    clean_everything()
    start_time = datetime.now()

    # Parse arguments
    auto_push = '--auto-push' in sys.argv or '-y' in sys.argv
    skip_push = '--no-push' in sys.argv
    force = '--force' in sys.argv

    # Ensure directories exist
    for directory in ["data", "weekly_reports", "docs", "archive"]:
        os.makedirs(directory, exist_ok=True)

    # Check Groq API
    if not check_groq_api():
        print(f"\n{Colors.RED}⌛ Pipeline aborted - Groq API not configured{Colors.RESET}\n")
        sys.exit(1)

    # Define pipeline steps
    steps = [
        ("fetch.py", "Fetch and curate articles with agentic pipeline", True),
        ("summarize.py", "AI enhancement of summaries", True),
        ("generate_reports.py", "Generate markdown reports", True),
        ("generate_html.py", "Convert to HTML", True)
    ]

    # Agentic Decision: Check if there are new articles after fetching
    print(f"\n{Colors.YELLOW}[AGENT] Making autonomous decisions...{Colors.RESET}")

    results = []
    for i, (script, desc, required) in enumerate(steps, 1):
        success = run_script(script, desc, i, len(steps), required)
        results.append(success)

        if not success and required:
            print(f"\n{Colors.RED}⚠ Pipeline stopped due to critical error{Colors.RESET}")
            break

        # Agentic check after fetching
        if i == 2 and success:  # After fetch step
            if not check_for_new_articles():
                print(f"\n{Colors.YELLOW}[AGENT] No new articles found - stopping pipeline{Colors.RESET}")
                print(f"{Colors.YELLOW}This is normal if:{Colors.RESET}")
                print("  • All articles were duplicates")
                print("  • No articles matched relevance criteria")
                break

    # Push to GitHub (if not skipped and steps succeeded)
    if not skip_push and all(results):
        push_success = push_to_github(auto_push)
        results.append(push_success)

    # Show summary
    elapsed = datetime.now() - start_time
    show_summary_stats()

    print(f"\n{Colors.BLUE}{'=' * 70}")
    print("⏱️ EXECUTION SUMMARY")
    print(f"{'=' * 70}{Colors.RESET}\n")

    for i, (script, desc, required) in enumerate(steps, 1):
        if i <= len(results):
            status = f"{Colors.GREEN}✓{Colors.RESET}" if results[i - 1] else f"{Colors.RED}✗{Colors.RESET}"
            req_marker = "[REQUIRED]" if required else "[OPTIONAL]"
            print(f"{status} Step {i}: {desc} {req_marker}")

    if not skip_push and len(results) > len(steps):
        status = f"{Colors.GREEN}✓{Colors.RESET}" if results[-1] else f"{Colors.RED}✗{Colors.RESET}"
        print(f"{status} Final: Push to GitHub")

    print(f"\n⏱️  Total time: {elapsed.total_seconds():.1f} seconds")

    if all(results):
        print(f"\n{Colors.GREEN}{'=' * 70}")
        print("✨ SUCCESS! Pipeline completed successfully!")
        print(f"{'=' * 70}{Colors.RESET}\n")

        if not skip_push:
            print("🌐 Your site will update in 1-2 minutes")
        else:
            print("📁 Files are ready in docs/ folder")
    else:
        print(f"\n{Colors.YELLOW}{'=' * 70}")
        print("⚠ Pipeline completed with warnings")
        print(f"{'=' * 70}{Colors.RESET}\n")


def show_help():
    """Show usage help."""
    print("""
Usage: python run_weekly.py [OPTIONS]

Options:
  --auto-push, -y    Auto-push to GitHub without asking
  --no-push          Skip GitHub push (just run pipeline)
  --force            Force run even if no new articles
  --help, -h         Show this help message

Examples:
  python run_weekly.py              # Run pipeline, ask before push
  python run_weekly.py --auto-push  # Run and auto-push
  python run_weekly.py --no-push    # Just generate files, don't push

Features:
  ✓ Automatic archive management (prevents duplication)
  ✓ Intelligent article filtering (relevance scoring)
  ✓ Deduplication across weeks (30-day history)
  ✓ Agentic decision making (stops if no new content)
  ✓ Narrowed topic focus (AI, hardware, edge computing)

Environment Variables (set in .env file):
  GROQ_API_KEY       Your Groq API key (required)
  GROQ_MODEL         Model to use (default: llama-3.1-8b-instant)
  REQUEST_DELAY      Delay between API calls (default: 2.0 seconds)
    """)



if __name__ == "__main__":
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
    else:
        try:
            main()
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠ Pipeline cancelled by user{Colors.RESET}\n")
            sys.exit(1)