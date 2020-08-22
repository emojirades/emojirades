import logging


class LeaderboardPrinter:
    def __init__(self, data, slack):
        self.data = data
        self.logger = logging.getLogger("EmojiradesBot.printers.LeaderboardPrinter")
        self.slack = slack

    def print(self):
        leaderboard = self.data

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
