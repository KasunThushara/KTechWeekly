"""
Generate Reports - Works with Agentic Pipeline
Simple, clean, focused on the 5 core categories
"""
import json
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path

INPUT_FILE = "data/final_articles.json"
OUTPUT_DIR = "weekly_reports"

# Match the 5 categories from agentic_pipeline.py
CATEGORIES = {
    "AI & ML": {"emoji": "🤖", "desc": "Artificial Intelligence and Machine Learning"},
    "Hardware": {"emoji": "💻", "desc": "Computing hardware and development boards"},
    "GPUs": {"emoji": "🎮", "desc": "Graphics cards and compute accelerators"},
    "Semiconductors": {"emoji": "⚡", "desc": "Chip manufacturing and design"},
    "Tech News": {"emoji": "📰", "desc": "Industry news and product launches"},
}


def generate_category_report(category_name, articles, week_date):
    """Generate markdown report for a category."""
    info = CATEGORIES.get(category_name, {"emoji": "📰", "desc": category_name})

    md = f"""# {info['emoji']} {category_name}
**Week of {week_date}**

*{info['desc']}*

---

## 📊 Summary
- **Articles this week:** {len(articles)}
- **Report generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📰 This Week's Articles

"""

    # Sort by quality score (highest first)
    sorted_articles = sorted(articles, key=lambda x: x.get('quality_score', 0), reverse=True)

    for i, article in enumerate(sorted_articles, 1):
        quality = article.get('quality_score', 0)
        stars = '⭐' * (quality // 15)  # 0-2 stars based on quality

        md += f"""### {i}. {article['title']} {stars}

{article['summary']}

"""
        if article.get('insight'):
            md += f"💡 *{article['insight']}*\n\n"

        md += f"🔗 [Read Full Article]({article['link']})\n\n---\n\n"

    return md


def generate_front_page(categorized, week_date):
    """Generate main digest page."""
    total = sum(len(articles) for articles in categorized.values())

    # Get top 5 articles across all categories
    all_articles = []
    for cat_name, articles in categorized.items():
        for article in articles:
            all_articles.append({**article, 'category': cat_name})

    all_articles.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
    top_articles = all_articles[:5]

    md = f"""# 🚀 Tech Weekly Digest
**Week of {week_date}**

Your curated weekly roundup of AI, hardware, and technology news.

---

## 📈 Top Stories This Week

"""

    for i, article in enumerate(top_articles, 1):
        emoji = CATEGORIES.get(article['category'], {}).get('emoji', '📰')
        quality = article.get('quality_score', 0)
        stars = '⭐' * (quality // 15)

        md += f"""### {i}. {article['title']} {stars}

**{emoji} {article['category']}**

{article['summary']}

"""
        if article.get('insight'):
            md += f"💡 **Key Point:** {article['insight']}\n\n"

        md += f"🔗 [Read More]({article['link']})\n\n---\n\n"

    # Category breakdown
    md += f"""## 📊 This Week's Coverage

We covered **{total} articles** across **{len(categorized)} focused categories**.

| Category | Articles | Description |
|----------|----------|-------------|
"""

    for cat_name in sorted(categorized.keys()):
        articles = categorized[cat_name]
        info = CATEGORIES.get(cat_name, {"emoji": "📰", "desc": cat_name})
        filename = cat_name.lower().replace(' ', '_').replace('&', 'and') + '.md'

        md += f"| {info['emoji']} [{cat_name}]({filename}) | {len(articles)} | {info['desc']} |\n"

    # Quick navigation
    md += "\n---\n\n## 🗂️ Browse by Category\n\n"

    for cat_name in sorted(categorized.keys()):
        count = len(categorized[cat_name])
        info = CATEGORIES.get(cat_name, {"emoji": "📰", "desc": cat_name})
        filename = cat_name.lower().replace(' ', '_').replace('&', 'and') + '.md'

        md += f"### {info['emoji']} [{cat_name}]({filename})\n"
        md += f"*{info['desc']}* — {count} articles\n\n"

    md += f"""---

## 📅 About

Generated {datetime.now().strftime('%Y-%m-%d at %H:%M')} by an autonomous AI curation system.

Articles are automatically filtered for quality and relevance.
"""

    return md


def main():
    print("=" * 70)
    print("📝 GENERATING REPORTS")
    print("=" * 70)

    # Load articles
    if not Path(INPUT_FILE).exists():
        print(f"\n❌ {INPUT_FILE} not found!")
        return

    with open(INPUT_FILE, 'r') as f:
        articles = json.load(f)

    print(f"\n✓ Loaded {len(articles)} articles")

    # Group by category
    categorized = defaultdict(list)
    for article in articles:
        # Each article can be in multiple categories
        for category in article.get('categories', ['Tech News']):
            categorized[category].append(article)

    print(f"✓ Found {len(categorized)} categories with content")

    # Show distribution
    print(f"\n📊 Distribution:")
    for cat in sorted(categorized.keys()):
        print(f"   {CATEGORIES.get(cat, {}).get('emoji', '📰')} {cat}: {len(categorized[cat])} articles")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get week date
    week_date = datetime.now().strftime('%B %d, %Y')

    # Generate category reports
    print(f"\n📝 Generating category reports...")
    for category, cat_articles in categorized.items():
        filename = category.lower().replace(' ', '_').replace('&', 'and') + '.md'
        filepath = Path(OUTPUT_DIR) / filename

        content = generate_category_report(category, cat_articles, week_date)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"   ✓ {category}: {len(cat_articles)} articles → {filename}")

    # Generate front page
    print(f"\n📰 Generating front page...")
    front_page = generate_front_page(categorized, week_date)
    front_path = Path(OUTPUT_DIR) / "README.md"

    with open(front_path, 'w', encoding='utf-8') as f:
        f.write(front_page)

    print(f"   ✓ README.md")

    print(f"\n{'=' * 70}")
    print(f"✅ Generated {len(categorized) + 1} report files in {OUTPUT_DIR}/")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()