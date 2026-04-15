"""
Campus Pulse AI — FastAPI backend
Person A owns this file.
"""

import random
import string
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, init_db
from backend.models import User, Issue, Post, SurveyResponse, EmpathyStat
from backend import ml

app = FastAPI(title="Campus Pulse AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


# ---------------------------------------------------------------------------
# Helper: anonymous name generator
# ---------------------------------------------------------------------------

_ADJECTIVES = [
    "Teal", "Quiet", "Silver", "Bright", "Calm", "Swift", "Dusk", "Gray",
    "Echo", "Wild", "Still", "High", "Open", "Clear", "Dark", "Soft",
    "Rising", "Lost", "Mild", "Warm", "Thin", "Bold", "Cold", "Round",
    "Flat", "Slow", "Pale", "Deep", "Light", "Steep",
]
_NOUNS = [
    "Harbor", "Maple", "Creek", "Fern", "Ridge", "Pine", "Meadow", "Stone",
    "Valley", "Oak", "Water", "Plain", "Field", "River", "Hollow", "Birch",
    "Tide", "Moss", "Cliff", "Delta", "Air", "Path", "Front", "Hill",
    "Rock", "Wave", "Leaf", "Fjord", "Mist", "Bank",
]


def _gen_anon_name() -> str:
    adj = random.choice(_ADJECTIVES)
    noun = random.choice(_NOUNS)
    num = random.randint(1, 99)
    return f"{adj}{noun}{num:02d}"


# ---------------------------------------------------------------------------
# Pydantic request/response schemas
# ---------------------------------------------------------------------------

class CreateUserResponse(BaseModel):
    id: str
    anon_name: str


class SubmitPostRequest(BaseModel):
    user_id: str | None = None
    text: str


class SubmitPostResponse(BaseModel):
    post_id: str
    issue_id: str
    issue_label: str


class IssueListItem(BaseModel):
    id: str
    label: str
    sentiment_avg: float
    intensity_avg: float
    post_count: int
    rank_score: float


class EmpathyStatsSchema(BaseModel):
    perspective_shift_rate: float
    conflict_deepening_rate: float
    shared_concern_index: float
    intensity_delta: float
    cross_position_empathy_score: float
    total_respondents: int


class IssueDetail(BaseModel):
    id: str
    label: str
    summary: str | None
    side_a_points: list[str]
    side_b_points: list[str]
    shared_concerns: list[str]
    sentiment_avg: float
    intensity_avg: float
    post_count: int
    empathy_stats: EmpathyStatsSchema | None


class SurveyRequest(BaseModel):
    user_id: str | None = None
    issue_id: str
    starting_position: int | None = None
    pre_intensity: float | None = None
    post_feeling: int | None = None
    empathy_choice: int | None = None
    statement_ratings: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/users", response_model=CreateUserResponse, status_code=201)
async def create_user(db: AsyncSession = Depends(get_db)):
    """Create an anonymous user with a generated name."""
    # Try up to 10 times to find a unique name
    for _ in range(10):
        name = _gen_anon_name()
        existing = await db.execute(select(User).where(User.anon_name == name))
        if existing.scalar_one_or_none() is None:
            break

    user = User(anon_name=name, lean_score=None)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return CreateUserResponse(id=str(user.id), anon_name=user.anon_name)


@app.post("/api/posts", response_model=SubmitPostResponse, status_code=201)
async def submit_post(req: SubmitPostRequest, db: AsyncSession = Depends(get_db)):
    """
    Accept a free-text opinion, embed it, classify into an issue cluster,
    score sentiment/intensity, persist, and update issue aggregates.
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Post text cannot be empty.")

    # 1. Embed
    embedding = await ml.embed_text(text)

    # 2. Score
    sentiment, intensity = await ml.score_post(text)

    # 3. Classify — fetch all issue embeddings via a representative post per issue
    issue_rows = (await db.execute(select(Issue))).scalars().all()

    # Build issue centroid embeddings from their posts
    issue_embeddings: list[tuple[str, list[float]]] = []
    for issue in issue_rows:
        posts_q = await db.execute(
            select(Post.embedding)
            .where(Post.issue_id == issue.id, Post.embedding.isnot(None))
            .limit(20)
        )
        vecs = [row[0] for row in posts_q.fetchall() if row[0] is not None]
        if vecs:
            import numpy as np
            centroid = list(np.mean(vecs, axis=0))
            issue_embeddings.append((str(issue.id), centroid))

    matched_issue_id = await ml.classify_post(embedding, issue_embeddings)

    if matched_issue_id:
        issue = await db.get(Issue, UUID(matched_issue_id))
    else:
        # Create new issue
        label = await ml.label_new_issue(text)
        issue = Issue(
            label=label,
            week_start=date.today(),
            post_count=0,
            sentiment_avg=0.0,
            intensity_avg=0.0,
            rank_score=0.0,
        )
        db.add(issue)
        await db.flush()  # get issue.id

    # 4. Persist post
    user_uuid = UUID(req.user_id) if req.user_id else None
    post = Post(
        user_id=user_uuid,
        issue_id=issue.id,
        text=text,
        embedding=embedding,
        sentiment=sentiment,
        intensity=intensity,
    )
    db.add(post)

    # 5. Update issue aggregates
    new_count = issue.post_count + 1
    issue.sentiment_avg = (
        (issue.sentiment_avg * issue.post_count + sentiment) / new_count
    )
    issue.intensity_avg = (
        (issue.intensity_avg * issue.post_count + intensity) / new_count
    )
    issue.post_count = new_count
    issue.rank_score = ml.compute_rank_score(
        new_count,
        issue.intensity_avg,
        ml.recency_weight(datetime.now(timezone.utc)),
    )
    issue.updated_at = datetime.utcnow()

    # 6. Optionally refresh summary if post_count crosses a threshold
    SUMMARY_THRESHOLDS = {5, 10, 20, 50}
    if new_count in SUMMARY_THRESHOLDS:
        posts_q = await db.execute(
            select(Post.text).where(Post.issue_id == issue.id).limit(80)
        )
        all_texts = [r[0] for r in posts_q.fetchall()]
        summary_data = await ml.summarize_issue(issue.label, all_texts)
        issue.summary = summary_data["summary"]
        issue.side_a_points = summary_data["side_a_points"]
        issue.side_b_points = summary_data["side_b_points"]
        issue.shared_concerns = summary_data["shared_concerns"]

    await db.commit()
    await db.refresh(post)
    await db.refresh(issue)

    return SubmitPostResponse(
        post_id=str(post.id),
        issue_id=str(issue.id),
        issue_label=issue.label,
    )


@app.get("/api/issues", response_model=list[IssueListItem])
async def get_issues(db: AsyncSession = Depends(get_db)):
    """Return top 10 issues ranked by rank_score for the current week."""
    result = await db.execute(
        select(Issue)
        .where(Issue.week_start == date.today())
        .order_by(Issue.rank_score.desc())
        .limit(10)
    )
    issues = result.scalars().all()

    # Fallback: if no issues for today, return the overall top 10
    if not issues:
        result = await db.execute(
            select(Issue).order_by(Issue.rank_score.desc()).limit(10)
        )
        issues = result.scalars().all()

    return [
        IssueListItem(
            id=str(i.id),
            label=i.label,
            sentiment_avg=i.sentiment_avg or 0.0,
            intensity_avg=i.intensity_avg or 0.0,
            post_count=i.post_count or 0,
            rank_score=i.rank_score or 0.0,
        )
        for i in issues
    ]


@app.get("/api/issues/{issue_id}", response_model=IssueDetail)
async def get_issue(issue_id: str, db: AsyncSession = Depends(get_db)):
    """Full issue detail including unbiased summary and empathy stats."""
    issue = await db.get(Issue, UUID(issue_id))
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")

    # Lazy-generate summary if missing and there are posts
    if not issue.summary and issue.post_count > 0:
        posts_q = await db.execute(
            select(Post.text).where(Post.issue_id == issue.id).limit(80)
        )
        all_texts = [r[0] for r in posts_q.fetchall()]
        if all_texts:
            summary_data = await ml.summarize_issue(issue.label, all_texts)
            issue.summary = summary_data["summary"]
            issue.side_a_points = summary_data["side_a_points"]
            issue.side_b_points = summary_data["side_b_points"]
            issue.shared_concerns = summary_data["shared_concerns"]
            await db.commit()
            await db.refresh(issue)

    # Fetch empathy stats
    stat_row = await db.get(EmpathyStat, UUID(issue_id))
    empathy = None
    if stat_row:
        empathy = EmpathyStatsSchema(
            perspective_shift_rate=stat_row.perspective_shift_rate or 0.0,
            conflict_deepening_rate=stat_row.conflict_deepening_rate or 0.0,
            shared_concern_index=stat_row.shared_concern_index or 0.0,
            intensity_delta=stat_row.intensity_delta or 0.0,
            cross_position_empathy_score=stat_row.cross_position_empathy_score or 0.0,
            total_respondents=stat_row.total_respondents or 0,
        )

    return IssueDetail(
        id=str(issue.id),
        label=issue.label,
        summary=issue.summary,
        side_a_points=issue.side_a_points or [],
        side_b_points=issue.side_b_points or [],
        shared_concerns=issue.shared_concerns or [],
        sentiment_avg=issue.sentiment_avg or 0.0,
        intensity_avg=issue.intensity_avg or 0.0,
        post_count=issue.post_count or 0,
        empathy_stats=empathy,
    )


@app.post("/api/survey", status_code=201)
async def submit_survey(req: SurveyRequest, db: AsyncSession = Depends(get_db)):
    """Persist survey response and recompute empathy stats for the issue."""
    issue = await db.get(Issue, UUID(req.issue_id))
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found.")

    user_uuid = UUID(req.user_id) if req.user_id else None
    response = SurveyResponse(
        user_id=user_uuid,
        issue_id=issue.id,
        starting_position=req.starting_position,
        pre_intensity=req.pre_intensity,
        post_feeling=req.post_feeling,
        empathy_choice=req.empathy_choice,
        statement_ratings=req.statement_ratings,
    )
    db.add(response)
    await db.flush()

    # Recompute empathy stats
    await _recompute_empathy_stats(db, issue.id)
    await db.commit()

    return {"success": True}


@app.get("/api/stats/{issue_id}", response_model=EmpathyStatsSchema)
async def get_stats(issue_id: str, db: AsyncSession = Depends(get_db)):
    """Return precomputed empathy analytics for an issue."""
    stat = await db.get(EmpathyStat, UUID(issue_id))
    if not stat:
        # Return zeroes rather than 404 — issue may exist but have no survey data yet
        return EmpathyStatsSchema(
            perspective_shift_rate=0.0,
            conflict_deepening_rate=0.0,
            shared_concern_index=0.0,
            intensity_delta=0.0,
            cross_position_empathy_score=0.0,
            total_respondents=0,
        )
    return EmpathyStatsSchema(
        perspective_shift_rate=stat.perspective_shift_rate or 0.0,
        conflict_deepening_rate=stat.conflict_deepening_rate or 0.0,
        shared_concern_index=stat.shared_concern_index or 0.0,
        intensity_delta=stat.intensity_delta or 0.0,
        cross_position_empathy_score=stat.cross_position_empathy_score or 0.0,
        total_respondents=stat.total_respondents or 0,
    )


# ---------------------------------------------------------------------------
# Internal: empathy stats recomputation
# ---------------------------------------------------------------------------

async def _recompute_empathy_stats(db: AsyncSession, issue_id: UUID):
    """
    Recompute all empathy metrics from survey_responses for a given issue.

    Metrics:
    - perspective_shift_rate:    % who chose post_feeling 1 or 2 (shifted or understood better)
    - conflict_deepening_rate:   % who chose post_feeling 3 (felt more strongly opposed)
    - shared_concern_index:      avg of statement 4 ("common ground…") rating / 10
    - intensity_delta:           avg(pre_intensity) subtracted from inferred post_intensity
                                 (we use post_feeling=4 → conflicted as proxy for +intensity)
    - cross_position_empathy_score: avg of all statement_ratings / 10
    """
    rows_q = await db.execute(
        select(SurveyResponse).where(SurveyResponse.issue_id == issue_id)
    )
    rows = rows_q.scalars().all()

    n = len(rows)
    if n == 0:
        return

    shift = sum(1 for r in rows if r.post_feeling in (1, 2))
    deepen = sum(1 for r in rows if r.post_feeling == 3)

    # shared_concern_index: statement index 4 ("There's more common ground…"), 1-indexed key "4"
    shared_vals = []
    all_ratings = []
    for r in rows:
        if r.statement_ratings:
            ratings_vals = list(r.statement_ratings.values())
            all_ratings.extend(ratings_vals)
            # statement 5 is "more common ground" (last statement)
            key = str(len(r.statement_ratings))
            if key in r.statement_ratings:
                shared_vals.append(float(r.statement_ratings[key]))

    shared_concern_index = (sum(shared_vals) / len(shared_vals) / 10.0) if shared_vals else 0.0
    cross_pos = (sum(all_ratings) / len(all_ratings) / 10.0) if all_ratings else 0.0

    pre_intensities = [r.pre_intensity for r in rows if r.pre_intensity is not None]
    # Infer post-intensity: post_feeling=2 (shifted) or 4 (conflicted) → assume +1
    post_intensities = [
        (pi + 1.0) if r.post_feeling in (2, 4) else pi
        for r, pi in zip(rows, pre_intensities)
        if r.pre_intensity is not None
    ]
    intensity_delta = (
        (sum(post_intensities) - sum(pre_intensities)) / len(pre_intensities)
        if pre_intensities else 0.0
    )

    stat = await db.get(EmpathyStat, issue_id)
    if stat is None:
        stat = EmpathyStat(issue_id=issue_id)
        db.add(stat)

    stat.perspective_shift_rate = round(shift / n, 4)
    stat.conflict_deepening_rate = round(deepen / n, 4)
    stat.shared_concern_index = round(shared_concern_index, 4)
    stat.intensity_delta = round(intensity_delta, 4)
    stat.cross_position_empathy_score = round(cross_pos, 4)
    stat.total_respondents = n
    stat.updated_at = datetime.utcnow()
