import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from ollama import chat

INPUT_FILE = "../data/abstracted_articles.json"
OUTPUT_DIR = "../weekly_reports"
MODEL = "gemma3:4b"

CATEGORY_INFO = {
    "AI": {"emoji": "🤖", "description": "Artificial Intelligence developments"},
    "Machine Learning": {"emoji": "🧠", "description": "ML algorithms and research"},
    "NVIDIA": {"emoji": "🎮", "description": "NVIDIA hardware and GPUs"},
    "Raspberry Pi": {"emoji": "🍓", "description": "Raspberry Pi projects"},
    "Rockchip": {"emoji": "💎", "description": "Rockchip processors and SBCs"},
    "Semiconductors": {"emoji": "⚡", "description": "Chip manufacturing"},
    "Edge AI": {"emoji": "📡", "description": "AI on edge devices"},
    "Hardware": {"emoji": "🔧", "description": "Hardware news and reviews"},
    "Trends": {"emoji": "📈", "description": "Industry trends"}
}


def rank_article_importance(article):
    """Use AI to score article importance (0-10)."""
    prompt = f"""
Title: {article['title']}
Summary: {article['summary']}
Tags: {', '.join(article.get('tags', []))}

Rate this article's importance on a scale of 0-10, where:
- 10 = Major breakthrough, industry-changing news, or critical development
- 7-9 = Significant news, important product launch, or notable advancement
- 4-6 = Interesting update, useful information, or moderate relevance
- 1-3 = Minor news, deals/promotions, or niche interest
- 0 = Spam or irrelevant

Consider:
- Impact on the industry
- Technical significance
- Novelty and innovation
- Relevance to professionals

Output ONLY a single number from 0-10, nothing else.
"""

    try:
        response = chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        score_text = response.message.content.strip()

        # Extract number from response
        import re
        numbers = re.findall(r'\d+', score_text)
        if numbers:
            score = int(numbers[0])
            return min(max(score, 0), 10)  # Clamp between 0-10
        return 5  # Default middle score

    except Exception as e:
        print(f"  ⚠️  Error ranking '{article['title'][:40]}': {e}")
        return 5


def generate_article_insight(article):
    """Use AI to generate a one-line insight about the article."""
    prompt = f"""
Title: {article['title']}
Summary: {article['summary']}

Write ONE concise sentence (max 15 words) highlighting why this article matters or its key takeaway.

Examples:
- "First consumer GPU to break the PCIe bandwidth ceiling"
- "Could reduce AI inference costs by 40% for edge deployments"
- "Signals shift in industry approach to open-source hardware"

Output ONLY the insight sentence, nothing else.
"""

    try:
        response = chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        insight = response.message.content.strip().strip('"').strip("'")
        return insight if len(insight) < 200 else ""
    except:
        return ""


def rank_articles_in_category(articles, category):
    """Rank articles within a category by importance."""
    print(f"\n🔍 Ranking {len(articles)} articles in {category}...")

    ranked = []
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] Scoring: {article['title'][:50]}...")

        score = rank_article_importance(article)
        insight = generate_article_insight(article)

        ranked.append({
            **article,
            'importance_score': score,
            'insight': insight
        })

    # Sort by score (highest first)
    ranked.sort(key=lambda x: x['importance_score'], reverse=True)
    return ranked


