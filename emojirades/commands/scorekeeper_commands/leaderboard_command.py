import os

import pendulum

from emojirades.analytics.leaderboard import LeaderBoard
from emojirades.analytics.time_unit import TimeUnit
from emojirades.commands import BaseCommand
from emojirades.printers.leaderboard_printer import LeaderboardPrinter


class LeaderboardCommand(BaseCommand):

    TZ = "Australia/Melbourne"
    description = "Shows all the users scores"

    patterns = (
        r"<@{me}>[\s]+(?:score|leader)[\s]*board(?P<all_boards>s){{0,1}}$",
        r"<@{me}>[\s]+(?:score|leader)[\s]*board (?P<range>weekly|monthly) (?P<user_date>[0-9]{{8}})",
        r"<@{me}>[\s]+(?:score|leader)[\s]*board (?P<range>weekly|monthly|all time|alltime|all|everything)",
    )

    examples = [
        ("<@{me}> scoreboard", "Show current weekly scoreboard (default)"),
        ("<@{me}> scoreboards", "Show all scoreboards"),
        (
            "<@{me}> scoreboard weekly|monthly|all time",
            "Show user scores on different brackets",
        ),
        (
            "<@{me}> scoreboard weekly|monthly YYYYMMDD",
            "Show user weekly or monthly scores from a different date",
        ),
        ("<@{me}> leaderboard", "Alternative name for scoreboard"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        all_time_values = ["all time", "alltime", "all", "everything"]

        if self.args.get("range") in all_time_values:
            self.args["range"] = "all time"

        if self.args.get("all_boards"):
            self.time_units = (
                TimeUnit.WEEKLY,
                TimeUnit.MONTHLY,
                TimeUnit.ALL_TIME,
            )
        else:
            self.time_units = (TimeUnit(self.args.get("range", TimeUnit.WEEKLY.value)),)

    def get_leaderboard(self, time_unit: TimeUnit):
        """
        Given a time unit and a date, return the appropriate leaderboard
        """
        self.logger.debug(f"Getting a {time_unit} leaderboard")

        if time_unit == TimeUnit.ALL_TIME:
            return self.scorekeeper.leaderboard(self.args["channel"]), None

        all_history = self.scorekeeper.raw_history(self.args["channel"])
        lb = LeaderBoard(all_history)

        mock_date = os.environ.get("EMOJIRADE_MOCK_DATE")

        if (mock_date := os.environ.get("EMOJIRADE_MOCK_DATE")) :
            date = mock_date
        else:
            if self.args.get("user_date"):
                date = self.args["user_date"]
            else:
                date = pendulum.now(tz=self.TZ).strftime("%Y%m%d")

        parsed_date = pendulum.from_format(date, "YYYYMMDD", tz=self.TZ)
        self.logger.debug("Leaderboard date was set to: {parsed_date}")

        return (lb.get(parsed_date, time_unit), parsed_date)

    def execute(self):
        yield from super().execute()

        for time_unit in self.time_units:
            leaderboard, parsed_date = self.get_leaderboard(time_unit)

            leaderboard_printer = LeaderboardPrinter(
                leaderboard, self.slack, time_unit, parsed_date
            )

            yield from leaderboard_printer.print()
