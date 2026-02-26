"""
PMW Bridge Models — V1 minimal schema (must match agents/shared/models)
Bridge only creates workflow_runs and workflow_stages; does not run agents.
"""
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(255), nullable=False)
    affiliate_name = Column(String(255), nullable=False)
    affiliate_url = Column(String(512), nullable=False)
    target_keyword = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    status = Column(String(32), default="pending", nullable=False)
    current_stage = Column(String(64), default="research", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    final_score = Column(Float, nullable=True)


class WorkflowStage(Base):
    __tablename__ = "workflow_stages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("workflow_runs.id"), nullable=False)
    stage_name = Column(String(64), nullable=False)
    status = Column(String(32), default="pending", nullable=False)
    score = Column(Float, nullable=True)
    attempt_number = Column(Integer, default=1)
    output_json = Column(Text, nullable=True)
    judge_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
