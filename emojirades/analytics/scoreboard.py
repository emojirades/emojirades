# Thanks to https://github.com/BeheadedKamikaze for his help with the algorithm
import logging
import math

from collections import defaultdict

import pendulum


from emojirades.analytics.time_range import TimeRange
from emojirades.analytics.time_unit import TimeUnit


class ScoreboardAnalytics:
    NOT_FOUND = -1

    def __init__(self, history):
        self.history = history
        self.len = len(history)

        self.logger = logging.getLogger("EmojiradesBot.analytics.ScoreboardAnalytics")

    def find_rows_in_range(self, start_time: float, end_time: float) -> int:
        """
        :param start_time: timestamp of the start of the date range
        :param end_time: timestamp of the end of the date range
        :return: index of matched event in history

        A modified binary search to find a single match of event within the date range.

        - Get an approximate index by comparing requested daterange
          and the earliest and latest timestamp in history
        - If the number of events in history is distributed quiet evenly,
          this will usually match the first time
        - If not matched, jump to the half way point of the remaining events
        """
        low = 0
        high = self.len - 1

        first_time = self.history[low]["timestamp"]
        last_time = self.history[high]["timestamp"]

        self.logger.debug("Starting binary search")

        if end_time < first_time or start_time > last_time:
            self.logger.warning(
                "Date is out of range earliest=%s latest=%s start_time=%s end_time=%s",
                first_time,
                last_time,
                start_time,
                end_time,
            )
            return self.NOT_FOUND

        # History is empty
        if low == high:
            self.logger.warning("History is empty")
            return low

        # Binary search first guess with ratio to the time range of history
        # pylint: disable=c-extension-no-member
        guess = math.floor(
            (start_time - first_time) / (last_time - first_time) * (high - low) + low
        )
        # pylint: enable=c-extension-no-member

        self.logger.debug("first_guess=%s", guess)

        # Fine tune guess relative to the date range
        while low <= high and low <= guess <= high:
            if self.history[guess]["timestamp"] < start_time:
                low = guess + 1
            elif self.history[guess]["timestamp"] > end_time:
                high = guess - 1
            else:
                return guess

            # pylint: disable=c-extension-no-member
            guess = math.floor((high - low) / 2 + low)
            # pylint: enable=c-extension-no-member

        # If somehow still find nothing
        return self.NOT_FOUND

    def get_data(self, start_time: float, end_time: float) -> list:
        """
        :param start_time: timestamp of the start of the date range
        :param end_time: timestamp of the end of the date range
        :return: a list of events

        Find all events within the start and end time.
        """

        results = []
        affected_row_index = self.find_rows_in_range(start_time, end_time)

        if affected_row_index == self.NOT_FOUND:
            return results

        self.logger.debug("matched_row='%s'", affected_row_index)

        results.append(self.history[affected_row_index])

        # Get events from start_time to checkpoint
        cursor = affected_row_index - 1
        while cursor >= 0 and self.history[cursor]["timestamp"] >= start_time:
            results.insert(0, self.history[cursor])
            cursor -= 1

        # Get events from checkpoint to end_time
        cursor = affected_row_index + 1
        while (
            cursor <= (self.len - 1) and self.history[cursor]["timestamp"] <= end_time
        ):
            results.append(self.history[cursor])
            cursor += 1

        self.logger.debug("History events matches data: %s", results)

        return results

    @staticmethod
    def calculate_score(history):
        scoreboard = defaultdict(int)

        for item in history:
            operation, _, _ = item["operation"].split(",")

            if operation == "++":
                val = 1
            elif operation == "--":
                val = -1
            else:
                continue

            scoreboard[item["user_id"]] += val

        return [
            (user_id, scoreboard[user_id])
            for user_id in sorted(scoreboard, key=scoreboard.get, reverse=True)
        ]

    def get_by_range(self, of_date: pendulum.DateTime, time_unit: TimeUnit):
        start_time = TimeRange.get_start_date(of_date, time_unit)
        end_time = TimeRange.get_end_date(of_date, time_unit)

        self.logger.debug("Getting date range from %s => %s", start_time, end_time)

        return self.calculate_score(self.get_data(start_time, end_time))

    def get(self, of_date: pendulum.DateTime, time_unit):
        return self.get_by_range(of_date, time_unit)
