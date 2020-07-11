from emojirades.commands import BaseCommand
from emojirades.wrappers import admin_check


class GameStatusCommand(BaseCommand):
    description = "Prints out the game status"

    patterns = (r"<@{me}> (game[\s]*){{0,1}}(status|state)",)

    examples = [
        ("<@{me}> game status", "Print game status"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.masked_emojirade = True

    def prepare_args(self, event):
        super().prepare_args(event)

    def execute(self):
        yield from super().execute()

        status = self.gamestate.game_status(self.args["channel"])
        pretty_status = []

        # self.slack.pretty_name(name)

        args = {
            "old_winner_name": self.slack.pretty_name(status["old_winner"]),
            "winner_name": self.slack.pretty_name(status["winner"]),
            "old_winner": status["old_winner"],
            "winner": status["winner"],
        }

        # First item is game state (step)
        step_msg = {
            "new_game": f"Game has not started yet, please wait for an admin to start it!",
            "waiting": f"Waiting for <@{args['old_winner']}> to provide a 'rade to {args['winner_name']}",
            "provided": f"Waiting for <@{args['winner']}> to post an emoji to kick off the round!",
            "guessing": f"Come on, everyone's guessing what {args['winner_name']} has posted! Get to it! :runner::dash:",
        }

        pretty_status.append(("Status", step_msg[status["step"]]))

        yield (None, "\n".join(f"{k}: {v}" for k, v in pretty_status))
