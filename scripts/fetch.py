import feedparser
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, urlunparse
import time
from datetime import datetime, timedelta
import hashlib
from pathlib import Path

# ==============================
# 1️⃣ Feed URLs - Narrowed Focus
# ==============================
feeds = [
    "https://www.tomshardware.com/feeds.xml",
    "https://www.cnx-software.com/feed/"
]

# Keywords to focus on (narrowed topics)
FOCUS_KEYWORDS = [
    # AI/ML specific
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "transformer", "inference",

    # Edge computing
    "edge ai", "edge computing", "tinyml", "onnx", "quantization",

    # Hardware specific
    "nvidia", "raspberry pi", "rockchip", "jetson", "coral", "tpu",
    "risc-v", "arm cortex", "fpga",

    # Semiconductors
    "chip", "semiconductor", "foundry", "tsmc", "asml", "lithography",
    "processor", "soc", "gpu", "npu"
]

# Keywords to exclude (noise reduction)
EXCLUDE_KEYWORDS = [
    "coupon", "deal", "discount", "sale", "price drop", "giveaway",
    "review roundup", "weekly deals", "best buy", "amazon prime"
]

PROJECT_ROOT = Path(__file__).parent.parent
HISTORY_FILE = PROJECT_ROOT / "data" / "article_history.json"


# ==============================
# 2️⃣ Article History Manager
# ==============================
class ArticleHistory:
    """Tracks seen articles to prevent duplicates across weeks."""

    def __init__(self, history_file, max_age_days=30):
        self.history_file = Path(history_file)
        self.max_age_days = max_age_days
        self.history = self.load_history()

    def load_history(self):
        """Load article history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_history(self):
        """Save article history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)

    def cleanup_old_entries(self):
        """Remove entries older than max_age_days."""
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        cutoff_timestamp = cutoff_date.timestamp()

        old_count = len(self.history)
        self.history = {
            url: data for url, data in self.history.items()
            if data.get('timestamp', 0) > cutoff_timestamp
        }
        removed = old_count - len(self.history)
        if removed > 0:
            print(f"🧹 Cleaned up {removed} old entries (>{self.max_age_days} days)")

    def get_article_hash(self, title, url):
        """Generate unique hash for article."""
        content = f"{title.lower()}{url}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_seen(self, title, url):
        """Check if article was seen before."""
        url = clean_url(url)

        # Check by URL
        if url in self.history:
            return True

        # Check by title hash (for same article on different URLs)
        article_hash = self.get_article_hash(title, url)
        for data in self.history.values():
            if data.get('hash') == article_hash:
                return True

        return False

    def add_article(self, title, url):
        """Add article to history."""
        url = clean_url(url)
        self.history[url] = {
            'title': title,
            'hash': self.get_article_hash(title, url),
            'timestamp': datetime.now().timestamp(),
            'date': datetime.now().isoformat()
        }


# ==============================
# 3️⃣ Relevance Filter (Agentic Decision Making)
# ==============================
def calculate_relevance_score(article):
    """
    Calculate relevance score (0-100) based on keywords and content.
    This acts as an autonomous agent deciding what's relevant.
    """
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    content = f"{title} {summary}"

    score = 0

    # Check for focused keywords (bonus points)
    focus_matches = sum(1 for keyword in FOCUS_KEYWORDS if keyword in content)
    score += focus_matches * 10

    # Penalize excluded keywords
    exclude_matches = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in content)
    score -= exclude_matches * 20

    # Bonus for technical depth indicators
    technical_indicators = [
        'architecture', 'benchmark', 'performance', 'specification',
        'announcement', 'release', 'development', 'breakthrough'
    ]
    tech_matches = sum(1 for indicator in technical_indicators if indicator in content)
    score += tech_matches * 5

    # Ensure score is within 0-100
    return max(0, min(100, score))


def is_relevant_article(article, min_score=20):
    """
    Autonomous decision: Should we include this article?
    Returns (bool, score, reason)
    """
    score = calculate_relevance_score(article)

    if score < min_score:
        return False, score, "Low relevance score"

    title = article.get('title', '').lower()

    # Hard filter: Exclude promotional content
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in title:
            return False, score, f"Excluded keyword: {keyword}"

    return True, score, "Passed relevance check"


