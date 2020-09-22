import logging

import pendulum

from emojirades.analytics.time_range import TimeRange


class LeaderboardPrinter:
    def __init__(self, data, slack, time_unit, of_date: pendulum.DateTime):
        self.data = data
        self.logger = logging.getLogger("EmojiradesBot.printers.LeaderboardPrinter")
        self.slack = slack
        self.time_unit = time_unit
        self.of_date = of_date

    def print_date_range(self):
        date_range = ""
        if self.time_unit in [TimeRange.WEEKLY, TimeRange.MONTHLY]:
            start = TimeRange.get_start_date(self.of_date, self.time_unit).format("YYYY-MM-DD")
            end = TimeRange.get_end_date(self.of_date, self.time_unit).format("YYYY-MM-DD")
            date_range = f"({start} - {end})"

        return date_range

    def print(self):
        leaderboard = self.data

        self.logger.debug(f"Printing leaderboard: {leaderboard}")

        if not leaderboard:
            yield None, "Nothing to see here!"
            return

        title = []
        title.append("")
        title.append("::")
        title.append(f"{self.time_unit.title()}")
        title.append("leaderboard")
        if self.print_date_range():
            title.append(self.print_date_range())
        title.append("::")

        lines = [
            "```",
            " ".join(title),
            ""]

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

        yield None, "\n".join(lines)
