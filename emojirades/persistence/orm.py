from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def get_engine(db_uri):
    return create_engine(db_uri, echo=True, future=True)


def get_session(db_uri):
    return Session(get_engine(db_uri))
