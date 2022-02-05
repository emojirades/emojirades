import pendulum

from emojirades.commands import BaseCommand


class HistoryCommand(BaseCommand):
    description = "Shows the latest few actions performed"
    max_history = 50

    patterns = (
        r"<@{me}> history <@(?P<target_user>[0-9A-Z]+)> (?P<limit>[0-9]+)",
        r"<@{me}> history <@(?P<target_user>[0-9A-Z]+)>",
        r"<@{me}> history (?P<limit>[0-9]+)",
        r"<@{me}> history",
    )

    examples = [
        ("<@{me}> history", "Shows scoreboard history"),
        ("<@{me}> history @user", "Shows scoreboard history for a specific user"),
        ("<@{me}> history 20", "Shows last 20 history events"),
    ]

    def prepare_args(self, event):
        super().prepare_args(event)

        if "limit" in self.args:
            try:
                self.args["limit"] = int(self.args["limit"])

                if self.args["limit"] > self.max_history:
                    self.args["limit"] = self.max_history
            except ValueError:
                self.args.pop("limit")

    def execute(self):
        yield from super().execute()

        kwargs = {}

        if "target_user" in self.args:
            kwargs["user"] = self.args["target_user"]

        if "limit" in self.args:
            kwargs["limit"] = self.args["limit"]

        history = self.scorekeeper.history(self.args["channel"], **kwargs)

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
