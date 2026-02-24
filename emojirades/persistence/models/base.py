import datetime

from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AwareDateTime(TypeDecorator):
    """
    Ensures that datetimes are always timezone-aware (UTC).
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=datetime.timezone.utc)
            return value.astimezone(datetime.timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=datetime.timezone.utc)
            return value.astimezone(datetime.timezone.utc)
        return value
