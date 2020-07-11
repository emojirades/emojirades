import pendulum

from emojirades.analytics.leaderboard import LeaderBoard
from emojirades.commands import BaseCommand


class LeaderboardCommand(BaseCommand):
    description = "Shows all the users scores"

    patterns = (
        r"<@{me}> (score|leader)[\s]*board$",
        r"<@{me}> (score|leader)[\s]*board (?P<range>weekly|monthly)",
    )

    examples = [
        ("<@{me}> scoreboard", "Show user scores"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        yield from super().execute()
        leaderboard = []

        time_unit = self.args.get("range")
        if time_unit:
            self.logger.debug(f"Getting a {time_unit} leaderboard")
            history = self.scorekeeper.raw_history(self.args["channel"])
            of_date = pendulum.now("Australia/Melbourne")
            lb = LeaderBoard(history)

            if time_unit == "weekly":
                leaderboard = lb.get_week(of_date)
            elif time_unit == "monthly":
                leaderboard = lb.get_month(of_date)
        else:
            leaderboard = self.scorekeeper.leaderboard(self.args["channel"])

        self.logger.debug(f"Printing leaderboard: {leaderboard}")

        if not leaderboard:
            yield (None, "Nothing to see here!")
            return

        lines = ["```"]

        longest_name = 0
        biggest_score = 0

        for (name, score) in leaderboard:
            name = self.slack.pretty_name(name)

            name_length = len(name)
            score_length = len(str(score))

            if name_length > longest_name:
                longest_name = name_length

            if score_length > biggest_score:
                biggest_score = score_length

        for index, (name, score) in enumerate(leaderboard, start=1):
            name = self.slack.pretty_name(name)
            name = name if len(name) < 20 else "{name[0:18]}.."

            lines.append(
                f"{index:>2}. {name:<{longest_name}} [ {score:>{biggest_score}} point{'s' if score > 1 else ' '} ]"
            )

        lines.append("```")

        yield (None, "\n".join(lines))