# ==============================
# 4️⃣ Fetch Articles
# ==============================
def fetch_feeds(feed_urls, history, debug=True):
    articles = []
    total_start = time.time()

    for idx, feed in enumerate(feed_urls, start=1):
        start_time = time.time()
        print(f"\n📄 [{idx}/{len(feed_urls)}] Fetching feed: {feed}")

        try:
            parsed = feedparser.parse(feed)

            if parsed.bozo:
                print(f"⚠️  Warning: {feed} might have invalid RSS format")

            count = len(parsed.entries)
            print(f"✅ Retrieved {count} entries from {feed} in {time.time() - start_time:.2f}s")

            for entry in parsed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip() if "summary" in entry else ""

                article = {"title": title, "link": link, "summary": summary}

                # Agent decision 1: Is this relevant?
                is_relevant, score, reason = is_relevant_article(article)

                if not is_relevant:
                    if debug:
                        print(f"   ⊘ Filtered: {title[:50]}... (Reason: {reason})")
                    continue

                # Agent decision 2: Have we seen this before?
                if history.is_seen(title, link):
                    if debug:
                        print(f"   ↻ Duplicate: {title[:50]}...")
                    continue

                # Add relevance score to article
                article['relevance_score'] = score
                articles.append(article)

                if debug:
                    print(f"   ✓ Added: {title[:50]}... (Score: {score})")

        except Exception as e:
            print(f"❌ Failed to fetch {feed}: {e}")

    total_time = time.time() - total_start
    print(f"\n⏱️  Total fetch time: {total_time:.2f}s")
    print(f"📦 New relevant articles: {len(articles)}")

    return articles


# ==============================
# 5️⃣ Cleaning Utilities
# ==============================
def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def clean_text_boilerplate(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(Read more|Click here|Follow us on.*)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    clean = parsed._replace(query="")  # remove tracking params
    return urlunparse(clean)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII chars
    return text


# ==============================
# 6️⃣ Clean Articles
# ==============================
def clean_articles(articles):
    cleaned = []

    for article in articles:
        link = clean_url(article.get("link", ""))
        title = normalize_text(clean_html(article.get("title", "")))
        summary = clean_text_boilerplate(normalize_text(clean_html(article.get("summary", ""))))
        relevance_score = article.get("relevance_score", 0)

        if not title or not link:
            continue

        cleaned.append({
            "title": title,
            "link": link,
            "summary": summary,
            "relevance_score": relevance_score,
            "fetched_date": datetime.now().isoformat()
        })

    return cleaned


# ==============================
# 7️⃣ Run the Pipeline
# ==============================
if __name__ == "__main__":
    print("🔍 Fetching feeds with intelligent filtering...\n")

    # Initialize article history
    history = ArticleHistory(HISTORY_FILE, max_age_days=30)
    history.cleanup_old_entries()
    print(f"📚 Tracking {len(history.history)} articles in history\n")

    # Fetch new articles
    raw_articles = fetch_feeds(feeds, history)

    if not raw_articles:
        print("\n⚠️  No new relevant articles found!")
        print("   This could mean:")
        print("   1. All articles were duplicates")
        print("   2. No articles matched relevance criteria")
        print("   3. Check if feeds are accessible")
    else:
        print(f"\n🧹 Cleaning {len(raw_articles)} articles...")
        cleaned_articles = clean_articles(raw_articles)
        print(f"✅ {len(cleaned_articles)} cleaned articles ready")

        # Update history with new articles
        for article in cleaned_articles:
            history.add_article(article['title'], article['link'])

        history.save_history()
        print(f"💾 Updated history (now tracking {len(history.history)} articles)")

        # Save as JSON file
        output_dir = PROJECT_ROOT / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "cleaned_articles.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_articles, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved to {output_file}")

        # Show stats
        print("\n📊 Relevance Score Distribution:")
        scores = [a['relevance_score'] for a in cleaned_articles]
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"   Average: {avg_score:.1f}")
            print(f"   Range: {min(scores)} - {max(scores)}")

        print("\n✨ Sample Output (Top 5 by relevance):\n")
        sorted_articles = sorted(cleaned_articles, key=lambda x: x['relevance_score'], reverse=True)
        for i, art in enumerate(sorted_articles[:5], 1):
            print(f"{i}. [{art['relevance_score']}] {art['title']}")
            print(f"   {art['link']}\n")