from emojirades.commands.gamestate_commands.correct_guess_command import (
    CorrectGuessCommand,
)


class InferredCorrectGuessCommand(CorrectGuessCommand):
    description = (
        "Takes the user that send the event as the winner, "
        "this is only ever fired internally"
    )

    patterns = tuple()

    examples = [
        (None, "Internally awards a win"),
    ]

    def prepare_args(self, event):
        super().prepare_args(event)
        self.args["target_user"] = self.args["user"]
        self.args["inferred"] = True
