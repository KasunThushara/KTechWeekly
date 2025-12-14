import json
import time
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

INPUT_FILE = os.getenv("INPUT_FILE", "data/cleaned_articles.json")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "data/abstracted_articles.json")
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2.0"))

# Predefined categories
CATEGORIES = ["AI", "Machine Learning", "NVIDIA", "Raspberry Pi",
              "Rockchip", "Semiconductors", "Edge AI", "Hardware", "Trends"]

# Initialize Groq client
client = None


def init_groq_client():
    """Initialize Groq client with API key."""
    global client
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("\n❌ GROQ_API_KEY not found in environment!")
        print("\n💡 Please set your Groq API key:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: GROQ_API_KEY=your_api_key_here")
        print("   3. Or set it as an environment variable\n")
        return False

    try:
        client = Groq(api_key=api_key)
        # Test connection
        client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        print(f"✅ Connected to Groq API using model: {MODEL}")
        return True
    except Exception as e:
        print(f"\n❌ Cannot connect to Groq API: {e}")
        print("\n💡 Please check:")
        print("   1. Your API key is valid")
        print("   2. You have internet connection")
        print("   3. The model name is correct\n")
        return False


def summarize_article(article):
    """Use Groq API to summarize & tag article."""
    content = f"""
Title: {article['title']}
Text: {article['summary']}

Task:
1. Summarize in 2–3 sentences clearly.
2. Identify the best-matching categories from this list:
   {', '.join(CATEGORIES)}
3. Output ONLY valid JSON with no extra text, like this:
{{
  "title": "...",
  "summary": "...",
  "tags": ["AI", "NVIDIA"]
}}

DO NOT include a "link" field - I will add it separately.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": content}],
            temperature=0.7,
            max_tokens=500
        )

        text = response.choices[0].message.content.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            json_text = text[start:end]
            result = json.loads(json_text)

            # Always use the original link from input
            result["link"] = article.get('link', '')

            # Ensure other required fields exist
            if "title" not in result:
                result["title"] = article['title']
            if "summary" not in result:
                result["summary"] = article.get('summary', '')
            if "tags" not in result:
                result["tags"] = []

            return result
        else:
            raise ValueError("No JSON object found in response")

    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error for '{article['title'][:50]}': {e}")
        return create_fallback_result(article, text)
    except Exception as e:
        print(f"⚠️  Error summarizing '{article['title'][:50]}': {e}")
        return create_fallback_result(article)


def create_fallback_result(article, summary_text=None):
    """Create a fallback result when API fails."""
    return {
        "title": article['title'],
        "summary": summary_text[:300] if summary_text else article['summary'][:300],
        "tags": [],
        "link": article.get('link', '')
    }


def main():
    print("=" * 70)
    print("🤖 AI-Powered Article Summarization & Tagging (Groq API)")
    print("=" * 70)

    # Initialize Groq client
    if not init_groq_client():
        return

    # Load articles
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ Input file '{INPUT_FILE}' not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"\n📚 Processing {len(articles)} articles...")
    print(f"⏱️  Estimated time: ~{len(articles) * REQUEST_DELAY:.0f} seconds\n")

    results = []
    failed = 0
    start_time = time.time()

    for i, art in enumerate(articles, 1):
        print(f"🧠 [{i}/{len(articles)}] {art['title'][:70]}...", end=" ")

        result = summarize_article(art)
        if result:
            results.append(result)
            if result['tags']:
                print(f"✓ ({', '.join(result['tags'][:3])})")
            else:
                print("✓ (no tags)")
                failed += 1
        else:
            print("✗")
            failed += 1

        # Rate limiting
        time.sleep(REQUEST_DELAY)

    # Save results
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - start_time

    print(f"\n{'=' * 70}")
    print(f"✅ Saved {len(results)} articles to '{OUTPUT_FILE}'")
    print(f"⏱️  Total time: {elapsed:.1f} seconds")
    if failed > 0:
        print(f"⚠️  {failed} articles had issues (no tags or errors)")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()