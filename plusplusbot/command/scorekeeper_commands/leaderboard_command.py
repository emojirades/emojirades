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

        if not leaderboard:
            yield (None, "Nothing to see here!")
            raise StopIteration

        lines = ["```"]

        for index, (name, score) in enumerate(leaderboard):
            name = self.slack.pretty_name(name)

            lines.append("{0:>2}. {1:<20} [{2:>3} point{3}]".format(
                index + 1,
                name if len(name) < 20 else "{0}..".format(name[0:18]),
                score,
                "s" if score > 1 else ""
            ))

        lines.append("```")

        yield (None, "\n".join(lines))
