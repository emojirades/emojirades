import pendulum
import logging

from emojirades.analytics.time_range import TimeRange
from emojirades.analytics.time_unit import TimeUnit


class LeaderboardPrinter:
    def __init__(
        self, data, slack, time_unit: TimeUnit, parsed_date: pendulum.DateTime
    ):
        self.data = data
        self.logger = logging.getLogger("EmojiradesBot.printers.LeaderboardPrinter")
        self.slack = slack
        self.time_unit = time_unit
        self.parsed_date = parsed_date

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
        title = []
        title.append("")
        title.append("::")
        title.append(f"{self.time_unit.value.title()}")
        title.append("leaderboard")
        if self.print_date_range():
            title.append(self.print_date_range())
        title.append("::")

        return " ".join(title)

    def print(self):
        leaderboard = self.data

        self.logger.debug(f"Printing leaderboard: {leaderboard}")

        if not leaderboard:
            yield None, "Nothing to see here!"
            return

        lines = ["```", self.print_title(), ""]

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

        rank_buffer = 0
        last_score = 0

        for index, (name, score) in enumerate(leaderboard, start=1):
            name = self.slack.pretty_name(name)
            name = name if len(name) < 20 else "{name[0:18]}.."

            if score == last_score:
                rank_buffer -= 1
            elif rank_buffer < 0:
                rank_buffer = 0

            last_score = score

            lines.append(
                f"{index + rank_buffer:>2}. {name:<{longest_name}} [ {score:>{biggest_score}} point{'s' if score > 1 else ' '} ]"
            )

        lines.append("```")

        yield None, "\n".join(lines)
