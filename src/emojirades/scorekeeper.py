import logging

from emojirades.persistence import ScorekeeperRepository


class Scorekeeper:
    def __init__(self, session_factory, workspace_id, caching=False):
        self.repository = ScorekeeperRepository(session_factory, workspace_id, caching=caching)

        self.logger = logging.getLogger("EmojiradesBot.scorekeeper.ScoreKeeper")

    def plusplus(self, channel, user):
        return self.repository.increment_score(channel, user)

    def minusminus(self, channel, user):
        return self.repository.decrement_score(channel, user)

    def overwrite(self, channel, user, score):
        return self.repository.set_score(channel, user, score)

    def scoreboard(self, channel):
        return self.repository.get_scoreboard(channel)

    def user_score(self, channel, user):
        return self.repository.position_on_scoreboard(channel, user)

    def history(self, channel, user=None, limit=None):
        return self.repository.get_history(channel, user=user, limit=limit)

    def history_all(self, channel):
        return self.repository.get_history(channel, limit=0, order_by="asc")
