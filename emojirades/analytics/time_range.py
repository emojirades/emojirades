class TimeRange:

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all time"

    @classmethod
    def list(cls):
        return [cls.WEEKLY, cls.MONTHLY, cls.ALL_TIME]
