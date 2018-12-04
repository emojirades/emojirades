from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class LeaderboardCommand(ScoreKeeperCommand):
    patterns = (
        r"<@{me}> (score|leader)[\s]*board",
    )

    description = "Shows all the users scores"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        yield from super().execute()

        leaderboard = self.scorekeeper.leaderboard(self.args["channel"])

        self.logger.debug("Printing leaderboard: {0}".format(leaderboard))

        if not leaderboard:
            yield (None, "Nothing to see here!")
            return

        lines = ["```"]

        longest_name = max(len(name) for (name, score) in leaderboard)
        biggest_score = len(str(max(score for (name, score) in leaderboard)))

        for index, (name, score) in enumerate(leaderboard):
            name = self.slack.pretty_name(name)

            lines.append("{0:>2}. {1:<{name_width}} [{2:>{point_width}} point{3}]".format(
                index + 1,
                name if len(name) < 20 else "{0}..".format(name[0:18]),
                score,
                "s" if score > 1 else " ",
                name_width=longest_name + 1,
                point_width=biggest_score + 1,
            ))

        lines.append("```")

        yield (None, "\n".join(lines))
