import datetime
import enum

from sqlalchemy import Column, Text, Enum, ARRAY, DateTime, Boolean, BigInteger, Index, Identity

from .base import Base


class GamestateStep(enum.Enum):
    NEW_GAME = 1
    WAITING = 2
    PROVIDED = 3
    GUESSING = 4


class Gamestate(Base):
    # pylint: disable=too-few-public-methods
    __tablename__ = "game_state"

    workspace_id = Column(Text, primary_key=True)
    channel_id = Column(Text, primary_key=True)

    step = Column(Enum(GamestateStep), nullable=False, default=GamestateStep.NEW_GAME)
    current_winner = Column(Text)
    previous_winner = Column(Text)
    emojirade = Column(ARRAY(Text))
    raw_emojirade = Column(ARRAY(Text))
    first_guess = Column(Boolean)
    admins = Column(ARRAY(Text), nullable=False, default=list)

    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        return (
            f"Gamestate(workspace_id={self.workspace_id!r},"
            "channel_id={self.channel_id!r}, step={self.step!r})"
        )


class GamestateHistory(Base):
    # pylint: disable=too-few-public-methods
    __tablename__ = "gamestate_history"

    event_id = Column(BigInteger, Identity(), primary_key=True)

    workspace_id = Column(Text)
    channel_id = Column(Text)
    user_id = Column(Text)

    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    operation = Column(Text, nullable=False)

    Index("idx_gamestate_history_channel", "workspace_id", "channel_id")

    def __repr__(self):
        return f"GamestateHistory(w_id={self.workspace_id!r}, " \
                "c_id={self.channel_id!r}, u_id={self.user_id!r}, " \
                "op={self.operation!r})"
