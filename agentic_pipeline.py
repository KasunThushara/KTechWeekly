"""
AGENTIC NEWS CURATOR - Complete Redesign
A self-managing system that makes autonomous decisions about content quality and organization
"""
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# CORE CONFIGURATION - Simple & Focused
# ============================================================================

@dataclass
class Category:
    """Represents a content category."""
    name: str
    emoji: str
    description: str
    keywords: List[str]
    min_keyword_matches: int = 2  # Minimum keywords to match for assignment


# Define ONLY 5 core categories - keeping it focused
CATEGORIES = [
    Category(
        name="AI & ML",
        emoji="🤖",
        description="Artificial Intelligence and Machine Learning",
        keywords=[
            "ai", "artificial intelligence", "machine learning", "ml", "neural",
            "deep learning", "llm", "gpt", "transformer", "model", "training",
            "inference", "generative", "chatbot", "dataset"
        ],
        min_keyword_matches=1  # Changed from 2 to 1
    ),
    Category(
        name="Hardware",
        emoji="💻",
        description="Computing hardware and development boards",
        keywords=[
            "raspberry pi", "arduino", "esp32", "hardware", "board", "sbc",
            "jetson", "coral", "development board", "microcontroller",
            "fpga", "risc-v", "processor", "cpu", "embedded", "pc", "desktop",
            "laptop", "computer", "server", "workstation", "review"
        ],
        min_keyword_matches=1
    ),
    Category(
        name="GPUs",
        emoji="🎮",
        description="Graphics cards and compute accelerators",
        keywords=[
            "nvidia", "amd", "intel arc", "gpu", "graphics card", "rtx",
            "geforce", "radeon", "cuda", "tensor", "accelerator", "gaming",
            "graphics", "video card"
        ],
        min_keyword_matches=1
    ),
    Category(
        name="Semiconductors",
        emoji="⚡",
        description="Chip manufacturing and design",
        keywords=[
            "semiconductor", "chip", "tsmc", "fab", "foundry", "wafer",
            "lithography", "nanometer", "nm", "asml", "euv", "manufacturing",
            "rockchip", "qualcomm", "mediatek", "arm", "intel foundry",
            "5g", "wifi", "wireless", "networking"  # Added networking keywords
        ],
        min_keyword_matches=1
    ),
    Category(
        name="Tech News",
        emoji="📰",
        description="Industry news and product launches",
        keywords=[
            "announced", "launch", "release", "unveiled", "partnership",
            "acquisition", "breakthrough", "innovation", "startup", "funding",
            "review", "tested", "available"  # Added common words
        ],
        min_keyword_matches=1
    ),
]

# ============================================================================
# AGENT 1: Content Quality Evaluator
# ============================================================================

class QualityAgent:
    """Autonomous agent that evaluates article quality and relevance."""

    # Quality signals (positive)
    QUALITY_SIGNALS = [
        "announced", "released", "breakthrough", "innovation", "launched",
        "unveiled", "development", "research", "technical", "architecture",
        "benchmark", "performance", "specification", "analysis", "review"
    ]

    # Noise signals (negative)
    NOISE_SIGNALS = [
        "deal", "discount", "coupon", "sale", "price drop", "black friday",
        "prime day", "giveaway", "contest", "affiliate", "sponsored",
        "click here", "limited time", "act now", "hurry"
    ]

    def evaluate(self, article: Dict) -> tuple[bool, int, str]:
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()

        score = 0

        # Positive signals
        quality_matches = sum(1 for signal in self.QUALITY_SIGNALS if signal in text)
        score += quality_matches * 5

        # Negative signals
        noise_matches = sum(1 for signal in self.NOISE_SIGNALS if signal in text)
        score -= noise_matches * 10

        # Length bonus
        if len(text) > 200:
            score += 5

        # CHANGE THESE THRESHOLDS:
        if score < -20:  # Was 0, now -20 (more lenient)
            return False, score, "Promotional or low-quality content"

        if score < 0:  # Was 10, now 0 (more lenient)
            return False, score, "Insufficient quality signals"

        if noise_matches > 2:  # Was >0, now >2 (allow some promotional words)
            return False, score, f"Contains promotional keywords ({noise_matches})"

        return True, score, "Meets quality standards"


# ============================================================================
# AGENT 2: Smart Categorizer
# ============================================================================

class CategorizerAgent:
    """Autonomous agent that assigns articles to appropriate categories."""

    def __init__(self, categories: List[Category]):
        self.categories = categories

    def categorize(self, article: Dict) -> List[str]:
        """
        Assign article to 1-2 most relevant categories.

        Returns:
            List of category names (max 2)
        """
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()

        # Score each category
        category_scores = []

        for category in self.categories:
            matches = sum(1 for keyword in category.keywords if keyword in text)

            if matches >= category.min_keyword_matches:
                # Weight score by keyword relevance
                score = matches * 10

                # Title bonus (keywords in title are more important)
                title = article.get('title', '').lower()
                title_matches = sum(1 for keyword in category.keywords if keyword in title)
                score += title_matches * 5

                category_scores.append((category.name, score))

        # Sort by score and take top 1-2
        category_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top categories
        result = [cat for cat, score in category_scores[:2]]

        # Default to Tech News if no match
        if not result:
            result = ["Tech News"]

        return result


# ============================================================================
# AGENT 3: Deduplication Agent
# ============================================================================

