#!/usr/bin/env python3
"""
Master pipeline runner for Tech Weekly Digest
Runs all scripts in sequence and optionally pushes to GitHub
Uses Groq API instead of local Ollama
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Colors for Windows terminal
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
║           TECH WEEKLY DIGEST - PIPELINE RUNNER              ║
║                    Powered by Groq API                       ║
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
        print("  3. Or set as environment variable")
        print(f"\n{Colors.BLUE}Get your API key at: https://console.groq.com{Colors.RESET}\n")
        return False

    # Test API connection
    try:
        from groq import Groq

        # Initialize client - handles version compatibility
        try:
            client = Groq(api_key=api_key)
        except TypeError:
            # Fallback for older versions
            import groq
            groq.api_key = api_key
            client = groq

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
        print(f"\n{Colors.YELLOW}Please check:{Colors.RESET}")
        print("  1. Your API key is valid")
        print("  2. You have internet connection")
        print("  3. The model name is correct in .env\n")
        return False


def run_script(script_name, description, step_num, total_steps):
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
            check=True
        )

        print(f"\n{Colors.GREEN}✓ {description} - COMPLETED{Colors.RESET}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.RED}✗ Error in {script_name}{Colors.RESET}")
        print(f"   Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.RESET}")
        return False


def push_to_github(auto_push=False):
    """Push changes to GitHub."""
    print(f"\n{Colors.BLUE}{'=' * 70}")
    print("[STEP 5/5] Push to GitHub")
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

    # Ask for confirmation unless auto-push
    if not auto_push:
        print(f"\n{Colors.YELLOW}Push to GitHub? (Y/N):{Colors.RESET} ", end="")
        response = input().strip().upper()
        if response != 'Y':
            print(f"\n{Colors.YELLOW}⏸  Push cancelled{Colors.RESET}")
            print("   You can push manually with: git push origin main")
            return False

    # Get current date for commit message
    date_str = datetime.now().strftime('%Y-%m-%d')

    try:
        # Add files
        print(f"\n{Colors.BLUE}Adding files...{Colors.RESET}")
        subprocess.run(["git", "add", "docs/", "weekly_reports/", "data/"], check=True)

        # Commit
        print(f"{Colors.BLUE}Committing...{Colors.RESET}")
        commit_msg = f"Weekly update: {date_str}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)

        # Push
        print(f"{Colors.BLUE}Pushing to GitHub...{Colors.RESET}")
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print(f"\n{Colors.GREEN}✓ Successfully pushed to GitHub!{Colors.RESET}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n{Colors.RED}✗ Git operation failed{Colors.RESET}")
        return False


def main():
    """Main pipeline execution."""
    print_header()

    start_time = datetime.now()

    # Check for flags
    auto_push = '--auto-push' in sys.argv or '-y' in sys.argv
    skip_push = '--no-push' in sys.argv

    # Ensure directories exist
    for directory in ["data", "weekly_reports", "docs"]:
        os.makedirs(directory, exist_ok=True)

    # Check Groq API first
    if not check_groq_api():
        print(f"\n{Colors.RED}⌛ Pipeline aborted - Groq API not configured{Colors.RESET}\n")
        sys.exit(1)

    # Define pipeline steps
    steps = [
        ("fetch.py", "Fetching and cleaning articles from RSS feeds"),
        ("summary_tag.py", "AI summarization and tagging with Groq API"),
        ("generate_reports.py", "Generating markdown reports with rankings"),
        ("generate_html.py", "Converting to HTML for GitHub Pages")
    ]

    # Run pipeline
    results = []
    for i, (script, desc) in enumerate(steps, 1):
        success = run_script(script, desc, i, len(steps) + (0 if skip_push else 1))
        results.append(success)

        if not success:
            print(f"\n{Colors.RED}⚠  Pipeline stopped due to error{Colors.RESET}")
            break

    # Push to GitHub (if not skipped)
    if not skip_push and all(results):
        push_success = push_to_github(auto_push)
        results.append(push_success)

    # Summary
    elapsed = datetime.now() - start_time

    print(f"\n{Colors.BLUE}{'=' * 70}")
    print("📊 PIPELINE SUMMARY")
    print(f"{'=' * 70}{Colors.RESET}\n")

    for i, (script, desc) in enumerate(steps, 1):
        if i <= len(results):
            status = f"{Colors.GREEN}✓{Colors.RESET}" if results[i - 1] else f"{Colors.RED}✗{Colors.RESET}"
            print(f"{status} Step {i}: {desc}")

    if not skip_push:
        if len(results) > len(steps):
            status = f"{Colors.GREEN}✓{Colors.RESET}" if results[-1] else f"{Colors.RED}✗{Colors.RESET}"
            print(f"{status} Step {len(steps) + 1}: Push to GitHub")

    print(f"\n⏱️  Total time: {elapsed.total_seconds():.1f} seconds")

    if all(results):
        print(f"\n{Colors.GREEN}{'=' * 70}")
        print("✨ SUCCESS! Pipeline completed successfully!")
        print(f"{'=' * 70}{Colors.RESET}\n")

        if not skip_push:
            print("🌐 Your site will update in 1-2 minutes at:")
            print("   https://github.com/KasunThushara/KTechWeekly\n")
        else:
            print("📁 Files are ready in docs/ folder")
            print("   Run without --no-push to push to GitHub\n")
    else:
        print(f"\n{Colors.RED}{'=' * 70}")
        print("⌛ Pipeline failed - check errors above")
        print(f"{'=' * 70}{Colors.RESET}\n")
        sys.exit(1)


def show_help():
    """Show usage help."""
    print("""
Usage: python run_weekly.py [OPTIONS]

Options:
  --auto-push, -y    Auto-push to GitHub without asking
  --no-push          Skip GitHub push (just run pipeline)
  --help, -h         Show this help message

Examples:
  python run_weekly.py              # Run pipeline, ask before push
  python run_weekly.py --auto-push  # Run and auto-push
  python run_weekly.py --no-push    # Just generate files, don't push

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
            print(f"\n\n{Colors.YELLOW}⚠  Pipeline cancelled by user{Colors.RESET}\n")
            sys.exit(1)