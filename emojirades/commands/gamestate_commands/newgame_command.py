from emojirades.wrappers import admin_or_old_winner_set_check
from emojirades.commands import BaseCommand


class NewGameCommand(BaseCommand):
    description = "Initiate a new game by setting the Old Winner and the Winner"

    patterns = (
        r"<@{me}> new[\s]*game <@(?P<old_winner>[0-9A-Z]+)> <@(?P<winner>[0-9A-Z]+)>",
    )

    examples = [
        ("<@{me}> new game @old_winner @winner", "Initiates a new game"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    @admin_or_old_winner_set_check
    def execute(self):
        yield from super().execute()

        if self.args["winner"] == self.args["old_winner"]:
            yield (
                None,
                f"Sorry, but the old and current winner cannot be the same person (<@{self.args['winner']}>)...",
            )
            return

        self.gamestate.new_game(
            self.args["channel"], self.args["old_winner"], self.args["winner"]
        )
        yield (
            None,
            f"<@{self.args['user']}> has set the old winner to <@{self.args['old_winner']}> and the winner to <@{self.args['winner']}>",
        )
        yield (
            None,
            f"It's now <@{self.args['old_winner']}>'s turn to provide <@{self.args['winner']}> with the next 'rade!",
        )
        yield (
            self.args["old_winner"],
            f"You'll now need to send me the new 'rade for <@{self.args['winner']}>",
        )
        yield (
            self.args["old_winner"],
            "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade",
        )
