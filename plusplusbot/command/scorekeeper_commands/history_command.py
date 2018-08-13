from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class HistoryCommand(ScoreKeeperCommand):
    pattern = "<@{me}> history"
    description = "Shows the latest few actions performed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        for i in super().execute():
            yield i

        history = self.scorekeeper.history()

        if not history:
            self.logger.debug("No history available. History is temporary and doesn't persist across bot restarts.")
            yield (None, "No history available. History is temporary and doesn't persist across bot restarts.")
            raise StopIteration

        self.logger.debug("Printing history: {0}".format(history))

        yield (None, "\n".join(["{0}. <@{1}> > '{2}'".format(index + 1, name, action)
                                for index, (name, action) in enumerate(history)] + ["This is an in-memory log and only up-to-date from the last bot restart."]))
