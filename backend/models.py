import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, Text, Float, Integer, Date, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    anon_name = Column(Text, nullable=False, unique=True)
    lean_score = Column(Float, nullable=True)          # NEVER returned via API
    created_at = Column(DateTime, default=datetime.utcnow)


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    side_a_points = Column(Text, nullable=True)        # JSON string
    side_b_points = Column(Text, nullable=True)        # JSON string
    shared_concerns = Column(Text, nullable=True)      # JSON string
    sentiment_avg = Column(Float, default=0.0)
    intensity_avg = Column(Float, default=0.0)
    post_count = Column(Integer, default=0)
    rank_score = Column(Float, default=0.0)
    week_start = Column(Text, default=lambda: date.today().isoformat())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Text, ForeignKey("users.id"), nullable=True)
    issue_id = Column(Text, ForeignKey("issues.id"), nullable=True)
    text = Column(Text, nullable=False)
    sentiment = Column(Float, nullable=True)
    intensity = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Text, ForeignKey("users.id"), nullable=True)
    issue_id = Column(Text, ForeignKey("issues.id"), nullable=True)
    starting_position = Column(Integer, nullable=True)
    pre_intensity = Column(Float, nullable=True)
    post_feeling = Column(Integer, nullable=True)
    empathy_choice = Column(Integer, nullable=True)
    statement_ratings = Column(Text, nullable=True)    # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


class EmpathyStat(Base):
    __tablename__ = "empathy_stats"

    issue_id = Column(Text, ForeignKey("issues.id"), primary_key=True)
    perspective_shift_rate = Column(Float, default=0.0)
    conflict_deepening_rate = Column(Float, default=0.0)
    shared_concern_index = Column(Float, default=0.0)
    intensity_delta = Column(Float, default=0.0)
    cross_position_empathy_score = Column(Float, default=0.0)
    total_respondents = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
