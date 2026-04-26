import datetime
import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, Identity, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import AwareDateTime, Base


class GamestateStep(enum.Enum):
    NEW_GAME = 1
    WAITING = 2
    PROVIDED = 3
    GUESSING = 4


class GamestateModel(Base):
    __tablename__ = "gamestate"

    workspace_id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False)
    channel_id: Mapped[str] = mapped_column(Text, primary_key=True, autoincrement=False)

    step: Mapped[GamestateStep] = mapped_column(
        Enum(GamestateStep), nullable=False, default=GamestateStep.NEW_GAME
    )
    current_winner: Mapped[Optional[str]] = mapped_column(Text)
    previous_winner: Mapped[Optional[str]] = mapped_column(Text)
    emojirade: Mapped[Optional[str]] = mapped_column(Text)
    raw_emojirade: Mapped[Optional[str]] = mapped_column(Text)
    first_guess: Mapped[Optional[bool]] = mapped_column(Boolean)
    admins: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    last_updated: Mapped[datetime.datetime] = mapped_column(
        AwareDateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"GamestateModel(workspace_id={self.workspace_id!r},"
            f"channel_id={self.channel_id!r}, step={self.step!r})"
        )


class GamestateHistoryModel(Base):
    __tablename__ = "gamestate_history"

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
            f"GamestateHistoryModel(w_id={self.workspace_id!r}, "
            f"c_id={self.channel_id!r}, u_id={self.user_id!r}, "
            f"op={self.operation!r})"
        )


Index(
    "idx_gamestate_history_channel",
    GamestateHistoryModel.workspace_id,
    GamestateHistoryModel.channel_id,
)
