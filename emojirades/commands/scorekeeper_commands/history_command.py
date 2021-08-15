import pendulum

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
            message = "No history available."
            self.logger.debug(message)
            yield (None, message)
            return

        self.logger.debug("Printing history: %s", history)

        now = pendulum.now(tz=pendulum.UTC)
        history_log = []

        for item in history:
            ago = item["timestamp"].diff_for_humans(now).replace("before", "ago")
            name = self.slack.pretty_name(item["user_id"])
            command, prev, curr = item["operation"].split(",")

            line = f"{ago:<15}: {name:<20}: {command:>5} {prev:>5} => {curr:>5}"
            history_log.append(line)

        yield (None, "```" + "\n".join(history_log) + "```")
