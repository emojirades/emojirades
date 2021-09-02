import json

from sqlalchemy import select, delete, desc, or_

from ..models import Gamestate, GamestateHistory, GamestateStep


class GamestateDB:
    HISTORY_LIMIT = 5

    def __init__(self, session, workspace_id, caching=False):
        self.session = session
        self.workspace_id = workspace_id
        self.caching = caching

        self.gamestate_cache = {}
        self.history_cache = {}

    def clear_cache(self, channel):
        print("BEFORE CACHE CLEAR")
        print(self.gamestate_cache)
        self.gamestate_cache.pop(channel, None)
        self.history_cache.pop(channel, None)
        print("AFTER CACHE CLEAR")
        print(self.gamestate_cache)

    def delete(self, channel):
        print("TRIGGERING DELETE OF GamestateHistory")
        stmt = delete(GamestateHistory).where(
            GamestateHistory.workspace_id == self.workspace_id,
            GamestateHistory.channel_id == channel,
        )

        result = self.session.execute(stmt)

        print("TRIGGERING DELETE OF Gamestate")
        stmt = delete(Gamestate).where(
            Gamestate.workspace_id == self.workspace_id,
            Gamestate.channel_id == channel,
        )

        result = self.session.execute(stmt)
        print("DELETE DONE")

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
            print(f"GAMESTATE FOR {channel} FOUND IN CACHE")
            return gamestate

        stmt = select(Gamestate).where(
            Gamestate.workspace_id == self.workspace_id,
            Gamestate.channel_id == channel,
        )

        result = self.session.execute(stmt).first()

        if result:
            print(f"GAMESTATE FOR {channel} LOOKED UP")
            gamestate = result[0]

            if self.caching:
                self.gamestate_cache[channel] = gamestate

            return gamestate

        print(f"WARNING: Gamestate not found for {self.workspace_id}/{channel}")
        gamestate = Gamestate(
            workspace_id=self.workspace_id,
            channel_id=channel,
        )

        self.session.add(gamestate)
        self.session.commit()

        if self.caching:
            self.gamestate_cache[channel] = gamestate
            print(self.gamestate_cache)

        return gamestate

    def get_xyz(self, channel, xyz):
        print(f"WAS ASKED FOR {xyz} FOR {channel}")
        gamestate = self.get_gamestate(channel)

        return getattr(gamestate, xyz)

    def set_xyz(self, channel, user, xyz, value):
        print(f"WAS ASKED TO SET {xyz} TO {value} FOR {channel}")
        gamestate = self.get_gamestate(channel)

        setattr(gamestate, xyz, value)
        self.record_history(channel, user, f"set,{xyz},{value}")

        self.session.commit()

        if self.caching:
            self.clear_cache(channel)

    def set_many_xyz(self, channel, user, pairs):
        print(f"WAS ASKED TO SET {pairs} FOR {channel}")
        gamestate = self.get_gamestate(channel)

        for (xyz, value) in pairs:
            setattr(gamestate, xyz, value)
            self.record_history(channel, user, f"set,{xyz},{value}")

        self.session.commit()

        if self.caching:
            self.clear_cache(channel)

    def is_first_guess(self, channel):
        print(f"FIRST GUESS GAMESTATE FOR {channel} LOOKED UP")
        return self.get_gamestate(channel).first_guess

    def add_admin(self, channel, user):
        gamestate = self.get_gamestate(channel)

        admins = json.loads(gamestate.admins)

        if user in admins:
            return False

        admins.append(user)
        gamestate.admins = json.dumps(admins)

        self.session.commit()

        if self.caching:
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

        if self.caching:
            self.clear_cache(channel)

        return True

    def new_game(self, channel, previous_winner, current_winner):
        print(f"RUNNING NEW GAME FOR {channel}")
        gamestate = self.get_gamestate(channel)

        gamestate.step = GamestateStep.WAITING
        gamestate.current_winner = current_winner
        gamestate.previous_winner = previous_winner
        gamestate.emojirade = None
        gamestate.raw_emojirade = None
        gamestate.first_guess = True

        print(gamestate)
        self.session.commit()
        print(gamestate)

        if self.caching:
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
        print(f"GET_PENDING_CHANNEL FOR {previous_winner}")
        #import time
        #time.sleep(5)

        stmt = select(Gamestate)

        result = self.session.execute(stmt)

        for row in result:
            print(row)

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
            print("FOUND NOTHING")
            return None
        else:
            print(f"FOUND {result}")

        return result[0]
