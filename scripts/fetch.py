import feedparser
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, urlunparse
import time


# ==============================
# 1️⃣ Feed URLs
# ==============================
feeds = [
    "https://www.tomshardware.com/feeds.xml",
    "https://www.cnx-software.com/feed/"
]


# ==============================
# 2️⃣ Fetch Articles
# ==============================
def fetch_feeds(feed_urls, debug=True):
    articles = []
    total_start = time.time()

    for idx, feed in enumerate(feed_urls, start=1):
        start_time = time.time()
        print(f"\n🔄 [{idx}/{len(feed_urls)}] Fetching feed: {feed}")

        try:
            parsed = feedparser.parse(feed)

            if parsed.bozo:
                print(f"⚠️  Warning: {feed} might have invalid RSS format. Error: {parsed.bozo_exception}")

            count = len(parsed.entries)
            print(f"✅ Retrieved {count} entries from {feed} in {time.time() - start_time:.2f}s")

            for entry in parsed.entries:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip() if "summary" in entry else ""
                articles.append({"title": title, "link": link, "summary": summary})

        except Exception as e:
            print(f"❌ Failed to fetch {feed}: {e}")

    total_time = time.time() - total_start
    print(f"\n⏱️  Total fetch time: {total_time:.2f}s")
    print(f"📦 Total articles collected: {len(articles)}")

    return articles


# ==============================
# 3️⃣ Cleaning Utilities
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
    clean = parsed._replace(query="")  # remove tracking params like ?utm_source
    return urlunparse(clean)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII chars
    return text


# ==============================
# 4️⃣ Clean + Deduplicate
# ==============================
def clean_and_deduplicate(articles):
    cleaned = []
    seen = set()

    for article in articles:
        link = clean_url(article.get("link", ""))
        title = normalize_text(clean_html(article.get("title", "")))
        summary = clean_text_boilerplate(normalize_text(clean_html(article.get("summary", ""))))

        if not title or not link:
            continue  # skip incomplete entries

        if link not in seen:
            seen.add(link)
            cleaned.append({
                "title": title,
                "link": link,
                "summary": summary
            })
    return cleaned


# ==============================
# 5️⃣ Run the Pipeline
# ==============================
if __name__ == "__main__":
    print("🔍 Fetching feeds...")
    raw_articles = fetch_feeds(feeds)
    print(f"📦 Collected {len(raw_articles)} raw articles.")

    print("🧹 Cleaning and deduplicating...")
    cleaned_articles = clean_and_deduplicate(raw_articles)
    print(f"✅ {len(cleaned_articles)} cleaned unique articles.")

    # Optional: save as JSON file
    with open("../data/cleaned_articles.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_articles, f, indent=2, ensure_ascii=False)

    print("💾 Saved to cleaned_articles.json")
    print("\nSample Output:\n")
    for art in cleaned_articles[:5]:
        print(f"- {art['title']}\n  {art['link']}\n")
