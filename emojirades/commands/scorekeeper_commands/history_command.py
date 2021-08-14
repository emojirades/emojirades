import datetime

from emojirades.commands import BaseCommand


class HistoryCommand(BaseCommand):
    description = "Shows the latest few actions performed"

    patterns = (r"<@{me}> history",)

    examples = [
        ("<@{me}> history", "Shows history"),
    ]

    def execute(self):
        yield from super().execute()

        history = self.scorekeeper.history(self.args["channel"])

        if not history:
            message = (
                "No history available."
                "History is temporary and doesn't persist across bot restarts."
            )
            self.logger.debug(message)
            yield (None, message)
            return

        self.logger.debug("Printing history: %s", history)

        now = datetime.datetime.utcnow()

        history_log = []

        for (user_id, timestamp, operation) in history:
            ago = (now - timestamp).seconds
            name = self.slack.pretty_name(user_id)
            command, prev, curr = operation.split(",")

            line = f"{ago:>4}s ago: {name}: {command} {prev} => {curr}"
            history_log.append(line)

        yield (None, "\n".join(history_log))
