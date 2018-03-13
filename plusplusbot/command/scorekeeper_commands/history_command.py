from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class HistoryCommand(ScoreKeeperCommand):
    pattern = "<@{me}> history"
    description = "Shows the latest few actions performed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        history = self.scorekeeper.history()

        self.logger.debug("Printing history: {0}".format(history))

        yield (None, "\n".join(["{0}. <@{1}> > '{2}'".format(index + 1, name, action)
                                for index, (name, action) in enumerate(history)]))

    def __str__(self):
        return "HistoryCommand"
