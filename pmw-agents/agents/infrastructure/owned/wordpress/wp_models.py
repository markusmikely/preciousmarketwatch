# infrastructure/owned/wordpress/wp_models.py
"""
SQLAlchemy models for core WordPress tables.
Table prefix defaults to 'wp_' — override via WP_TABLE_PREFIX env var.
Used for direct MySQL reads (reporting, intelligence queries).
"""

from __future__ import annotations
import os

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase

PREFIX = os.getenv("WP_TABLE_PREFIX", "wp_")


class Base(DeclarativeBase):
    pass


class WPPost(Base):
    __tablename__ = f"{PREFIX}posts"
    ID                = Column(BigInteger, primary_key=True, autoincrement=True)
    post_author       = Column(BigInteger, default=0)
    post_date         = Column(DateTime, default=func.now())
    post_date_gmt     = Column(DateTime, default=func.now())
    post_content      = Column(Text, default="")
    post_title        = Column(Text, default="")
    post_excerpt      = Column(Text, default="")
    post_status       = Column(String(20), default="publish")
    post_name         = Column(String(200), default="")
    post_type         = Column(String(20), default="post")
    post_modified     = Column(DateTime, default=func.now())
    post_modified_gmt = Column(DateTime, default=func.now())
    comment_count     = Column(BigInteger, default=0)
    menu_order        = Column(Integer, default=0)


class WPPostMeta(Base):
    __tablename__ = f"{PREFIX}postmeta"
    meta_id   = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id   = Column(BigInteger, nullable=False)
    meta_key  = Column(String(255), default="")
    meta_value = Column(Text, default="")


class WPTerm(Base):
    __tablename__ = f"{PREFIX}terms"
    term_id    = Column(BigInteger, primary_key=True, autoincrement=True)
    name       = Column(String(200), default="")
    slug       = Column(String(200), default="")
    term_group = Column(BigInteger, default=0)


class WPTermTaxonomy(Base):
    __tablename__ = f"{PREFIX}term_taxonomy"
    term_taxonomy_id = Column(BigInteger, primary_key=True, autoincrement=True)
    term_id          = Column(BigInteger, nullable=False)
    taxonomy         = Column(String(32), default="")
    description      = Column(Text, default="")
    parent           = Column(BigInteger, default=0)
    count            = Column(BigInteger, default=0)


class WPTermRelationship(Base):
    __tablename__ = f"{PREFIX}term_relationships"
    object_id        = Column(BigInteger, nullable=False)
    term_taxonomy_id = Column(BigInteger, nullable=False)
    term_order       = Column(Integer, default=0)


class WPOption(Base):
    __tablename__ = f"{PREFIX}options"
    option_id    = Column(BigInteger, primary_key=True, autoincrement=True)
    option_name  = Column(String(255), default="")
    option_value = Column(Text, default="")
    autoload     = Column(String(20), default="yes")