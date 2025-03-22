import datetime

from emojirades.analytics.time_unit import TimeUnit


class TimeRange:
    @classmethod
    def get_start_date(
        cls, on_date: datetime.datetime, time_unit: TimeUnit
    ) -> datetime.datetime:
        if time_unit == TimeUnit.WEEKLY:
            first_day_of_week = on_date - datetime.timedelta(days=on_date.weekday())

            return first_day_of_week.replace(hour=0, minute=0, second=0)

        if time_unit == TimeUnit.MONTHLY:
            first_day_of_month = on_date.replace(day=1)

            return first_day_of_month.replace(hour=0, minute=0, second=0)

        raise RuntimeError(f"Unmapped TimeUnit: {time_unit}")

    @classmethod
    def get_end_date(
        cls, on_date: datetime.datetime, time_unit: TimeUnit
    ) -> datetime.datetime:
        if time_unit == TimeUnit.WEEKLY:
            last_day_of_week = TimeRange.get_start_date(
                on_date, time_unit
            ) + datetime.timedelta(days=6)

            return last_day_of_week.replace(hour=23, minute=59, second=59)

        if time_unit == TimeUnit.MONTHLY:
            next_month = on_date.replace(day=28) + datetime.timedelta(days=4)
            last_day_of_month = next_month - datetime.timedelta(days=next_month.day)

            return last_day_of_month.replace(hour=23, minute=59, second=59)

        raise RuntimeError(f"Unmapped TimeUnit: {time_unit}")
