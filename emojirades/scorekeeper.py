import logging
import time

from collections import defaultdict

from emojirades.handlers import get_config_handler


module_logger = logging.getLogger("EmojiradesBot.scorekeeper")

LEADERBOARD_LIMIT = 15
HISTORY_LIMIT = 5


class ScoreKeeper:
    """
    self.scoreboard = {
       "channel_a": {
           "scores": {
               player1: 100,
               player2: 50
           },
           "history": [
           {
                'timestamp': 1593565068.205327,
                'user_id': player1,
                'operation': "++"
            },
            {
                'timestamp': 1593565068.205327,
                'user_id': player2,
                'operation': "++"
            }]
        }
    }
    """

    def __init__(self, score_uri):
        self.config = get_config_handler(score_uri)
        self.logger = logging.getLogger("EmojiradesBot.scorekeeper.ScoreKeeper")

        def scoreboard_factory():
            return {
                "scores": defaultdict(int),
                "history": [],
            }

        existing_state = self.config.load()

        if not existing_state:
            self.scoreboard = defaultdict(scoreboard_factory)
        else:
            self.scoreboard = defaultdict(scoreboard_factory, existing_state)

            for config in self.scoreboard.values():
                config["scores"] = defaultdict(int, config["scores"])

            self.logger.info(f"Loaded scores from {score_uri}")

        self.command_history = []

    def current_score(self, channel, user):
        leaderboard = list(
            map(
                lambda x: x[0],
                sorted(
                    self.scoreboard[channel]["scores"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                ),
            )
        )

        try:
            position = leaderboard.index(user) + 1
        except ValueError:
            # User is not in the leaderboard
            position = -1

        return self.scoreboard[channel]["scores"][user], position

    def plusplus(self, channel, user):
        self.scoreboard[channel]["scores"][user] += 1
        self.scoreboard[channel]["history"].append(self.history_template(user, "++"))
        self.save()
        return self.current_score(channel, user)

    def minusminus(self, channel, user):
        self.scoreboard[channel]["scores"][user] -= 1
        self.scoreboard[channel]["history"].append(self.history_template(user, "--"))
        self.save()
        return self.current_score(channel, user)

    def overwrite(self, channel, user, score):
        self.scoreboard[channel]["scores"][user] = score
        self.scoreboard[channel]["history"].append(
            self.history_template(user, f"Manually set to {score}")
        )
        self.save()
        return self.current_score(channel, user)

    @staticmethod
    def history_template(user, operation):
        return {"operation": operation, "timestamp": time.time(), "user_id": user}

    def leaderboard(self, channel, limit=LEADERBOARD_LIMIT):
        return sorted(
            self.scoreboard[channel]["scores"].items(),
            key=lambda i: (i[1], i[0]),
            reverse=True,
        )[:limit]

    def history(self, channel, limit=HISTORY_LIMIT):
        return self.raw_history(channel)[-limit:][::-1]

    def raw_history(self, channel):
        return self.scoreboard[channel]["history"]

    def save(self):
        self.config.save(self.scoreboard)
