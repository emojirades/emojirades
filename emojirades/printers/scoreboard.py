import logging

import pendulum

from emojirades.analytics.time_range import TimeRange
from emojirades.analytics.time_unit import TimeUnit


class ScoreboardPrinter:
    def __init__(
        self, data, slack, time_unit: TimeUnit, parsed_date: pendulum.DateTime
    ):
        self.scoreboard = data
        self.slack = slack
        self.time_unit = time_unit
        self.parsed_date = parsed_date

        self.logger = logging.getLogger("EmojiradesBot.printers.ScoreboardPrinter")

    def print_date_range(self):
        date_range = ""

        if self.time_unit in [TimeUnit.WEEKLY, TimeUnit.MONTHLY]:
            start = TimeRange.get_start_date(self.parsed_date, self.time_unit).format(
                "YYYY-MM-DD"
            )
            end = TimeRange.get_end_date(self.parsed_date, self.time_unit).format(
                "YYYY-MM-DD"
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

        lines = ["```", self.print_title(), ""]

        # Calculate the max width of the name and score columns
        longest_name = 0
        biggest_score = 0

        for (name, score) in self.scoreboard:
            name = self.slack.pretty_name(name)

            name_len = len(name)
            score_len = len(str(score))

            if name_len > longest_name:
                longest_name = name_len

            if score_len > biggest_score:
                biggest_score = score_len

        rank_buffer = 0
        last_score = 0

        for pos, (name, score) in enumerate(self.scoreboard, start=1):
            name = self.slack.pretty_name(name)
            name = name if len(name) < 20 else "{name[0:18]}.."

            if score == last_score:
                rank_buffer -= 1
            elif rank_buffer < 0:
                rank_buffer = 0

            last_score = score

            lines.append(
                f"{pos + rank_buffer:>2}. {name:<{longest_name}}"
                + f" [ {score:>{biggest_score}} point{'s' if score > 1 else ' '} ]"
            )

        lines.append("```")

        yield None, "\n".join(lines)
