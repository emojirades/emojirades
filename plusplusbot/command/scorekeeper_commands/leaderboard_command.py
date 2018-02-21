from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class LeaderboardCommand(ScoreKeeperCommand):
    pattern = "<@{me}> leaderboard"
    description = "Shows all the users scores"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        leaderboard = self.scorekeeper.leaderboard()

        self.logger.debug("Printing leaderboard: {0}".format(leaderboard))

        yield (None, "\n".join(["{0}. <@{1}> [{2} point{3}]".format(index + 1, name, score, "s" if score > 1 else "")
                                for index, (name, score) in enumerate(leaderboard)]))

    def __str__(self):
        return "LeaderboardCommand"
