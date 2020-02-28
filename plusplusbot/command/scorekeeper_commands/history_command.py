from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class HistoryCommand(ScoreKeeperCommand):
    description = "Shows the latest few actions performed"
    short_description = "Shows history"

    patterns = (
        r"<@{me}> history",
    )
    example = "<@{me}> history"

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

        self.logger.debug("Printing history: {history}")

        history_log = [f"{index}. <@{name}> > '{action}'" for index, (name, action) in enumerate(history, start=1)]
        last_message = ["This is an in-memory log and only up-to-date from the last bot restart."]

        yield (None, "\n".join(history_log + last_message))
