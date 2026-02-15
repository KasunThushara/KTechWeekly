"""
Weekly Archive Manager
Prevents page duplication by archiving old reports and maintaining clean history
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "weekly_reports"
DOCS_DIR = PROJECT_ROOT / "docs"
ARCHIVE_DIR = PROJECT_ROOT / "archive"
DATA_DIR = PROJECT_ROOT / "data"


class ArchiveManager:
    """Manages weekly archives to prevent duplication and maintain history."""

    def __init__(self):
        self.current_week = datetime.now().strftime('%Y-W%W')
        self.archive_index_file = ARCHIVE_DIR / "index.json"
        self.archive_index = self.load_archive_index()

    def load_archive_index(self):
        """Load archive index."""
        if self.archive_index_file.exists():
            with open(self.archive_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"weeks": [], "latest_week": None}

    def save_archive_index(self):
        """Save archive index."""
        self.archive_index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.archive_index_file, 'w', encoding='utf-8') as f:
            json.dump(self.archive_index, f, indent=2)

    def should_archive(self):
        """
        Determine if we should archive previous week's content.
        Returns True if this is a new week.
        """
        latest_week = self.archive_index.get('latest_week')

        if latest_week is None:
            print("🆕 First run - no archiving needed")
            return False

        if latest_week != self.current_week:
            print(f"📅 New week detected: {self.current_week} (previous: {latest_week})")
            return True

        print(f"📅 Same week: {self.current_week} - updating existing reports")
        return False

    def archive_previous_week(self):
        """Archive previous week's reports before generating new ones."""
        latest_week = self.archive_index.get('latest_week')

        if not latest_week:
            print("⚠️  No previous week to archive")
            return

        print(f"\n📦 Archiving week {latest_week}...")

        # Create archive directory for the week
        week_archive_dir = ARCHIVE_DIR / latest_week
        week_archive_dir.mkdir(parents=True, exist_ok=True)

        archived_files = []

        # Archive markdown reports
        if REPORTS_DIR.exists():
            for md_file in REPORTS_DIR.glob('*.md'):
                dest = week_archive_dir / "reports" / md_file.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(md_file, dest)
                archived_files.append(f"reports/{md_file.name}")

        # Archive HTML files (except index.html which is always current)
        if DOCS_DIR.exists():
            for html_file in DOCS_DIR.glob('*.html'):
                if html_file.name != 'index.html':
                    dest = week_archive_dir / "html" / html_file.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(html_file, dest)
                    archived_files.append(f"html/{html_file.name}")

        # Archive data files
        if DATA_DIR.exists():
            for data_file in ['cleaned_articles.json', 'abstracted_articles.json']:
                src = DATA_DIR / data_file
                if src.exists():
                    dest = week_archive_dir / "data" / data_file
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                    archived_files.append(f"data/{data_file}")

        # Update archive index
        week_entry = {
            "week": latest_week,
            "archived_date": datetime.now().isoformat(),
            "files": archived_files,
            "file_count": len(archived_files)
        }

        self.archive_index["weeks"].append(week_entry)

        print(f"✅ Archived {len(archived_files)} files to {week_archive_dir}")
        return week_entry

    def clean_current_directories(self):
        """Clean current working directories before new generation."""
        print("\n🧹 Cleaning current directories...")

        cleaned = []

        # Clean reports directory (keep directory structure)
        if REPORTS_DIR.exists():
            for md_file in REPORTS_DIR.glob('*.md'):
                md_file.unlink()
                cleaned.append(f"reports/{md_file.name}")

        # Clean docs directory (except index.html)
        if DOCS_DIR.exists():
            for html_file in DOCS_DIR.glob('*.html'):
                if html_file.name != 'index.html':
                    html_file.unlink()
                    cleaned.append(f"html/{html_file.name}")

        print(f"✅ Cleaned {len(cleaned)} old files")
        return cleaned

    def update_current_week(self):
        """Update the archive index with current week."""
        self.archive_index["latest_week"] = self.current_week
        self.archive_index["last_updated"] = datetime.now().isoformat()
        self.save_archive_index()
        print(f"✅ Updated current week to: {self.current_week}")

    def generate_archive_page(self):
        """Generate an HTML page listing all archived weeks."""
        print("\n📄 Generating archive index page...")

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Archive - Tech Weekly Digest</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: #2563eb; }
        .week-entry {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .week-entry h3 {
            color: #1f2937;
            margin-top: 0;
        }
        .week-entry a {
            color: #2563eb;
            text-decoration: none;
        }
        .week-entry a:hover {
            text-decoration: underline;
        }
        .meta {
            color: #6b7280;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <h1>📚 Tech Weekly Digest Archive</h1>
    <p><a href="index.html">← Back to Latest Digest</a></p>
    <hr>
"""

        # List weeks in reverse chronological order
        weeks = sorted(self.archive_index.get("weeks", []),
                       key=lambda x: x['week'], reverse=True)

        for week_entry in weeks:
            week_num = week_entry['week']
            archived_date = week_entry.get('archived_date', 'Unknown')[:10]
            file_count = week_entry.get('file_count', 0)

            # Parse week number to readable format
            try:
                year, week = week_num.split('-W')
                week_display = f"Week {week}, {year}"
            except:
                week_display = week_num

            html += f"""
    <div class="week-entry">
        <h3>📅 {week_display}</h3>
        <p class="meta">Archived: {archived_date} | Files: {file_count}</p>
        <p>
            <a href="../archive/{week_num}/html/weekly_master_report.html">📰 Read Full Report</a> |
            <a href="../archive/{week_num}/reports/">📝 View Markdown</a>
        </p>
    </div>
"""

        html += """
    <hr>
    <p style="text-align: center; color: #6b7280;">
        Archive maintained automatically by Tech Weekly Digest
    </p>
</body>
</html>
"""

        # Save archive page
        archive_page = DOCS_DIR / "archive.html"
        archive_page.parent.mkdir(parents=True, exist_ok=True)
        with open(archive_page, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ Archive page generated: {archive_page}")

    def get_archive_stats(self):
        """Get statistics about the archive."""
        weeks = self.archive_index.get("weeks", [])
        total_files = sum(w.get('file_count', 0) for w in weeks)

        return {
            "total_weeks": len(weeks),
            "total_files": total_files,
            "current_week": self.current_week,
            "latest_archived_week": self.archive_index.get("latest_week")
        }


def main():
    """Main archive management workflow."""
    print("=" * 70)
    print("📦 Weekly Archive Manager")
    print("=" * 70)

    manager = ArchiveManager()

    # Check if we need to archive
    if manager.should_archive():
        # Archive previous week
        manager.archive_previous_week()

        # Clean current directories
        manager.clean_current_directories()

    # Update current week
    manager.update_current_week()

    # Generate archive page
    manager.generate_archive_page()

    # Show stats
    stats = manager.get_archive_stats()
    print("\n" + "=" * 70)
    print("📊 Archive Statistics")
    print("=" * 70)
    print(f"Current Week: {stats['current_week']}")
    print(f"Total Archived Weeks: {stats['total_weeks']}")
    print(f"Total Archived Files: {stats['total_files']}")
    print("=" * 70)
    print("\n✅ Archive management complete!")


if __name__ == "__main__":
    main()