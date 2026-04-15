"""
ML pipeline: embeddings, issue classification, sentiment/intensity scoring, LLM summarizer.
"""

import os
import json
import math
from typing import Optional
import numpy as np
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "claude-sonnet-4-6"
SIMILARITY_THRESHOLD = 0.65


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

async def embed_text(text: str) -> list[float]:
    """Return a 1536-dim embedding vector for the given text."""
    response = await _client.embeddings.create(
        model=EMBED_MODEL,
        input=text.replace("\n", " "),
    )
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


# ---------------------------------------------------------------------------
# Lean detection (private — result stored, never returned via API)
# ---------------------------------------------------------------------------

_LEAN_SYSTEM = (
    "You are a private political lean classifier. "
    "Return ONLY a JSON object: {\"lean\": <float>} "
    "where -1.0 = strongly progressive, 0.0 = centrist, +1.0 = strongly conservative. "
    "Base the score solely on the text. Do not explain."
)


async def infer_lean(text: str) -> float:
    """Privately classify political lean. Never exposed via API."""
    try:
        resp = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _LEAN_SYSTEM},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=20,
        )
        raw = resp.choices[0].message.content.strip()
        return float(json.loads(raw)["lean"])
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Sentiment + intensity scoring
# ---------------------------------------------------------------------------

_SCORE_SYSTEM = (
    "You are a sentiment and intensity scorer. "
    "Return ONLY a JSON object: {\"sentiment\": <float -1 to 1>, \"intensity\": <float 1 to 10>}. "
    "sentiment: -1 = very negative, 0 = neutral, 1 = very positive. "
    "intensity: 1 = barely matters, 10 = deeply personal/urgent. Do not explain."
)


async def score_post(text: str) -> tuple[float, float]:
    """Return (sentiment, intensity) for a post."""
    try:
        resp = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SCORE_SYSTEM},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=30,
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        sentiment = max(-1.0, min(1.0, float(data["sentiment"])))
        intensity = max(1.0, min(10.0, float(data["intensity"])))
        return sentiment, intensity
    except Exception:
        return 0.0, 5.0


# ---------------------------------------------------------------------------
# Issue classifier
# ---------------------------------------------------------------------------

async def classify_post(
    post_embedding: list[float],
    issue_embeddings: list[tuple[str, list[float]]],  # [(issue_id, embedding)]
) -> Optional[str]:
    """
    Return the best-matching issue_id if cosine similarity > SIMILARITY_THRESHOLD,
    else None (caller should create a new issue).
    """
    best_id, best_sim = None, -1.0
    for issue_id, emb in issue_embeddings:
        sim = cosine_similarity(post_embedding, emb)
        if sim > best_sim:
            best_sim, best_id = sim, issue_id
    if best_sim >= SIMILARITY_THRESHOLD:
        return best_id
    return None


async def label_new_issue(text: str) -> str:
    """Generate a short label (3-6 words) for a brand-new issue."""
    try:
        resp = await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You create concise campus issue labels (3-6 words, title case). "
                        "Return ONLY the label, nothing else."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=20,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "General Campus Issue"


# ---------------------------------------------------------------------------
# Rank score
# ---------------------------------------------------------------------------

def compute_rank_score(post_volume: int, intensity_avg: float, recency_weight: float) -> float:
    """rank_score = (post_volume × 0.4) + (intensity_avg × 0.4) + (recency_weight × 0.2)"""
    return (post_volume * 0.4) + (intensity_avg * 0.4) + (recency_weight * 0.2)


def recency_weight(latest_post_ts, now=None) -> float:
    """Decay weight: 10 for <1 day old, approaches 0 over 7 days."""
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
shared_concerns: 1-3 points almost everyone agrees on.
"""


async def summarize_issue(label: str, posts: list[str]) -> dict:
    """
    Given an issue label and its post texts, return a structured summary dict.
    Keys: summary, side_a_points, side_b_points, shared_concerns, human_concern
    """
    combined = "\n---\n".join(posts[:80])   # cap at 80 posts to stay within token budget
    prompt = f"ISSUE: {label}\n\nPOSTS:\n{combined}"
    try:
        resp = await _anthropic.messages.create(
            model=CHAT_MODEL,
            max_tokens=1024,
            system=_SUMMARIZER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        # Strip markdown code fences if present
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
            "summary": f"Summary unavailable ({e})",
            "side_a_points": [],
            "side_b_points": [],
            "shared_concerns": [],
            "human_concern": "",
        }
