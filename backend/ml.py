"""
ML pipeline: LLM classification, sentiment/intensity scoring, summarizer.
Anthropic-only. No pgvector required.
"""

import os
import json
import math
from typing import Optional
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

_anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CHAT_MODEL = "claude-haiku-4-5-20251001"   # fast + cheap for scoring/classification
SUMMARY_MODEL = "claude-sonnet-4-6"         # best quality for summaries shown to judges
SIMILARITY_THRESHOLD = 0.65


# ---------------------------------------------------------------------------
# Issue classifier (LLM-based, no embeddings needed)
# ---------------------------------------------------------------------------

async def classify_post(text: str, issues: list[tuple[str, str]]) -> Optional[str]:
    """
    Ask Claude which existing issue this post belongs to.
    issues: list of (issue_id, issue_label)
    Returns matching issue_id or None (caller creates new issue).
    """
    if not issues:
        return None

    issue_list = "\n".join(f"{i+1}. {label}" for i, (_, label) in enumerate(issues))
    try:
        resp = await _anthropic.messages.create(
            model=CHAT_MODEL,
            max_tokens=10,
            system=(
                "You are a topic classifier. Given a student post and a numbered list of campus issues, "
                "respond with ONLY the number of the best matching issue. "
                "If the post does not fit any issue well, respond with '0'. No explanation, just the number."
            ),
            messages=[{"role": "user", "content": f"ISSUES:\n{issue_list}\n\nPOST: {text}"}],
        )
        idx = int(resp.content[0].text.strip()) - 1
        if 0 <= idx < len(issues):
            return issues[idx][0]
        return None
    except Exception:
        return None


async def label_new_issue(text: str) -> str:
    """Generate a short label (3-6 words) for a brand-new issue."""
    try:
        resp = await _anthropic.messages.create(
            model=CHAT_MODEL,
            max_tokens=20,
            system="You create concise campus issue labels (3-6 words, title case). Return ONLY the label, nothing else.",
            messages=[{"role": "user", "content": text}],
        )
        return resp.content[0].text.strip()
    except Exception:
        return "General Campus Issue"


# ---------------------------------------------------------------------------
# Lean detection (private — result stored, never returned via API)
# ---------------------------------------------------------------------------

async def infer_lean(text: str) -> float:
    """Privately classify political lean. Never exposed via API."""
    try:
        resp = await _anthropic.messages.create(
            model=CHAT_MODEL,
            max_tokens=20,
            system=(
                "You are a private political lean classifier. "
                "Return ONLY a JSON object: {\"lean\": <float>} "
                "where -1.0 = strongly progressive, 0.0 = centrist, +1.0 = strongly conservative. "
                "Base the score solely on the text. Do not explain."
            ),
            messages=[{"role": "user", "content": text}],
        )
        return float(json.loads(resp.content[0].text.strip())["lean"])
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Sentiment + intensity scoring
# ---------------------------------------------------------------------------

async def score_post(text: str) -> tuple[float, float]:
    """Return (sentiment, intensity) for a post."""
    try:
        resp = await _anthropic.messages.create(
            model=CHAT_MODEL,
            max_tokens=30,
            system=(
                "You are a sentiment and intensity scorer. "
                "Return ONLY a JSON object: {\"sentiment\": <float -1 to 1>, \"intensity\": <float 1 to 10>}. "
                "sentiment: -1 = very negative, 0 = neutral, 1 = very positive. "
                "intensity: 1 = barely matters, 10 = deeply personal/urgent. Do not explain."
            ),
            messages=[{"role": "user", "content": text}],
        )
        data = json.loads(resp.content[0].text.strip())
        return max(-1.0, min(1.0, float(data["sentiment"]))), max(1.0, min(10.0, float(data["intensity"])))
    except Exception:
        return 0.0, 5.0


# ---------------------------------------------------------------------------
# Rank score
# ---------------------------------------------------------------------------

def compute_rank_score(post_volume: int, intensity_avg: float, recency_weight: float) -> float:
    return (post_volume * 0.4) + (intensity_avg * 0.4) + (recency_weight * 0.2)


def recency_weight(latest_post_ts, now=None) -> float:
    from datetime import datetime, timezone
    if now is None:
        now = datetime.now(timezone.utc)
    if latest_post_ts.tzinfo is None:
        latest_post_ts = latest_post_ts.replace(tzinfo=timezone.utc)
    age_days = (now - latest_post_ts).total_seconds() / 86400
    return max(0.0, 10.0 * math.exp(-age_days / 3))


# ---------------------------------------------------------------------------
# LLM Summarizer
# ---------------------------------------------------------------------------

_SUMMARIZER_SYSTEM = """You are a neutral civic journalist. Your job is to summarize student opinions \
on a campus issue fairly and completely. Do not favor any side. Do not editorialize. \
Represent every major viewpoint with equal weight and clarity. \
Use plain, accessible language. Do not use political labels.

Return ONLY valid JSON matching this exact schema:
{
  "summary": "<2 sentences, factual only>",
  "side_a_points": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
  "side_b_points": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
  "shared_concerns": ["<point 1>", "<point 2>"],
  "human_concern": "<1 sentence capturing the shared human concern>"
}

side_a_points: 3-5 bullets for the strongly-frustrated/change-demanding perspective.
side_b_points: 3-5 bullets for the context/complexity/counter perspective.
shared_concerns: 1-3 points almost everyone agrees on."""


async def summarize_issue(label: str, posts: list[str]) -> dict:
    combined = "\n---\n".join(posts[:80])
    try:
        resp = await _anthropic.messages.create(
            model=SUMMARY_MODEL,
            max_tokens=1024,
            system=_SUMMARIZER_SYSTEM,
            messages=[{"role": "user", "content": f"ISSUE: {label}\n\nPOSTS:\n{combined}"}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return {
            "summary": data.get("summary", ""),
            "side_a_points": data.get("side_a_points", []),
            "side_b_points": data.get("side_b_points", []),
            "shared_concerns": data.get("shared_concerns", []),
            "human_concern": data.get("human_concern", ""),
        }
    except Exception as e:
        return {
            "summary": f"Summary unavailable: {e}",
            "side_a_points": [], "side_b_points": [],
            "shared_concerns": [], "human_concern": "",
        }
