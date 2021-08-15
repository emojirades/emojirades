import pendulum

from sqlalchemy import select, asc, desc

from ..models import Scoreboard, ScoreboardHistory


class ScorekeeperDB:
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
        stmt = select(Scoreboard).where(
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
            score=0,
        )

    def increment_score(self, channel, user, score=1):
        entry = self.get_user(channel, user)

        previous_score = int(entry.score)
        entry.score += score
        current_score = int(entry.score)

        self.session.add(entry)

        self.record_history(channel, user, f"++,{previous_score},{current_score}")

        self.session.commit()
        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def decrement_score(self, channel, user, score=1):
        entry = self.get_user(channel, user)

        previous_score = int(entry.score)
        entry.score -= score
        current_score = int(entry.score)

        self.session.add(entry)

        self.record_history(channel, user, f"--,{previous_score},{current_score}")

        self.session.commit()
        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def set_score(self, channel, user, score):
        entry = self.get_user(channel, user)

        previous_score = int(entry.score)
        entry.score = score
        current_score = int(entry.score)

        self.session.add(entry)

        self.record_history(channel, user, f"set,{previous_score},{current_score}")

        self.session.commit()
        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def get_scoreboard(self, channel, limit=None):
        if limit is None:
            limit = self.SCOREBOARD_LIMIT

        if scoreboard := self.scoreboard_cache.get(channel):
            return scoreboard

        stmt = (
            select(Scoreboard)
            .where(
                Scoreboard.workspace_id == self.workspace_id,
                Scoreboard.channel_id == channel,
            )
            .order_by(
                desc(Scoreboard.score),
            )
        )

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()
        scoreboard = [
            (pos, row[0].user_id, row[0].score)
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

    def get_history(self, channel, limit=None, order_by="desc"):
        if limit is None:
            limit = self.HISTORY_LIMIT

        if history := self.history_cache.get((channel, limit, order_by)):
            return history

        stmt = select(ScoreboardHistory).where(
            ScoreboardHistory.workspace_id == self.workspace_id,
            ScoreboardHistory.channel_id == channel,
        )

        if order_by == "asc":
            stmt = stmt.order_by(asc(ScoreboardHistory.timestamp))
        elif order_by == "desc":
            stmt = stmt.order_by(desc(ScoreboardHistory.timestamp))

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()

        scorekeeper_history = [
            {
                "user_id": row[0].user_id,
                "timestamp": pendulum.instance(row[0].timestamp),
                "operation": row[0].operation,
            }
            for row in result
        ]

        self.history_cache[(channel, limit, order_by)] = scorekeeper_history

        return scorekeeper_history
