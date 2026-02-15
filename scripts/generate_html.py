"""
Generate beautiful HTML pages from markdown reports for GitHub Pages
"""
import os
import json
import markdown
from datetime import datetime
from pathlib import Path

# Get the project root directory (parent of scripts/)
import sys

PROJECT_ROOT = Path(__file__).parent.parent

MD_DIR = PROJECT_ROOT / "weekly_reports"
HTML_DIR = PROJECT_ROOT / "docs"
DATA_FILE = PROJECT_ROOT / "data" / "abstracted_articles.json"

CATEGORY_INFO = {
    "AI & Machine Learning": {"emoji": "🤖", "description": "..."},
    "Hardware & SBCs": {"emoji": "💻", "description": "..."},
    "GPUs & Accelerators": {"emoji": "🎮", "description": "..."},
    "Semiconductors & Chips": {"emoji": "⚡", "description": "..."},
    "Edge Computing": {"emoji": "📡", "description": "..."},
    "Industry News": {"emoji": "📰", "description": "..."}
}

# Beautiful HTML template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Tech Weekly Digest</title>
    <meta name="description" content="{description}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">

    <style>
        :root {{
            --primary: #2563eb;
            --secondary: #7c3aed;
            --accent: #10b981;
            --text: #1f2937;
            --text-light: #6b7280;
            --bg: #ffffff;
            --bg-secondary: #f9fafb;
            --border: #e5e7eb;
            --shadow: rgba(0, 0, 0, 0.1);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 40px 20px;
            margin-bottom: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 30px var(--shadow);
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .subtitle {{
            font-size: 1.1rem;
            opacity: 0.95;
        }}

        /* Navigation */
        nav {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}

        nav a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: 8px;
            transition: all 0.2s;
        }}

        nav a:hover {{
            background: var(--primary);
            color: white;
        }}

        /* Content */
        .content {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
        }}

        /* Typography */
        h1, h2, h3, h4 {{
            margin-top: 30px;
            margin-bottom: 15px;
            color: var(--text);
            font-weight: 600;
        }}

        h1 {{ font-size: 2.2rem; margin-top: 0; }}
        h2 {{ 
            font-size: 1.8rem; 
            border-bottom: 3px solid var(--primary);
            padding-bottom: 10px;
            margin-top: 40px;
        }}
        h3 {{ font-size: 1.4rem; color: var(--primary); }}
        h4 {{ font-size: 1.1rem; }}

        p {{
            margin-bottom: 15px;
            color: var(--text);
        }}

        a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        /* Lists */
        ul, ol {{
            margin: 15px 0 15px 25px;
        }}

        li {{
            margin-bottom: 8px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            box-shadow: 0 2px 5px var(--shadow);
        }}

        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: var(--primary);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9rem;
        }}

        tr:hover {{
            background: var(--bg-secondary);
        }}

        /* Horizontal Rule */
        hr {{
            border: none;
            border-top: 2px solid var(--border);
            margin: 40px 0;
        }}

        /* Special Elements */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            background: var(--primary);
            color: white;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-right: 8px;
        }}

        .insight {{
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            border-left: 4px solid var(--primary);
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-style: italic;
        }}

        .star {{
            color: #fbbf24;
            font-size: 1.2rem;
        }}

        /* Code blocks */
        code {{
            background: var(--bg-secondary);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }}

        pre {{
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-light);
            border-top: 1px solid var(--border);
            margin-top: 60px;
        }}

        footer a {{
            color: var(--primary);
        }}

        .timestamp {{
            color: var(--text-light);
            font-size: 0.95rem;
            margin-bottom: 10px;
        }}

        /* Category cards */
        .category-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .category-card {{
            background: white;
            border: 2px solid var(--border);
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s;
            text-decoration: none;
            color: var(--text);
            display: block;
        }}

        .category-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px var(--shadow);
            border-color: var(--primary);
        }}

        .category-card h3 {{
            margin-top: 0;
            color: var(--primary);
        }}

        .category-card .count {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--secondary);
            margin: 10px 0;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            header h1 {{ font-size: 1.8rem; }}
            .container {{ padding: 10px; }}
            nav {{ flex-direction: column; }}
            .content {{ padding: 20px; }}
            .category-grid {{ grid-template-columns: 1fr; }}
        }}

        /* Loading animation */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .content {{
            animation: fadeIn 0.5s ease-out;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 Tech Weekly Digest</h1>
            <p class="subtitle">AI, Hardware & Edge Computing News</p>
        </header>

        <nav>
            <a href="index.html">🏠 Home</a>
            {category_links}
        </nav>

        <div class="content">
            {content}
        </div>

        <footer>
            <p class="timestamp">Generated on {timestamp}</p>
            <p>Powered by AI-driven content curation with Ollama</p>
            <p><a href="https://github.com/yourusername/tech-weekly-digest" target="_blank">View on GitHub</a></p>
        </footer>
    </div>
</body>
</html>
"""


def get_category_emoji(category):
    """Get emoji for a category."""
    return CATEGORY_INFO.get(category, {}).get("emoji", "📰")


def collect_stats():
    """Collect statistics from abstracted articles."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                articles = json.load(f)

            category_counts = {}
            for article in articles:
                for tag in article.get('tags', []):
                    category_counts[tag] = category_counts.get(tag, 0) + 1

            print(f"✓ Loaded stats: {len(articles)} articles across {len(category_counts)} categories")
            return {
                'total_articles': len(articles),
                'total_categories': len(category_counts),
                'category_counts': category_counts
            }
        else:
            print(f"⚠️  Stats file not found: {DATA_FILE}")
            print(f"   Attempting to count from markdown files instead...")
            return count_from_markdown_files()
    except Exception as e:
        print(f"⚠️  Could not load stats from JSON: {e}")
        return count_from_markdown_files()


def count_from_markdown_files():
    """Fallback: Count articles from markdown files if JSON doesn't exist."""
    try:
        category_counts = {}
        total = 0

        for md_file in Path(MD_DIR).glob('*.md'):
            if md_file.stem in ['README', 'weekly_master_report']:
                continue

            # Count articles in each markdown file
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Count markdown headers (###) as articles
                article_count = content.count('### ')
                if article_count > 0:
                    category = md_file.stem.replace('_', ' ').title()
                    category_counts[category] = article_count
                    total += article_count

        print(f"✓ Counted from markdown: {total} articles across {len(category_counts)} categories")
        return {
            'total_articles': total,
            'total_categories': len(category_counts),
            'category_counts': category_counts
        }
    except Exception as e:
        print(f"⚠️  Could not count from markdown: {e}")
        return {
            'total_articles': 0,
            'total_categories': 0,
            'category_counts': {}
        }


def convert_md_to_html(md_file, categories):
    """Convert a markdown file to HTML."""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )

        # Get title from filename
        filename = Path(md_file).stem

        if filename == 'README':
            title = 'Weekly Digest'
            description = 'Your curated weekly roundup of tech news'
        else:
            title = filename.replace('_', ' ').title()
            description = f'Latest {title} news and updates'

        # Generate category navigation links
        category_links = []
        for cat in sorted(categories):
            cat_file = cat.lower().replace(' ', '_')
            emoji = get_category_emoji(cat)
            category_links.append(f'<a href="{cat_file}.html">{emoji} {cat}</a>')

        # Add link to main digest
        category_links.insert(1, '<a href="weekly_master_report.html">📰 Full Digest</a>')

        # Fill template
        html = HTML_TEMPLATE.format(
            title=title,
            description=description,
            content=html_content,
            category_links=' '.join(category_links),
            timestamp=datetime.now().strftime('%B %d, %Y at %H:%M UTC')
        )

        return html

    except Exception as e:
        print(f"❌ Error converting {md_file}: {e}")
        return None


def generate_index_page(categories, stats):
    """Generate the main landing page."""
    content = f"""
<div id="home">
    <h1>🚀 Welcome to Tech Weekly Digest</h1>
    <p class="timestamp">Week of {datetime.now().strftime('%B %d, %Y')}</p>

    <p style="font-size: 1.1rem; margin: 20px 0;">
        Your AI-curated weekly roundup of the most important developments in 
        <strong>AI</strong>, <strong>hardware</strong>, and <strong>edge computing</strong>.
    </p>

    <hr>

    <h2>📊 This Week's Coverage</h2>
    <p style="font-size: 1.1rem;">
        We analyzed <strong style="color: var(--primary);">{stats['total_articles']}</strong> articles 
        across <strong style="color: var(--secondary);">{stats['total_categories']}</strong> categories 
        using AI-powered ranking and curation.
    </p>

    <hr>

    <h2>🗂️ Browse by Category</h2>
    <div class="category-grid">
"""

    for category in sorted(categories):
        cat_file = category.lower().replace(' ', '_')
        emoji = get_category_emoji(category)
        count = stats['category_counts'].get(category, 0)
        desc = CATEGORY_INFO.get(category, {}).get('description', category)

        content += f"""
        <a href="{cat_file}.html" class="category-card">
            <h3>{emoji} {category}</h3>
            <div class="count">{count}</div>
            <p style="color: var(--text-light); margin: 0;">{desc}</p>
        </a>
"""

    content += """
    </div>

    <hr>

    <h2>🌟 Featured Reports</h2>
    <p>
        <a href="weekly_master_report.html" style="font-size: 1.2rem; font-weight: 600;">
            📰 Read the Complete Weekly Report →
        </a>
    </p>
    <p style="color: var(--text-light);">
        Includes top stories, trends analysis, and comprehensive coverage across all categories.
    </p>

    <hr>

    <h2>💡 About This Digest</h2>
    <p>
        This digest is automatically generated using:
    </p>
    <ul>
        <li><strong>AI-powered summarization</strong> with Ollama (Gemma 3 4B model)</li>
        <li><strong>Smart ranking</strong> based on importance and relevance</li>
        <li><strong>Multi-source aggregation</strong> from trusted tech news sources</li>
        <li><strong>Category-based organization</strong> for easy navigation</li>
    </ul>

    <p style="margin-top: 20px;">
        Articles are scored on a 0-10 importance scale considering industry impact, 
        technical significance, and professional relevance.
    </p>
</div>
"""

    return content


def main():
    print("🎨 Converting Markdown to HTML for GitHub Pages...\n")

    # Create output directory
    os.makedirs(HTML_DIR, exist_ok=True)

    # Check if markdown files exist
    if not os.path.exists(MD_DIR):
        print(f"❌ Markdown directory '{MD_DIR}/' not found!")
        print("   Run generate_reports.py first to create markdown files.")
        return

    # Get list of markdown files
    md_files = list(Path(MD_DIR).glob('*.md'))
    if not md_files:
        print(f"❌ No markdown files found in '{MD_DIR}/'")
        return

    print(f"✓ Found {len(md_files)} markdown files\n")

    # Collect categories
    categories = set()
    for md_file in md_files:
        if md_file.stem not in ['README', 'weekly_master_report']:
            category = md_file.stem.replace('_', ' ').title()
            categories.add(category)

    # Get statistics
    stats = collect_stats()

    # Convert each markdown file to HTML
    print("📝 Converting markdown files to HTML...\n")
    converted = 0

    for md_file in md_files:
        print(f"  Converting {md_file.name}...", end=" ")

        html_content = convert_md_to_html(md_file, categories)

        if html_content:
            # Determine output filename
            if md_file.stem == 'README':
                html_file = Path(HTML_DIR) / 'weekly_master_report.html'
            else:
                html_file = Path(HTML_DIR) / f'{md_file.stem}.html'

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"✓ → {html_file.name}")
            converted += 1
        else:
            print("✗")

    # Generate custom index page
    print("\n📄 Generating index page...", end=" ")
    index_content = generate_index_page(categories, stats)

    # Use template for index
    category_links = []
    for cat in sorted(categories):
        cat_file = cat.lower().replace(' ', '_')
        emoji = get_category_emoji(cat)
        category_links.append(f'<a href="{cat_file}.html">{emoji} {cat}</a>')

    category_links.insert(1, '<a href="weekly_master_report.html">📰 Full Digest</a>')

    index_html = HTML_TEMPLATE.format(
        title='Home',
        description='AI-curated tech news digest',
        content=index_content,
        category_links=' '.join(category_links),
        timestamp=datetime.now().strftime('%B %d, %Y at %H:%M UTC')
    )

    with open(Path(HTML_DIR) / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

    print("✓ → index.html")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"✅ Successfully generated {converted + 1} HTML files!")
    print(f"{'=' * 70}")
    print(f"\n📁 Output location: {HTML_DIR}/")
    print(f"   • index.html (landing page)")
    print(f"   • weekly_master_report.html (full digest)")
    print(f"   • {len(categories)} category pages")
    print(f"\n🌐 Preview locally:")
    print(f"   cd {HTML_DIR}")
    print(f"   python -m http.server 8000")
    print(f"   Open: http://localhost:8000")
    print(f"\n🚀 Ready to push to GitHub Pages!")


if __name__ == "__main__":
    main()