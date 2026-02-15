"""
Fetch Script - Uses Agentic Pipeline
Completely rewritten to be simple and effective
"""
import feedparser
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, urlunparse
import time
from pathlib import Path
import sys

# Add parent directory to path to import agentic_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))
from agentic_pipeline import AgenticPipeline

# ============================================================================
# RSS FEEDS - Keep focused on quality sources
# ============================================================================

FEEDS = [
    "https://www.tomshardware.com/feeds.xml",
    "https://www.cnx-software.com/feed/"
]


# ============================================================================
# UTILITIES
# ============================================================================

def clean_html(raw_html: str) -> str:
    """Remove HTML tags from text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def clean_url(url: str) -> str:
    """Remove tracking parameters from URL."""
    parsed = urlparse(url)
    clean = parsed._replace(query="")
    return urlunparse(clean)


def normalize_text(text: str) -> str:
    """Normalize text by removing non-ASCII and extra whitespace."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII
    text = re.sub(r"\s+", " ", text)  # Normalize whitespace
    return text


# ============================================================================
# FETCH
# ============================================================================

def fetch_feeds(feed_urls):
    """Fetch articles from RSS feeds."""
    print(f"📡 Fetching from {len(feed_urls)} RSS feeds...\n")

    all_articles = []

    for idx, feed_url in enumerate(feed_urls, 1):
        print(f"[{idx}/{len(feed_urls)}] Fetching: {feed_url}")

        try:
            start_time = time.time()
            parsed = feedparser.parse(feed_url)

            if parsed.bozo:
                print(f"  ⚠️  Warning: Feed may have invalid format")

            count = len(parsed.entries)
            elapsed = time.time() - start_time
            print(f"  ✓ Retrieved {count} entries in {elapsed:.2f}s")

            for entry in parsed.entries:
                # Extract raw data
                article = {
                    'title': normalize_text(clean_html(entry.get('title', ''))),
                    'summary': normalize_text(clean_html(entry.get('summary', ''))),
                    'link': clean_url(entry.get('link', ''))
                }

                # Only add if we have minimum required fields
                if article['title'] and article['link']:
                    all_articles.append(article)

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n📦 Collected {len(all_articles)} raw articles\n")
    return all_articles


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("🚀 AGENTIC NEWS FETCHER")
    print("=" * 70)

    # Step 1: Fetch raw articles
    raw_articles = fetch_feeds(FEEDS)

    if not raw_articles:
        print("\n⚠️  No articles fetched. Check RSS feeds.")
        return

    # Step 2: Process through agentic pipeline
    pipeline = AgenticPipeline()
    curated_articles = pipeline.process_batch(raw_articles)

    # Step 3: Show statistics
    pipeline.print_stats()

    # Step 4: Save results
    if curated_articles:
        output_dir = Path("data")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "curated_articles.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(curated_articles, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(curated_articles)} curated articles to {output_file}")

        # Show sample
        print(f"\n📝 Sample Articles:\n")
        for i, article in enumerate(curated_articles[:3], 1):
            print(f"{i}. [{article.get('quality_score', 0)}] {article['title']}")
            print(f"   Categories: {', '.join(article['categories'])}")
            print(f"   {article['link']}\n")
    else:
        print("⚠️  No articles passed quality and deduplication filters.")
        print("   This is normal if:")
        print("   - All articles were already seen recently")
        print("   - All articles were promotional/low-quality")
        print("   - RSS feeds had no new content")

    print("=" * 70)


if __name__ == "__main__":
    main()