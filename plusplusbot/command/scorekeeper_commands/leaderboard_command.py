from plusplusbot.command.scorekeeper_commands.scorekeeper_command import ScoreKeeperCommand


class LeaderboardCommand(ScoreKeeperCommand):
    description = "Shows all the users scores"
    short_description = "Show user scores"

    patterns = (
        r"<@{me}> (score|leader)[\s]*board",
    )
    example = "<@{me}> scoreboard"

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

        longest_name = 0
        biggest_score = 0

        for (name, score) in leaderboard:
            name_length = len(name)
            score_length = len(str(score))

            if name_length > longest_name:
                longest_name = name_length

            if score_length > biggest_score:
                biggest_score = score_length

        for index, (name, score) in enumerate(leaderboard):
            name = self.slack.pretty_name(name)

            lines.append("{0:>2}. {1:<{name_width}} [ {2:>{point_width}} point{3} ]".format(
                index + 1,
                name if len(name) < 20 else "{0}..".format(name[0:18]),
                score,
                "s" if score > 1 else " ",
                name_width=longest_name,
                point_width=biggest_score,
            ))

        lines.append("```")

        yield (None, "\n".join(lines))
