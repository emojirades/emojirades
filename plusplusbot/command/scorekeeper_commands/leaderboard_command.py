from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class LeaderboardCommand(ScoreKeeperCommand):
    pattern = "<@{me}> leaderboard"
    description = "Shows all the users scores"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        for i in super().execute():
            yield i

        leaderboard = self.scorekeeper.leaderboard(self.args["channel"])

        self.logger.debug("Printing leaderboard: {0}".format(leaderboard))

        lines = []

        for index, (name, score) in enumerate(leaderboard):
            lines.append("{0}. {1} [{2} point{3}]".format(
                index + 1,
                self.slack.pretty_name(name),
                score,
                "s" if score > 1 else ""
            ))

        yield (None, "\n".join(lines))
