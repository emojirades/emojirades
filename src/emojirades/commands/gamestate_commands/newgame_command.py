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

    @admin_or_old_winner_set_check
    def execute(self):
        yield from super().execute()

        user = self.args["user"]

        previous_winner = self.args["old_winner"]
        current_winner = self.args["winner"]

        previous_winner_name = self.slack.pretty_name(previous_winner)
        current_winner_name = self.slack.pretty_name(current_winner)

        if current_winner == previous_winner:
            yield (
                None,
                "Sorry, but the old and current winner "
                f"cannot be the same person (<@{current_winner}>)...",
            )
            return

        self.gamestate.new_game(self.args["channel"], previous_winner, current_winner)

        yield (
            None,
            f"<@{user}> has set the old winner to {previous_winner_name} "
            f"and the winner to {current_winner_name}",
        )
        yield (
            None,
            f"It's now <@{previous_winner}>'s turn "
            f"to provide {current_winner_name} with the next 'rade!",
        )
        yield (
            previous_winner,
            f"You'll now need to send me the new 'rade for <@{current_winner}>",
        )
        yield (
            previous_winner,
            "Please reply back in the format `emojirade Point Break` "
            "if `Point Break` was the new 'rade",
        )
