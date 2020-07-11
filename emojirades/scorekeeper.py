import logging
import json
import time

from collections import defaultdict

from emojirades.handlers import get_configuration_handler


module_logger = logging.getLogger("EmojiradesBot.scorekeeper")

leaderboard_limit = 15
history_limit = 5


def get_handler(filename):
    class ScoreKeeperConfigHandler(get_configuration_handler(filename)):
        """
        Handles CRUD for the ScoreKeeper configuration file
        """

        FILE_ENCODING = "utf-8"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            if bytes_content is None or not bytes_content:
                return None

            conf = json.loads(bytes_content.decode(self.FILE_ENCODING))

            for channel, channel_conf in conf.items():
                channel_conf["scores"] = defaultdict(int, channel_conf["scores"])

            return conf

        def save(self, scoreboard):
            super().save(json.dumps(scoreboard).encode(self.FILE_ENCODING))

    return ScoreKeeperConfigHandler(filename)


class ScoreKeeper(object):
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

    def __init__(self, filename=None):
        self.logger = logging.getLogger("EmojiradesBot.scorekeeper.ScoreKeeper")

        def scoreboard_factory():
            return {
                "scores": defaultdict(int),
                "history": [],
            }

        self.scoreboard = defaultdict(scoreboard_factory)
        self.command_history = []

        self.config = get_handler(filename)

        if filename is not None:
            existing_state = self.config.load()

            if existing_state is not None:
                self.scoreboard = defaultdict(scoreboard_factory, existing_state)
                self.logger.info(f"Loaded scores from {filename}")

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

    def history_template(self, user, operation):
        return {"operation": operation, "timestamp": time.time(), "user_id": user}

    def leaderboard(self, channel, limit=leaderboard_limit):
        return sorted(
            self.scoreboard[channel]["scores"].items(),
            key=lambda i: (i[1], i[0]),
            reverse=True,
        )[:limit]

    def history(self, channel, limit=history_limit):
        return self.raw_history(channel)[-limit:][::-1]

    def raw_history(self, channel):
        return self.scoreboard[channel]["history"]

    def save(self):
        self.config.save(self.scoreboard)
