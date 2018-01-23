import re

from plusplusbot.command.gamestate_commands.gamestate_command import GameStateCommand
from plusplusbot.wrappers import admin_check


class NewGame(GameStateCommand):
    pattern = "<@{me}> new game <@([0-9A-Z]+)> <@([0-9A-Z]+)>"
    description = "Initiate a new game by setting the Old Winner and the Winner"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        rendered_pattern = self.pattern.format(me=self.slack.bot_id)

        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]
        self.args["old_winner"] = re.match(rendered_pattern, event["text"]).group(1)
        self.args["winner"] = re.match(rendered_pattern, event["text"]).group(2)

    @admin_check
    def execute(self):
        if self.args["winner"] == self.args["old_winner"]:
            yield (None, "Sorry, but the old and current winner cannot be the same person (<@{winner}>)...".format(**self.args))
            raise StopIteration

        self.gamestate.new_game(self.args["channel"], self.args["old_winner"], self.args["winner"])
        yield (None, "<@{user}> has set the old winner to <@{old_winner}> and the winner to <@{winner}>".format(**self.args))
        yield (None, "It's now <@{old_winner}>'s turn to provide <@{winner}> with the next 'rade!".format(**self.args))
        yield (self.args["old_winner"], "You'll now need to send me the new 'rade for <@{winner}>".format(**self.args))
        yield (self.args["old_winner"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
