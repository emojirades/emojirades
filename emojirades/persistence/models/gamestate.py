import datetime
import enum

from sqlalchemy import Column, Text, Enum, DateTime, Boolean, Integer, Index, Identity

from .base import Base


class GamestateStep(enum.Enum):
    NEW_GAME = 1
    WAITING = 2
    PROVIDED = 3
    GUESSING = 4


class Gamestate(Base):
    # pylint: disable=too-few-public-methods
    __tablename__ = "gamestate"

    workspace_id = Column(Text, primary_key=True)
    channel_id = Column(Text, primary_key=True)

    step = Column(Enum(GamestateStep), nullable=False, default=GamestateStep.NEW_GAME)
    current_winner = Column(Text)
    previous_winner = Column(Text)
    emojirade = Column(Text)
    raw_emojirade = Column(Text)
    first_guess = Column(Boolean)
    admins = Column(Text, nullable=False, default="[]")

    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def __repr__(self):
        return (
            f"Gamestate(workspace_id={self.workspace_id!r},"
            f"channel_id={self.channel_id!r}, step={self.step!r})"
        )


class GamestateHistory(Base):
    # pylint: disable=too-few-public-methods
    __tablename__ = "gamestate_history"

    event_id = Column(Integer, Identity(), primary_key=True)

    workspace_id = Column(Text)
    channel_id = Column(Text)
    user_id = Column(Text)

    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    operation = Column(Text, nullable=False)

    def __repr__(self):
        return (
            f"GamestateHistory(w_id={self.workspace_id!r}, "
            f"c_id={self.channel_id!r}, u_id={self.user_id!r}, "
            f"op={self.operation!r})"
        )


Index(
    "idx_gamestate_history_channel",
    GamestateHistory.workspace_id,
    GamestateHistory.channel_id,
)
