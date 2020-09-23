from emojirades.commands import BaseCommand


class HistoryCommand(BaseCommand):
    description = "Shows the latest few actions performed"

    patterns = (r"<@{me}> history",)

    examples = [
        ("<@{me}> history", "Shows history"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        yield from super().execute()

        history = self.scorekeeper.history(self.args["channel"])

        if not history:
            message = "No history available. History is temporary and doesn't persist across bot restarts."
            self.logger.debug(message)
            yield (None, message)
            return

        self.logger.debug(f"Printing history: {history}")

        history_log = [
            f"{index}. {self.slack.pretty_name(event['user_id'])} > '{event['operation']}'"
            for index, event in enumerate(history, start=1)
        ]
        last_message = [
            "This is an in-memory log and only up-to-date from the last bot restart."
        ]

        yield (None, "\n".join(history_log + last_message))
