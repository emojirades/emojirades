import datetime
from typing import Optional

from sqlalchemy import Identity, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import AwareDateTime, Base


class ScoreboardModel(Base):
    __tablename__ = "scoreboard"

    workspace_id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False)
    channel_id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False)

    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_updated: Mapped[datetime.datetime] = mapped_column(
        AwareDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"ScoreboardModel(workspace_id={self.workspace_id!r}, "
            f"channel_id={self.channel_id!r}, user_id={self.user_id!r}, "
            f"score={self.score!r})"
        )


class ScoreboardHistoryModel(Base):
    __tablename__ = "scoreboard_history"

    event_id: Mapped[int] = mapped_column(Identity(), primary_key=True)

    workspace_id: Mapped[Optional[str]] = mapped_column(Text)
    channel_id: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[Optional[str]] = mapped_column(Text)

    timestamp: Mapped[datetime.datetime] = mapped_column(
        AwareDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    operation: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return (
            f"ScoreboardHistoryModel(w_id={self.workspace_id!r}, "
            f"c_id={self.channel_id!r}, u_id={self.user_id!r}, "
            f"operation={self.operation!r})"
        )
