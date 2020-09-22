import pendulum


class TimeRange:

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all time"

    pendulum_unit = {
        WEEKLY: "week",
        MONTHLY: "month"
    }

    @classmethod
    def list(cls):
        return [cls.WEEKLY,
                cls.MONTHLY,
                cls.ALL_TIME]

    @classmethod
    def get_start_date(cls, on_date: pendulum.DateTime, time_unit) -> pendulum.DateTime:
        return on_date.start_of(cls.pendulum_unit[time_unit])

    @classmethod
    def get_end_date(cls, on_date: pendulum.DateTime, time_unit) -> pendulum.DateTime:
        return on_date.end_of(cls.pendulum_unit[time_unit])
