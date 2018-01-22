
from plusplusbot.handlers import get_configuration_handler
from plusplusbot.commands import Command
from plusplusbot.wrappers import only_in_progress, admin_check
from collections import defaultdict

import logging
import csv
import re
import io

module_logger = logging.getLogger("PlusPlusBot.scorekeeper")

leaderboard_limit = 10
history_limit = 5

def get_handler(filename):
    class ScoreKeeperConfigurationHandler(get_configuration_handler(filename)):
        """
        Handles CRUD for the ScoreKeeper configuration file
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            if bytes_content is None:
                return None

            score_file = io.StringIO(bytes_content.decode("utf-8"))

            return {user: int(score) for (user, score) in csv.reader(score_file)}

        def save(self, scores):
            output = io.StringIO()

            writer = csv.writer(output)
            writer.writerows(scores.items())

            bytes_content = output.getvalue().encode("utf-8")

            super().save(bytes_content)

    return ScoreKeeperConfigurationHandler(filename)


class ScoreKeeper(object):
    def __init__(self, filename):
        self.logger = logging.getLogger("PlusPlusBot.scorekeeper.ScoreKeeper")
        self.config = get_handler(filename)
        self.scoreboard = defaultdict(int)
        self.history = []

        if filename:
            existing_state = self.config.load()

            if existing_state is not None:
                self.scoreboard.update(existing_state)
                self.logger.info("Loaded scores from {0}".format(filename))

    def plusplus(self, user):
        self.scoreboard[user] += 1
        self.history.append((user, "++"))
        self.config.flush()

    def minusminus(self, user):
        self.scoreboard[user] -= 1
        self.history.append((user, "--"))
        self.config.flush()

    def overwrite(self, user, score):
        self.scoreboard[user] = score
        self.history.append((user, score))
        self.config.flush()

    def leaderboard(self, limit=leaderboard_limit):
        return sorted(self.scoreboard.items(), key=lambda i: (i[1], i[0]), reverse=True)[:limit]

    def history(self, limit=history_limit):
        return self.history[::-1][:limit]

    def save(self):
        self.config.save(self.scoreboard)

    @property
    def commands(self):
        return [
            PlusPlusCommand,
            MinusMinusCommand,
            SetCommand,
            LeaderboardCommand,
            HistoryCommand,
        ]


class ScoreKeeperCommand(Command):
    def __init__(self, *args, **kwargs):
        self.scorekeeper = kwargs.pop("scorekeeper")
        self.gamestate = kwargs.pop("gamestate")
        super().__init__(*args, **kwargs)


class InferredPlusPlusCommand(ScoreKeeperCommand):
    pattern = None
    description = "Increments the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = event["user"]
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        target_user = self.args["target_user"]

        self.logger.debug("Incrementing user's score: {}".format(target_user))
        self.scorekeeper.plusplus(target_user)

        score = self.scorekeeper.scoreboard[target_user]

        message = "Congrats <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))

    def __str__(self):
        return "InferredPlusPlusCommand"


class PlusPlusCommand(ScoreKeeperCommand):
    pattern = "<@([0-9A-Z]+)>[\s]*\+\+"
    description = "Increment the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"]).group(1)
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] == target_user:
            yield (None, ":thinking_face: you're not allowed to award points to yourself...")
            raise StopIteration

        if self.slack.is_bot(target_user):
            yield (None, ":thinking_face: robots aren't allowed to play Emojirades!")
            raise StopIteration

        self.logger.debug("Incrementing user's score: {}".format(target_user))
        self.scorekeeper.plusplus(target_user)

        score = self.scorekeeper.scoreboard[target_user]

        message = "Congrats <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))

    def __str__(self):
        return "PlusPlusCommand"


class SetCommand(ScoreKeeperCommand):
    pattern = "<@([0-9A-Z]+)> set (-?[0-9]+)"
    description = "Manually set the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]

        matches = re.match(self.pattern, event["text"])
        self.args["target_user"] = matches.group(1)
        self.args["new_score"] = matches.group(2)

    @admin_check
    def execute(self):
        target_user = self.args["target_user"]
        new_score = int(self.args["new_score"])

        if self.args["user"] == target_user:
            yield ":thinking_face: you can't do that to yourself"
            raise StopIteration

        if self.slack.is_bot(target_user):
            yield ":thinking_face: robots aren't allowed to play Emojirades"
            raise StopIteration

        self.logger.debug("Setting {} score to: {}".format(target_user, new_score))
        self.scorekeeper.overwrite(target_user, new_score)

        message = "<@{0}> manually set to {1} point{2}"
        yield (None, message.format(target_user, new_score, "s" if new_score > 1 else ""))

    def __str__(self):
        return "SetCommand"


class MinusMinusCommand(ScoreKeeperCommand):
    pattern = "<@([0-9A-Z]+)> --"
    description = "Decrement the users score"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"]).group(1)
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @admin_check
    def execute(self):
        target_user = self.args["target_user"]

        if self.args["user"] == target_user:
            yield ":thinking_face: you're not allowed to deduct points from yourself..."
            raise StopIteration

        if self.slack.is_bot(target_user):
            yield ":thinking_face: robots aren't allowed to play Emojirades!"
            raise StopIteration

        self.logger.debug("Decrementing user's score: {}".format(target_user))
        self.scorekeeper.minusminus(target_user)

        score = self.scorekeeper.scoreboard[target_user]

        message = "Oops <@{0}>, you're now at {1} point{2}"
        yield (None, message.format(target_user, score, "s" if score > 1 else ""))

    def __str__(self):
        return "MinusMinusCommand"


class LeaderboardCommand(ScoreKeeperCommand):
    pattern = "<@{me}> leaderboard"
    description = "Shows all the users scores"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        leaderboard = self.scorekeeper.leaderboard()

        self.logger.debug("Printing leaderboard: {0}".format(leaderboard))

        yield (None, "\n".join(["{0}. <@{1}> [{2} point{3}]".format(index + 1, name, score, "s" if score > 1 else "")
                               for index, (name, score) in enumerate(leaderboard)]))

    def __str__(self):
        return "LeaderboardCommand"


class HistoryCommand(ScoreKeeperCommand):
    pattern = "<@{me}> history"
    description = "Shows the latest few actions performed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        history = self.scorekeeper.history()

        self.logger.debug("Printing history: {0}".format(history))

        yield (None, "\n".join(["{0}. <@{1}> > '{2}'".format(index + 1, name, action)
                               for index, (name, action) in enumerate(history)]))

    def __str__(self):
        return "HistoryCommand"
