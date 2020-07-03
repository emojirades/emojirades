# Thanks to https://github.com/BeheadedKamikaze for his help with the algorithm
import logging
import math
from collections import defaultdict

import pendulum


class LeaderBoard:

    NOT_FOUND = -1

    def __init__(self, history):
        self.history = history
        self.len = len(history)
        self.logger = logging.getLogger('PlusPlusBot.analytics.LeaderBoard')

    # First step, find something in the history that matches the range.
    def find_rows_in_range(self, start_time, end_time):
        low = 0
        high = self.len - 1

        first_time = self.history[low]['timestamp']
        last_time = self.history[high]['timestamp']

        self.logger.debug('Starting binary search')
        # Out of range
        if end_time < first_time or start_time > last_time:
            self.logger.warning(f'Date is out of range earliest: {first_time}, latest: {last_time},'
                                f' start_time: {start_time}, end_time: {end_time}')
            return self.NOT_FOUND

        # history is empty
        if low == high:
            self.logger.warning(f'History is empty')
            return low

        # Binary search first guess with ratio to the time range of history
        guess = math.floor((start_time - first_time) / (last_time - first_time) * (high - low) + low)

        self.logger.debug(f'first_guess: {guess}')

        # Fine tune guess relative to the date range
        while low <= high and low <= guess <= high:
            if self.history[guess]['timestamp'] < start_time:
                low = guess + 1
            elif self.history[guess]['timestamp'] > end_time:
                high = guess - 1
            else:
                return guess

        # if somehow still find nothing
        return self.NOT_FOUND

    # Second step, flood-fill up and bottom
    # this reduces search time compared to finding the upper/lower bound
    def get_data(self, start_time, end_time):
        results = []
        affected_row_index = self.find_rows_in_range(start_time, end_time)

        if affected_row_index == self.NOT_FOUND:
            return results

        self.logger.debug(f'Found a match matched_row: {affected_row_index}')

        results.append(self.history[affected_row_index])

        # get events from start_time to checkpoint
        cursor = affected_row_index - 1
        while cursor >= 0 and self.history[cursor]['timestamp'] >= start_time:
            results.insert(0, self.history[cursor])
            cursor -= 1

        # get events from checkpoint to end_time
        cursor = affected_row_index + 1
        while cursor <= (self.len - 1) and self.history[cursor]['timestamp'] <= end_time:
            results.append(self.history[cursor])
            cursor += 1

        self.logger.debug(f'History events matches data: {results}')

        return results

    @staticmethod
    def calculate_score(history):
        leaderboard = defaultdict(int)

        for item in history:
            val = 0
            if item['operation'] == '++':
                val = 1
            elif item['operation'] == '--':
                val = -1

            leaderboard[item['user_id']] += val

        return [(u, leaderboard[u]) for u in sorted(leaderboard, key=leaderboard.get, reverse=True)]

    def get_by_range(self, of_date: pendulum.DateTime, unit: str):
        start_time = of_date.start_of(unit).timestamp()
        end_time = of_date.end_of(unit).timestamp()

        self.logger.debug(f"Getting date range from start_time: {start_time} to end_time: {end_time}")

        return self.calculate_score(self.get_data(start_time, end_time))

    def get_week(self, of_date: pendulum.DateTime):
        return self.get_by_range(of_date, 'week')

    def get_month(self, of_date: pendulum.DateTime):
        return self.get_by_range(of_date, 'month')


