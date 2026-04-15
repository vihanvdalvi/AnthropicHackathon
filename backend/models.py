import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, Text, Float, Integer, Date, DateTime,
    ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anon_name = Column(Text, nullable=False, unique=True)
    lean_score = Column(Float, nullable=True)          # NEVER returned via API
    created_at = Column(DateTime, default=datetime.utcnow)


class Issue(Base):
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    side_a_points = Column(JSONB, nullable=True)       # list[str]
    side_b_points = Column(JSONB, nullable=True)       # list[str]
    shared_concerns = Column(JSONB, nullable=True)     # list[str]
    sentiment_avg = Column(Float, default=0.0)
    intensity_avg = Column(Float, default=0.0)
    post_count = Column(Integer, default=0)
    rank_score = Column(Float, default=0.0)
    week_start = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    sentiment = Column(Float, nullable=True)
    intensity = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=True)
    starting_position = Column(Integer, nullable=True)     # 1-4 (before-reading choice)
    pre_intensity = Column(Float, nullable=True)           # 1–10 slider
    post_feeling = Column(Integer, nullable=True)          # 1-4 (after-reading choice)
    empathy_choice = Column(Integer, nullable=True)        # 1-4 (empathy check choice)
    statement_ratings = Column(JSONB, nullable=True)       # {stmt_index: rating}
    created_at = Column(DateTime, default=datetime.utcnow)


class EmpathyStat(Base):
    __tablename__ = "empathy_stats"

    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), primary_key=True)
    perspective_shift_rate = Column(Float, default=0.0)
    conflict_deepening_rate = Column(Float, default=0.0)
    shared_concern_index = Column(Float, default=0.0)
    intensity_delta = Column(Float, default=0.0)
    cross_position_empathy_score = Column(Float, default=0.0)
    total_respondents = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
