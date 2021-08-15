from emojirades.commands import BaseCommand

from emojirades.persistence import GamestateStep


class GameStatusCommand(BaseCommand):
    description = "Prints out the game status"

    patterns = (r"<@{me}> (game[\s]*){{0,1}}(status|state)",)

    examples = [
        ("<@{me}> game status", "Print game status"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.masked_emojirade = True

    def execute(self):
        yield from super().execute()

        channel = self.args["channel"]
        (previous_winner, current_winner) = self.gamestate.winners(channel)
        current_winner_name = self.slack.pretty_name(current_winner)

        step = self.gamestate.step(channel)

        if step == GamestateStep.NEW_GAME:
            status = "Game has not started yet, please wait for an admin to start it!"
        elif step == GamestateStep.WAITING:
            status = f"Waiting for <@{previous_winner}> to provide a 'rade to {current_winner_name}"
        elif step == GamestateStep.PROVIDED:
            status = f"Waiting for <@{current_winner}> to post an emoji to kick off the round!"
        elif step == GamestateStep.GUESSING:
            status = (
                f"Come on, everyone's guessing what {current_winner_name} has posted! "
                "Get to it! :runner::dash:"
            )
        else:
            status = "Not entirely sure what the state of this game is in... :shrug:"

        yield (None, f"Status: {status}")
