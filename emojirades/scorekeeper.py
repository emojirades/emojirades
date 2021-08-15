import logging

from emojirades.persistence import ScorekeeperDB


class Scorekeeper:
    def __init__(self, session, workspace_id):
        self.handler = ScorekeeperDB(session, workspace_id)

        self.logger = logging.getLogger("EmojiradesBot.scorekeeper.ScoreKeeper")

    def plusplus(self, channel, user):
        return self.handler.increment_score(channel, user)

    def minusminus(self, channel, user):
        return self.handler.decrement_score(channel, user)

    def overwrite(self, channel, user, score):
        return self.handler.set_score(channel, user, score)

    def scoreboard(self, channel):
        return self.handler.get_scoreboard(channel)

    def user_score(self, channel, user):
        return self.handler.position_on_scoreboard(channel, user)

    def history(self, channel):
        return self.handler.get_history(channel)

    def history_all(self, channel):
        return self.handler.get_history(channel, limit=0, order_by="asc")