class DeduplicationAgent:
    """Autonomous agent that identifies and removes duplicate content."""

    def __init__(self, history_file: Path, retention_days: int = 30):
        self.history_file = history_file
        self.retention_days = retention_days
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """Load deduplication history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_history(self):
        """Save deduplication history."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _cleanup_old_entries(self):
        """Remove entries older than retention period."""
        cutoff = (datetime.now() - timedelta(days=self.retention_days)).timestamp()

        old_count = len(self.history)
        self.history = {
            url: data for url, data in self.history.items()
            if data.get('timestamp', 0) > cutoff
        }

        removed = old_count - len(self.history)
        if removed > 0:
            print(f"  🧹 Cleaned {removed} old history entries")

    def _get_fingerprint(self, article: Dict) -> str:
        """Generate content fingerprint for similarity detection."""
        # Use first 100 chars of title for similarity
        title = article.get('title', '')[:100].lower()
        # Remove common words
        for word in ['the', 'a', 'an', 'and', 'or', 'but', 'with', 'for']:
            title = title.replace(f' {word} ', ' ')

        return hashlib.md5(title.encode()).hexdigest()

    def is_duplicate(self, article: Dict) -> tuple[bool, str]:
        """
        Check if article is a duplicate.

        Returns:
            (is_duplicate, reason)
        """
        url = article.get('link', '')

        # Check exact URL match
        if url in self.history:
            return True, "Exact URL match"

        # Check content fingerprint
        fingerprint = self._get_fingerprint(article)
        for existing_url, data in self.history.items():
            if data.get('fingerprint') == fingerprint:
                return True, f"Similar content (fingerprint match)"

        return False, "Not a duplicate"

    def mark_as_seen(self, article: Dict):
        """Mark article as seen in history."""
        url = article.get('link', '')
        self.history[url] = {
            'title': article.get('title', ''),
            'fingerprint': self._get_fingerprint(article),
            'timestamp': datetime.now().timestamp(),
            'date': datetime.now().isoformat()
        }

    def save(self):
        """Save history and cleanup old entries."""
        self._cleanup_old_entries()
        self._save_history()


# ============================================================================
# ORCHESTRATOR: Agentic Pipeline
# ============================================================================

class AgenticPipeline:
    """Orchestrates all agents to curate content autonomously."""

    def __init__(self):
        self.quality_agent = QualityAgent()
        self.categorizer_agent = CategorizerAgent(CATEGORIES)
        self.dedup_agent = DeduplicationAgent(
            Path("data/dedup_history.json"),
            retention_days=30
        )

        self.stats = {
            'total_fetched': 0,
            'filtered_low_quality': 0,
            'filtered_duplicates': 0,
            'accepted': 0,
            'by_category': {cat.name: 0 for cat in CATEGORIES}
        }

    def process_article(self, article: Dict) -> Optional[Dict]:
        """
        Process a single article through all agents.

        Returns:
            Processed article or None if filtered
        """
        self.stats['total_fetched'] += 1

        # Agent 1: Quality Check
        is_quality, quality_score, quality_reason = self.quality_agent.evaluate(article)

        if not is_quality:
            self.stats['filtered_low_quality'] += 1
            print(f"  ⊘ Quality: {article.get('title', '')[:60]}... ({quality_reason})")
            return None

        # Agent 2: Deduplication Check
        is_dup, dup_reason = self.dedup_agent.is_duplicate(article)

        if is_dup:
            self.stats['filtered_duplicates'] += 1
            print(f"  ↻ Duplicate: {article.get('title', '')[:60]}... ({dup_reason})")
            return None

        # Agent 3: Categorization
        categories = self.categorizer_agent.categorize(article)

        # Accept article
        self.stats['accepted'] += 1
        for cat in categories:
            self.stats['by_category'][cat] = self.stats['by_category'].get(cat, 0) + 1

        # Mark as seen
        self.dedup_agent.mark_as_seen(article)

        # Build processed article
        processed = {
            'title': article.get('title', ''),
            'summary': article.get('summary', ''),
            'link': article.get('link', ''),
            'categories': categories,
            'quality_score': quality_score,
            'processed_date': datetime.now().isoformat()
        }

        print(f"  ✓ Accepted: {article.get('title', '')[:60]}... ({', '.join(categories)})")

        return processed

    def process_batch(self, articles: List[Dict]) -> List[Dict]:
        """Process a batch of articles."""
        print(f"\n🤖 Agentic Pipeline Processing {len(articles)} articles...\n")

        processed = []
        for article in articles:
            result = self.process_article(article)
            if result:
                processed.append(result)

        # Save deduplication history
        self.dedup_agent.save()

        return processed

    def print_stats(self):
        """Print processing statistics."""
        print(f"\n{'=' * 70}")
        print(f"📊 AGENTIC PIPELINE STATISTICS")
        print(f"{'=' * 70}")
        print(f"Total Fetched:       {self.stats['total_fetched']}")
        print(f"Filtered (Quality):  {self.stats['filtered_low_quality']}")
        print(f"Filtered (Duplicate): {self.stats['filtered_duplicates']}")
        print(f"Accepted:            {self.stats['accepted']}")
        print(f"\nCategory Distribution:")
        for cat_name, count in sorted(self.stats['by_category'].items()):
            if count > 0:
                emoji = next((c.emoji for c in CATEGORIES if c.name == cat_name), "📰")
                print(f"  {emoji} {cat_name}: {count}")
        print(f"{'=' * 70}\n")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'AgenticPipeline',
    'CATEGORIES',
    'Category'
]