def generate_enhanced_category_report(category, ranked_articles, week_date):
    """Generate improved markdown with rankings."""
    info = CATEGORY_INFO.get(category, {"emoji": "📰", "description": category})

    # Calculate statistics
    high_importance = sum(1 for a in ranked_articles if a['importance_score'] >= 7)
    avg_score = sum(a['importance_score'] for a in ranked_articles) / len(ranked_articles)

    md = f"""# {info['emoji']} {category} Weekly Report
**Week of {week_date}**

*{info['description']}*

---

## 📊 Summary
- **Total Articles:** {len(ranked_articles)}
- **High Priority:** {high_importance} articles (score ≥7)
- **Average Importance:** {avg_score:.1f}/10
- **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 🌟 Top Stories

"""

    # Show top 3 as highlights
    top_stories = ranked_articles[:3]
    for i, article in enumerate(top_stories, 1):
        md += f"""### {i}. {article['title']} {'⭐' * (article['importance_score'] // 3)}

**Importance:** {article['importance_score']}/10

{article['summary']}

"""
        if article.get('insight'):
            md += f"💡 *{article['insight']}*\n\n"

        md += f"🔗 [Read More]({article['link']})\n\n---\n\n"

    # Rest of articles
    if len(ranked_articles) > 3:
        md += "## 📰 Other Stories\n\n"

        for i, article in enumerate(ranked_articles[3:], 4):
            stars = '⭐' * (article['importance_score'] // 3) if article['importance_score'] >= 7 else ''
            md += f"""### {i}. {article['title']} {stars}

**Score:** {article['importance_score']}/10 | {article['summary']}

"""
            if article.get('insight'):
                md += f"💡 *{article['insight']}*\n\n"

            md += f"🔗 [Read More]({article['link']})\n\n---\n\n"

    return md


def identify_top_stories(categorized_ranked):
    """Identify the week's most important stories across all categories."""
    all_articles = []
    for category, articles in categorized_ranked.items():
        for article in articles:
            all_articles.append({
                **article,
                'primary_category': category
            })

    # Sort by importance
    all_articles.sort(key=lambda x: x['importance_score'], reverse=True)
    return all_articles[:10]  # Top 10 overall


def generate_front_page(categorized_ranked, top_stories, week_date):
    """Generate an engaging front page digest."""
    total_articles = sum(len(articles) for articles in categorized_ranked.values())

    md = f"""# 🚀 Tech Weekly Digest
**Week of {week_date}**

Your curated weekly roundup of the most important tech news in AI, hardware, and edge computing.

---

## 📈 This Week's Highlights

"""

    # Top stories with insights
    for i, article in enumerate(top_stories[:5], 1):
        emoji = CATEGORY_INFO.get(article['primary_category'], {}).get('emoji', '📰')
        stars = '⭐' * (article['importance_score'] // 3)

        md += f"""### {i}. {article['title']} {stars}

**{emoji} {article['primary_category']}** | Importance: {article['importance_score']}/10

{article['summary']}

"""
        if article.get('insight'):
            md += f"💡 **Key Takeaway:** {article['insight']}\n\n"

        md += f"🔗 [Read Full Article]({article['link']})\n\n---\n\n"

    # Category breakdown
    md += f"""## 📊 By the Numbers

This week we covered **{total_articles} articles** across **{len(categorized_ranked)} categories**.

| Category | Articles | Top Score | Highlights |
|----------|----------|-----------|------------|
"""

    for category in sorted(categorized_ranked.keys()):
        articles = categorized_ranked[category]
        emoji = CATEGORY_INFO.get(category, {}).get('emoji', '📰')
        top_score = max(a['importance_score'] for a in articles)
        high_priority = sum(1 for a in articles if a['importance_score'] >= 7)

        md += f"| {emoji} [{category}]({category.lower().replace(' ', '_')}.md) | {len(articles)} | {top_score}/10 | {high_priority} high-priority |\n"

    # Trending topics analysis
    md += "\n---\n\n## 🔥 Trending Topics\n\n"

    # Count common keywords/themes
    all_tags = []
    for articles in categorized_ranked.values():
        for article in articles:
            all_tags.extend(article.get('tags', []))

    tag_counts = Counter(all_tags)
    top_tags = tag_counts.most_common(5)

    for tag, count in top_tags:
        percentage = (count / total_articles * 100)
        md += f"- **{tag}**: {count} articles ({percentage:.1f}%)\n"

    # Quick navigation
    md += "\n---\n\n## 🗂️ Browse by Category\n\n"

    for category in sorted(categorized_ranked.keys()):
        emoji = CATEGORY_INFO.get(category, {}).get('emoji', '📰')
        count = len(categorized_ranked[category])
        desc = CATEGORY_INFO.get(category, {}).get('description', '')
        md += f"### {emoji} [{category}]({category.lower().replace(' ', '_')}.md)\n"
        md += f"*{desc}* — {count} articles\n\n"

    md += f"""---

## 📅 About This Digest

Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')} using AI-powered ranking and curation.

Articles are scored on a 0-10 importance scale based on:
- Industry impact and significance
- Technical innovation
- Relevance to professionals
- Timeliness and newsworthiness

⭐⭐⭐ = Critical (9-10) | ⭐⭐ = Important (6-8) | ⭐ = Notable (3-5)
"""

    return md


def main():
    print("🤖 AI-Powered Article Ranking & Front Page Generation\n")

    # Load articles
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File '{INPUT_FILE}' not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"✓ Loaded {len(articles)} articles")

    # Group by category
    categorized = defaultdict(list)
    for article in articles:
        tags = article.get('tags', ['Uncategorized'])
        for tag in tags:
            categorized[tag].append(article)

    print(f"✓ Found {len(categorized)} categories")

    # Rank articles within each category
    categorized_ranked = {}
    for category, cat_articles in categorized.items():
        ranked = rank_articles_in_category(cat_articles, category)
        categorized_ranked[category] = ranked

    # Get week date
    week_date = datetime.now().strftime('%B %d, %Y')

    # Generate enhanced category reports
    print("\n📝 Generating enhanced category reports...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for category, ranked_articles in categorized_ranked.items():
        filename = f"{category.lower().replace(' ', '_')}.md"
        content = generate_enhanced_category_report(category, ranked_articles, week_date)
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  ✓ {category}: {len(ranked_articles)} articles")

    # Identify top stories
    print("\n🌟 Identifying top stories...")
    top_stories = identify_top_stories(categorized_ranked)

    # Generate front page
    print("📰 Generating front page digest...")
    front_page = generate_front_page(categorized_ranked, top_stories, week_date)
    front_path = os.path.join(OUTPUT_DIR, "README.md")

    with open(front_path, "w", encoding="utf-8") as f:
        f.write(front_page)

    print(f"\n✅ All reports generated in '{OUTPUT_DIR}/'")
    print("\n📊 Results:")
    print(f"  • Front page: README.md")
    print(f"  • Category reports: {len(categorized_ranked)} files")
    print(f"  • Top story: {top_stories[0]['title'][:60]}... (score: {top_stories[0]['importance_score']}/10)")

    print("\n💡 Next steps:")
    print("  1. Review README.md for the weekly digest")
    print("  2. Check individual category reports")
    print("  3. Publish to your blog/newsletter!")


if __name__ == "__main__":
    main()