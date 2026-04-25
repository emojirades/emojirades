from sqlalchemy import select, delete, asc, desc

from ..models import ScoreboardModel, ScoreboardHistoryModel


class ScorekeeperDB:
    SCOREBOARD_LIMIT = 15
    HISTORY_LIMIT = 15

    def __init__(self, session_factory, workspace_id, caching=False):
        self.session_factory = session_factory
        self.workspace_id = workspace_id
        self.caching = caching

        self.scoreboard_cache = {}
        self.history_cache = {}

    @property
    def session(self):
        return self.session_factory()

    def clear_cache(self, channel):
        self.scoreboard_cache.pop(channel, None)
        self.history_cache.pop(channel, None)

    def delete(self, iknowwhatimdoing=False):
        if not iknowwhatimdoing:
            return

        self.scoreboard_cache = {}
        self.history_cache = {}

        self.session.execute(delete(ScoreboardHistoryModel))
        self.session.execute(delete(ScoreboardModel))

        self.session.commit()

    def record_history(self, channel, user, operation, commit=False):
        self.session.add(
            ScoreboardHistoryModel(
                workspace_id=self.workspace_id,
                channel_id=channel,
                user_id=user,
                operation=operation,
            )
        )

        if commit:
            self.session.commit()

    def get_user(self, channel, user):
        # We don't cache user objects directly here (get_scoreboard caches them in a list)
        # But for correctness if we ever do, or if an object is already in session:
        stmt = select(ScoreboardModel).where(
            ScoreboardModel.workspace_id == self.workspace_id,
            ScoreboardModel.channel_id == channel,
            ScoreboardModel.user_id == user,
        )

        result = self.session.execute(stmt).first()

        if result:
            return result[0]

        return ScoreboardModel(
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

        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def decrement_score(self, channel, user, score=1):
        entry = self.get_user(channel, user)

        previous_score = int(entry.score)
        entry.score -= score
        current_score = int(entry.score)

        self.session.add(entry)

        self.record_history(channel, user, f"--,{previous_score},{current_score}")

        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def set_score(self, channel, user, score):
        entry = self.get_user(channel, user)

        previous_score = int(entry.score)
        entry.score = score
        current_score = int(entry.score)

        self.session.add(entry)

        self.record_history(channel, user, f"set,{previous_score},{current_score}")

        self.clear_cache(channel)

        return self.position_on_scoreboard(channel, user)

    def get_scoreboard(self, channel, limit=None):
        if limit is None:
            limit = self.SCOREBOARD_LIMIT

        if scoreboard := self.scoreboard_cache.get(channel):
            return scoreboard

        stmt = (
            select(ScoreboardModel)
            .where(
                ScoreboardModel.workspace_id == self.workspace_id,
                ScoreboardModel.channel_id == channel,
            )
            .order_by(
                desc(ScoreboardModel.score),
            )
        )

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()
        scoreboard = [
            (pos, row[0].user_id, row[0].score)
            for pos, row in enumerate(result, start=1)
        ]

        if self.caching:
            self.scoreboard_cache[channel] = scoreboard

        return scoreboard

    def position_on_scoreboard(self, channel, user):
        scoreboard = self.get_scoreboard(channel)

        for pos, user_id, score in scoreboard:
            if user_id == user:
                return pos, score

        return None, None

    def get_history(self, channel, limit=None, user=None, order_by="desc"):
        if limit is None:
            limit = self.HISTORY_LIMIT

        cache_key = (channel, user, limit, order_by)

        if history := self.history_cache.get(cache_key):
            return history

        stmt = select(ScoreboardHistoryModel).where(
            ScoreboardHistoryModel.workspace_id == self.workspace_id,
            ScoreboardHistoryModel.channel_id == channel,
        )

        if user is not None:
            stmt = stmt.where(
                ScoreboardHistoryModel.user_id == user,
            )

        if order_by == "asc":
            stmt = stmt.order_by(asc(ScoreboardHistoryModel.timestamp))
        elif order_by == "desc":
            stmt = stmt.order_by(desc(ScoreboardHistoryModel.timestamp))

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()

        scorekeeper_history = [
            {
                "user_id": row[0].user_id,
                "timestamp": row[0].timestamp,
                "operation": row[0].operation,
            }
            for row in result
        ]

        if self.caching:
            self.history_cache[cache_key] = scorekeeper_history

        return scorekeeper_history
