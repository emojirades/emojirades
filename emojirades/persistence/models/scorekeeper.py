import datetime

from sqlalchemy import Column, Text, Integer, DateTime, Identity, Index

from .base import Base


class Scoreboard(Base):
    # pylint: disable=too-few-public-methods
    __tablename__ = "scoreboard"

    workspace_id = Column(Text, primary_key=True)
    channel_id = Column(Text, primary_key=True)
    user_id = Column(Text, primary_key=True)

    score = Column(Integer, nullable=False, default=0)

    last_updated = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    Index("idx_scoreboard_channel", "workspace_id", "channel_id", unique=True)

    def __repr__(self):
        return (
            f"Scoreboard(w_id={self.workspace_id!r}, c_id={self.channel_id!r}, "
            f"u_id={self.user_id!r}, score={self.score!r})"
        )


class ScoreboardHistory(Base):
    # pylint: disable=too-few-public-methods
    __tablename__ = "scoreboard_history"

    event_id = Column(Integer, Identity(), primary_key=True)

    workspace_id = Column(Text)
    channel_id = Column(Text)
    user_id = Column(Text)

    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    operation = Column(Text, nullable=False)

    Index("idx_scoreboard_history_channel", "workspace_id", "channel_id")

    def __repr__(self):
        return (
            f"ScoreboardHistory(w_id={self.workspace_id!r}, "
            f"c_id={self.channel_id!r}, u_id={self.user_id!r}, "
            f"op={self.operation!r})"
        )
