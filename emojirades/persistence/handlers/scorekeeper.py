from sqlalchemy import select, desc

from ..models import Scoreboard, ScoreboardHistory


class ScorekeeperDB():
    SCOREBOARD_LIMIT = 15
    HISTORY_LIMIT = 15

    def __init__(self, session, workspace_id):
        self.session = session
        self.workspace_id = workspace_id

        self.scoreboard_cache = {}
        self.history_cache = {}

    def clear_cache(self, channel):
        self.scoreboard_cache.pop(channel, None)
        self.history_cache.pop(channel, None)

    def record_history(self, channel, user, operation, commit=False):
        self.session.add(
            ScoreboardHistory(
                workspace_id=self.workspace_id,
                channel_id=channel,
                user_id=user,
                operation=operation,
            )
        )

        if commit:
            self.session.commit()

    def get_user(self, channel, user):
        stmt = select(
            Scoreboard,
        ).where(
            Scoreboard.workspace_id == self.workspace_id,
            Scoreboard.channel_id == channel,
            Scoreboard.user_id == user,
        )

        result = self.session.execute(stmt).first()

        if result:
            return result[0]

        return Scoreboard(
            workspace_id=self.workspace_id,
            channel_id=channel,
            user_id=user,
        )

    def increment_score(self, channel, user, score=1):
        user = self.get_user(channel, user)

        previous_score = int(user.score)
        user.score += score
        current_score = int(user.score)

        self.session.add(user)

        self.record_history(channel, user, f"++,{previous_score},{current_score}")

        self.session.commit()
        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def decrement_score(self, channel, user, score=1):
        user = self.get_user(channel, user)

        previous_score = int(user.score)
        user.score -= score
        current_score = int(user.score)

        self.session.add(user)

        self.record_history(channel, user, f"--,{previous_score},{current_score}")

        self.session.commit()
        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def set_score(self, channel, user, score):
        user = self.get_user(channel, user)

        previous_score = int(user.score)
        user.score = score
        current_score = int(user.score)

        self.session.add(user)

        self.record_history(channel, user, f"set,{previous_score},{current_score}")

        self.session.commit()
        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def get_scoreboard(self, channel, limit=None):
        if limit is None:
            limit = self.SCOREBOARD_LIMIT

        if scoreboard := self.scoreboard_cache.get(channel):
            return scoreboard

        stmt = select(
            Scoreboard.user_id,
            Scoreboard.score,
        ).where(
            Scoreboard.workspace_id == self.workspace_id,
            Scoreboard.channel_id == channel,
        ).order_by(
            desc(Scoreboard.score),
        )

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()
        scoreboard = [
            (pos, row.user_id, row.score)
            for pos, row in enumerate(result, start=1)
        ]

        self.scoreboard_cache[channel] = scoreboard

        return scoreboard

    def position_on_scoreboard(self, channel, user):
        scoreboard = self.get_scoreboard(channel)

        for (pos, user_id, score) in scoreboard:
            if user_id == user:
                return pos, score

        return None, None

    def get_history(self, channel, limit=None):
        if limit is None:
            limit = self.HISTORY_LIMIT

        if history := self.history_cache.get(channel):
            return history

        stmt = select(
            ScoreboardHistory.user_id,
            ScoreboardHistory.timestamp,
            ScoreboardHistory.operation,
        ).where(
            ScoreboardHistory.workspace_id == self.workspace_id,
            ScoreboardHistory.channel_id == channel,
        ).order_by(
            desc(ScoreboardHistory.timestamp),
        )

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()

        scorekeeper_history = [
            (row.user_id, row.timestamp, row.operation)
            for row in result
        ]

        self.history_cache[channel] = scorekeeper_history

        return scorekeeper_history
