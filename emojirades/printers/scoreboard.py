import datetime
import logging

from emojirades.analytics.time_range import TimeRange
from emojirades.analytics.time_unit import TimeUnit


class ScoreboardPrinter:
    def __init__(
        self, data, slack, time_unit: TimeUnit, parsed_date: datetime.datetime
    ):
        self.scoreboard = data
        self.slack = slack
        self.time_unit = time_unit
        self.parsed_date = parsed_date

        self.logger = logging.getLogger("EmojiradesBot.printers.ScoreboardPrinter")

    def print_date_range(self):
        date_range = ""

        if self.time_unit in [TimeUnit.WEEKLY, TimeUnit.MONTHLY]:
            start = TimeRange.get_start_date(self.parsed_date, self.time_unit).strftime(
                "%Y-%m-%d"
            )
            end = TimeRange.get_end_date(self.parsed_date, self.time_unit).strftime(
                "%Y-%m-%d"
            )
            date_range = f"({start} - {end})"

        return date_range

    def print_title(self):
        title = [
            "",
            "::",
            f"{self.time_unit.value.title()}",
            "leaderboard",
        ]

        if date_range := self.print_date_range():
            title.append(date_range)

        title.append("::")

        return " ".join(title)

    def print(self):
        self.logger.debug("Printing leaderboard: %s", self.scoreboard)

        if not self.scoreboard:
            yield None, "Nothing to see here!"
            return

        # Prepare and truncate names
        processed_scoreboard = []
        for name_id, score in self.scoreboard:
            if score <= 0:
                continue
            name = self.slack.pretty_name(name_id)
            if len(name) >= 20:
                name = f"{name[:18]}.."
            processed_scoreboard.append((name, score))

        if not processed_scoreboard:
            yield None, "Nothing to see here!"
            return

        lines = ["```", self.print_title(), ""]

        # Calculate the max width of the name and score columns
        longest_name = max(len(name) for name, _ in processed_scoreboard)
        biggest_score = max(len(str(score)) for _, score in processed_scoreboard)

        rank_buffer = 0
        last_score = 0

        for pos, (name, score) in enumerate(processed_scoreboard, start=1):
            if score == last_score:
                rank_buffer -= 1
            elif rank_buffer < 0:
                rank_buffer = 0

            last_score = score

            points_str = "point" if score == 1 else "points"
            lines.append(
                f"{pos + rank_buffer:>2}. {name:<{longest_name}}"
                + f" [ {score:>{biggest_score}} {points_str:<6} ]"
            )

        lines.append("```")

        yield None, "\n".join(lines)
