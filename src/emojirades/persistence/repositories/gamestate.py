import json
import threading

from sqlalchemy import delete, desc, or_, select

from ..models import GamestateHistoryModel, GamestateModel, GamestateStep


class GamestateRepository:
    HISTORY_LIMIT = 5

    def __init__(self, session_factory, workspace_id, caching=False):
        self.session_factory = session_factory
        self.workspace_id = workspace_id
        self.caching = caching

        self.lock = threading.Lock()
        self.gamestate_cache = {}
        self.history_cache = {}

    @property
    def session(self):
        return self.session_factory()

    def clear_cache(self, channel):
        with self.lock:
            self.gamestate_cache.pop(channel, None)
            self.history_cache.pop(channel, None)

    def delete(self, iknowwhatimdoing=False):
        if not iknowwhatimdoing:
            return

        with self.lock:
            self.gamestate_cache = {}
            self.history_cache = {}

        self.session.execute(delete(GamestateHistoryModel))
        self.session.execute(delete(GamestateModel))

        self.session.commit()

    def record_history(self, channel, user, operation, commit=False):
        self.session.add(
            GamestateHistoryModel(
                workspace_id=self.workspace_id,
                channel_id=channel,
                user_id=user,
                operation=operation,
            )
        )

        if commit:
            self.session.commit()

    def get_gamestates(self, current_workspace=True):
        stmt = select(GamestateModel)

        if current_workspace:
            stmt = stmt.where(GamestateModel.workspace_id == self.workspace_id)

        return self.session.execute(stmt)

    def get_gamestate(self, channel):
        # session.get handles both local (identity map) and database lookups
        # It's more robust than manual caching with merge for composite PKs
        gamestate = self.session.get(GamestateModel, (self.workspace_id, channel))

        if gamestate:
            return gamestate

        gamestate = GamestateModel(
            workspace_id=self.workspace_id,
            channel_id=channel,
        )

        self.session.add(gamestate)
        self.session.commit()

        return gamestate

    def get_xyz(self, channel, xyz):
        gamestate = self.get_gamestate(channel)

        return getattr(gamestate, xyz)

    def set_xyz(self, channel, user, xyz, value):
        gamestate = self.get_gamestate(channel)

        setattr(gamestate, xyz, value)
        self.record_history(channel, user, f"set,{xyz},{value}")

        if self.caching:
            self.clear_cache(channel)

    def set_many_xyz(self, channel, user, pairs):
        gamestate = self.get_gamestate(channel)

        for xyz, value in pairs:
            setattr(gamestate, xyz, value)
            self.record_history(channel, user, f"set,{xyz},{value}")

        if self.caching:
            self.clear_cache(channel)

    def is_first_guess(self, channel):
        return self.get_gamestate(channel).first_guess

    def add_admin(self, channel, user):
        gamestate = self.get_gamestate(channel)

        admins = json.loads(gamestate.admins or "[]")

        if user in admins:
            return False

        admins.append(user)
        gamestate.admins = json.dumps(admins)

        if self.caching:
            self.clear_cache(channel)

        return True

    def remove_admin(self, channel, user):
        gamestate = self.get_gamestate(channel)

        admins = json.loads(gamestate.admins or "[]")

        if user not in admins:
            return False

        admins.remove(user)
        gamestate.admins = json.dumps(admins)

        if self.caching:
            self.clear_cache(channel)

        return True

    def new_game(self, channel, previous_winner, current_winner):
        gamestate = self.get_gamestate(channel)

        gamestate.step = GamestateStep.WAITING
        gamestate.current_winner = current_winner
        gamestate.previous_winner = previous_winner
        gamestate.emojirade = None
        gamestate.raw_emojirade = None
        gamestate.first_guess = True

        if self.caching:
            self.clear_cache(channel)

    def get_history(self, channel, limit=None):
        if limit is None:
            limit = self.HISTORY_LIMIT

        with self.lock:
            if history := self.history_cache.get(channel):
                return history

            stmt = (
                select(
                    GamestateHistoryModel.user_id,
                    GamestateHistoryModel.timestamp,
                    GamestateHistoryModel.operation,
                )
                .where(
                    GamestateHistoryModel.workspace_id == self.workspace_id,
                    GamestateHistoryModel.channel_id == channel,
                )
                .order_by(
                    desc(GamestateHistoryModel.timestamp),
                )
            )

            if limit:
                stmt = stmt.limit(limit)

            result = self.session.execute(stmt).fetchall()

            gamestate_history = [(row.user_id, row.timestamp, row.operation) for row in result]

            self.history_cache[channel] = gamestate_history

            return gamestate_history

    def get_channels(self):
        stmt = select(
            GamestateModel.channel_id,
        )

        result = self.session.execute(stmt).fetchall()

        return [row.channel_id for row in result]

    def get_pending_channel(self, previous_winner):
        stmt = select(
            GamestateModel.channel_id,
        ).where(
            GamestateModel.workspace_id == self.workspace_id,
            or_(
                GamestateModel.step == GamestateStep.WAITING,
                GamestateModel.step == GamestateStep.PROVIDED,
            ),
            GamestateModel.previous_winner == previous_winner,
        )

        # We pick the first
        result = self.session.execute(stmt).first()

        if result is None:
            return None

        return result[0]
