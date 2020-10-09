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
        r"<@{me}> (score|leader)[\s]*board$",
        r"<@{me}> (score|leader)[\s]*board (?P<range>weekly|monthly) (?P<on_date>[0-9]{{8}})",
        r"<@{me}> (score|leader)[\s]*board (?P<range>weekly|monthly|all time)",
    )

    examples = [
        ("<@{me}> scoreboard", "Show user scores"),
        ("<@{me}> scoreboard weekly|monthly|all time", "Show user scores on different brackets"),
        ("<@{me}> scoreboard weekly|monthly YYYYMMDD", "Show user weekly or monthly scores from a different date"),
        ("<@{me}> leaderboard", "Alternative name for scoreboard"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: :thinking: Maybe we could add default value regex in the command translation
        self.time_unit = TimeUnit(self.args.get("range", TimeUnit.WEEKLY.value))
        self.on_date = self.args.get("on_date")

    def execute(self):
        yield from super().execute()

        of_date = pendulum.now(tz=self.TZ)

        if self.time_unit == TimeUnit.ALL_TIME:
            leaderboard = self.scorekeeper.leaderboard(self.args["channel"])
        else:
            self.logger.debug(f"Getting a {self.time_unit} leaderboard")
            history = self.scorekeeper.raw_history(self.args["channel"])

            mock_date = os.environ.get("EMOJIRADE_MOCK_DATE")
            if self.on_date:
                of_date = pendulum.from_format(self.on_date, "YYYYMMDD", tz=self.TZ)
                self.logger.info(f"User requested date to: {of_date}")
            elif mock_date:
                # Mockable date
                of_date = pendulum.from_format(mock_date, "YYYYMMDD", tz=self.TZ)
                self.logger.info(f"Mocking date to: {of_date}")

            lb = LeaderBoard(history)
            leaderboard = lb.get(of_date, self.time_unit)

        leaderboard_printer = LeaderboardPrinter(leaderboard, self.slack, self.time_unit, of_date)

        yield from leaderboard_printer.print()
