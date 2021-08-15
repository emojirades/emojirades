import json

from sqlalchemy import select, desc, or_

from ..models import Gamestate, GamestateHistory, GamestateStep


class GamestateDB:
    HISTORY_LIMIT = 5

    def __init__(self, session, workspace_id):
        self.session = session
        self.workspace_id = workspace_id

        self.gamestate_cache = {}
        self.history_cache = {}

    def clear_cache(self, channel):
        self.gamestate_cache.pop(channel, None)
        self.history_cache.pop(channel, None)

    def record_history(self, channel, user, operation, commit=False):
        self.session.add(
            GamestateHistory(
                workspace_id=self.workspace_id,
                channel_id=channel,
                user_id=user,
                operation=operation,
            )
        )

        if commit:
            self.session.commit()

    def get_gamestate(self, channel):
        if gamestate := self.gamestate_cache.get(channel):
            return gamestate

        stmt = select(Gamestate).where(
            Gamestate.workspace_id == self.workspace_id,
            Gamestate.channel_id == channel,
        )

        result = self.session.execute(stmt).first()

        if result:
            gamestate = result[0]

            self.gamestate_cache[channel] = gamestate
            return gamestate

        gamestate = Gamestate(
            workspace_id=self.workspace_id,
            channel_id=channel,
        )

        self.session.add(gamestate)
        self.session.commit()

        self.gamestate_cache[channel] = gamestate
        return gamestate

    def get_xyz(self, channel, xyz):
        gamestate = self.get_gamestate(channel)

        return getattr(gamestate, xyz)

    def set_xyz(self, channel, user, xyz, value):
        gamestate = self.get_gamestate(channel)

        setattr(gamestate, xyz, value)
        self.record_history(channel, user, f"set,{xyz},{value}")

        self.session.commit()
        self.clear_cache(channel)

    def set_many_xyz(self, channel, user, pairs):
        gamestate = self.get_gamestate(channel)

        for (xyz, value) in pairs:
            setattr(gamestate, xyz, value)
            self.record_history(channel, user, f"set,{xyz},{value}")

        self.session.commit()
        self.clear_cache(channel)

    def is_first_guess(self, channel):
        return self.get_gamestate(channel).first_guess

    def add_admin(self, channel, user):
        gamestate = self.get_gamestate(channel)

        admins = json.loads(gamestate.admins)

        if user in admins:
            return False

        admins.append(user)
        gamestate.admins = json.dumps(admins)

        self.session.commit()
        self.clear_cache(channel)

        return True

    def remove_admin(self, channel, user):
        gamestate = self.get_gamestate(channel)

        admins = json.loads(gamestate.admins)

        if user not in admins:
            return False

        admins.remove(user)
        gamestate.admins = json.dumps(admins)

        self.session.commit()
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

        self.session.commit()
        self.clear_cache(channel)

    def get_history(self, channel, limit=None):
        if limit is None:
            limit = self.HISTORY_LIMIT

        if history := self.history_cache.get(channel):
            return history

        stmt = (
            select(
                GamestateHistory.user_id,
                GamestateHistory.timestamp,
                GamestateHistory.operation,
            )
            .where(
                GamestateHistory.workspace_id == self.workspace_id,
                GamestateHistory.channel_id == channel,
            )
            .order_by(
                desc(GamestateHistory.timestamp),
            )
        )

        if limit:
            stmt = stmt.limit(limit)

        result = self.session.execute(stmt).fetchall()

        gamestate_history = [
            (row.user_id, row.timestamp, row.operation) for row in result
        ]

        self.history_cache[channel] = gamestate_history

        return gamestate_history

    def get_channels(self):
        stmt = select(
            Gamestate.channel_id,
        )

        result = self.session.execute(stmt).fetchall()

        return [row.channel_id for row in result]

    def get_pending_channel(self, previous_winner):
        stmt = select(Gamestate.channel_id,).where(
            Gamestate.workspace_id == self.workspace_id,
            or_(
                Gamestate.step == GamestateStep.WAITING,
                Gamestate.step == GamestateStep.PROVIDED,
            ),
            Gamestate.previous_winner == previous_winner,
        )

        # We pick the first
        result = self.session.execute(stmt).first()

        if result is None:
            return None

        return result[0]
