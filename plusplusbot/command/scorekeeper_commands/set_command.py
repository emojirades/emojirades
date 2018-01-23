from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand
from plusplusbot.wrappers import admin_check


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