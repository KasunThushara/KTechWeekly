"""
Summarize & Tag - Works with Agentic Pipeline Output
Much simpler since categorization is already done
"""
import json
import time
import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

INPUT_FILE = "data/curated_articles.json"
OUTPUT_FILE = "data/final_articles.json"
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2.0"))

client = None


def init_groq_client():
    """Initialize Groq client."""
    global client
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("\n❌ GROQ_API_KEY not found!")
        return False

    try:
        client = Groq(api_key=api_key)
        # Test
        client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        print(f"✅ Connected to Groq API")
        return True
    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return False


def enhance_article(article):
    """
    Use AI to:
    1. Create better summary (2-3 sentences)
    2. Generate a key insight
    """
    prompt = f"""
Title: {article['title']}
Original Summary: {article['summary']}

Tasks:
1. Write a clear, informative 2-3 sentence summary
2. Generate ONE key insight (max 12 words) that captures why this matters

Output ONLY valid JSON:
{{
  "summary": "...",
  "insight": "..."
}}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        text = response.choices[0].message.content.strip()

        # Extract JSON
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            json_text = text[start:end]
            result = json.loads(json_text)

            return {
                **article,
                'summary': result.get('summary', article['summary']),
                'insight': result.get('insight', '')
            }

    except Exception as e:
        print(f"  ⚠️  AI enhancement failed: {e}")

    # Return original if AI fails
    return article


def main():
    print("=" * 70)
    print("✨ AI ARTICLE ENHANCEMENT")
    print("=" * 70)

    # Check Groq
    if not init_groq_client():
        return

    # Load curated articles
    if not Path(INPUT_FILE).exists():
        print(f"\n❌ {INPUT_FILE} not found!")
        print("   Run fetch_new.py first")
        return

    with open(INPUT_FILE, 'r') as f:
        articles = json.load(f)

    print(f"\n📚 Enhancing {len(articles)} articles with AI...\n")

    enhanced = []
    for i, article in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] {article['title'][:60]}...")

        result = enhance_article(article)
        enhanced.append(result)

        # Rate limiting
        if i < len(articles):  # Don't sleep after last one
            time.sleep(REQUEST_DELAY)

    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(enhanced, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"✅ Saved {len(enhanced)} enhanced articles to {OUTPUT_FILE}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()