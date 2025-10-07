import json
import time
from ollama import chat
import os

INPUT_FILE = "../data/cleaned_articles.json"
OUTPUT_FILE = "../data/abstracted_articles.json"
MODEL = "gemma3:4b"

# Predefined categories
CATEGORIES = ["AI", "Machine Learning", "NVIDIA", "Raspberry Pi",
              "Rockchip", "Semiconductors", "Edge AI", "Hardware", "Trends"]


def check_ollama_connection():
    """Verify Ollama is running before processing."""
    try:
        response = chat(model=MODEL, messages=[{"role": "user", "content": "test"}])
        return True
    except Exception as e:
        print(f"\n❌ Cannot connect to Ollama: {e}")
        print("\n💡 Please start Ollama first:")
        print("   1. Open a terminal and run: ollama serve")
        print("   2. Or run: ollama run gemma3:4b")
        print("   3. Then run this script again\n")
        return False


def summarize_article(article):
    """Use Ollama local LLM to summarize & tag article."""
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
        response = chat(model=MODEL, messages=[{"role": "user", "content": content}])
        text = response.message.content.strip()

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
    """Create a fallback result when LLM fails."""
    return {
        "title": article['title'],
        "summary": summary_text[:300] if summary_text else article['summary'][:300],
        "tags": [],
        "link": article.get('link', '')
    }


def main():
    # Check Ollama connection first
    if not check_ollama_connection():
        return

    # Load articles
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file '{INPUT_FILE}' not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"\n📚 Processing {len(articles)} articles...")

    results = []
    failed = 0

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
        time.sleep(0.5)

    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(results)} articles to '{OUTPUT_FILE}'")
    if failed > 0:
        print(f"⚠️  {failed} articles had issues (no tags or errors)")


if __name__ == "__main__":
    main()