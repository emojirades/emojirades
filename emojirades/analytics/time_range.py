import pendulum

from emojirades.analytics.time_unit import TimeUnit


class TimeRange:
    pendulum_unit = {TimeUnit.WEEKLY: "week", TimeUnit.MONTHLY: "month"}

    @classmethod
    def get_start_date(
        cls, on_date: pendulum.DateTime, time_unit: TimeUnit
    ) -> pendulum.DateTime:
        return on_date.start_of(cls.pendulum_unit[time_unit])

    @classmethod
    def get_end_date(
        cls, on_date: pendulum.DateTime, time_unit: TimeUnit
    ) -> pendulum.DateTime:
        return on_date.end_of(cls.pendulum_unit[time_unit])
