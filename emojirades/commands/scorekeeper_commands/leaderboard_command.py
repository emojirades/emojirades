import pendulum

from emojirades.analytics.leaderboard import LeaderBoard
from emojirades.analytics.time_range import TimeRange
from emojirades.commands import BaseCommand
from emojirades.printers.leaderboard_printer import LeaderboardPrinter


class LeaderboardCommand(BaseCommand):

    description = "Shows all the users scores"

    patterns = (
        r"<@{me}> (score|leader)[\s]*board$",
        r"<@{me}> (score|leader)[\s]*board (?P<range>weekly|monthly|all time)",
    )

    examples = [
        ("<@{me}> scoreboard", "Show user scores"),
        ("<@{me}> scoreboard weekly|monthly|all time", "Show user scores on different brackets"),
        ("<@{me}> leaderboard", "Alternative name for scoreboard"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: :thinking: Maybe we could add default value regex in the command translation
        self.time_unit = self.args.get("range", TimeRange.WEEKLY)

    def execute(self):
        yield from super().execute()
        leaderboard = []

        if self.time_unit == TimeRange.ALL_TIME:
            leaderboard = self.scorekeeper.leaderboard(self.args["channel"])
        else:
            self.logger.debug(f"Getting a {self.time_unit} leaderboard")
            history = self.scorekeeper.raw_history(self.args["channel"])
            of_date = pendulum.now("Australia/Melbourne")
            lb = LeaderBoard(history)

            if self.time_unit == TimeRange.WEEKLY:
                leaderboard = lb.get_week(of_date)
            elif self.time_unit == TimeRange.MONTHLY:
                leaderboard = lb.get_month(of_date)

        leaderboard_printer = LeaderboardPrinter(leaderboard, self.slack, self.time_unit)
        yield from leaderboard_printer.print()
