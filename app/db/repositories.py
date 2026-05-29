"""Small repository helpers for persistence tests and early services."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel, col, select

from app.db.models import Article, Comment, DailyReport

ModelT = TypeVar("ModelT", bound=SQLModel)


class Repository(Generic[ModelT]):
    """Minimal repository wrapper around a SQLModel table class."""

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def get(self, item_id: str) -> ModelT | None:
        return self.session.get(self.model, item_id)

    def list(self, limit: int = 100) -> Sequence[ModelT]:
        statement = select(self.model).limit(limit)
        return self.session.exec(statement).all()


def get_article_by_content_hash(session: Session, content_hash: str) -> Article | None:
    statement = select(Article).where(Article.content_hash == content_hash)
    return session.exec(statement).first()


def get_comment_by_content_hash(session: Session, content_hash: str) -> Comment | None:
    statement = select(Comment).where(Comment.content_hash == content_hash)
    return session.exec(statement).first()


def list_reports_by_date(session: Session, report_date) -> Sequence[DailyReport]:
    statement = select(DailyReport).where(DailyReport.report_date == report_date)
    return session.exec(statement).all()


def list_recent_articles(session: Session, limit: int = 20) -> Sequence[Article]:
    statement = select(Article).order_by(col(Article.collected_at).desc()).limit(limit)
    return session.exec(statement).all()
