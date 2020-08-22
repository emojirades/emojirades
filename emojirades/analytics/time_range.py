class TimeRange:

    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    ALLTIME = 'alltime'

    @classmethod
    def list(cls):
        return [cls.WEEKLY,
                cls.MONTHLY,
                cls.ALLTIME]
