import datetime
import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic.config import Config
from alembic import command

from .models import (
    Gamestate,
    GamestateHistory,
    Scoreboard,
    ScoreboardHistory,
    GamestateStep,
)


def get_engine(db_uri):
    return create_engine(db_uri, echo=True, future=True)


def get_session(db_uri):
    return Session(get_engine(db_uri))


def discover_base_dir():
    return os.path.join(os.path.dirname(__file__), "models")


def discover_migration_ini(base=None):
    if base is None:
        base = discover_base_dir()

    return os.path.join(base, "alembic.ini")


def discover_migration_dir(base=None):
    if base is None:
        base = discover_base_dir()

    return os.path.join(base, "alembic")


def migrate(db_uri, migration_ini=None, migration_dir=None):
    if migration_ini is None:
        migration_ini = discover_migration_ini()

    if migration_dir is None:
        migration_dir = discover_migration_dir()

    alembic_cfg = Config(migration_ini)
    alembic_cfg.set_main_option("script_location", migration_dir)
    alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
    command.upgrade(alembic_cfg, "head")


def populate(db_uri, table, data_filename, commit_every=100):
    session = get_session(db_uri)

    if table == "gamestate":
        Obj = Gamestate
        col_funcs = {
            "step": lambda x: getattr(GamestateStep, x),
        }
    elif table == "gamestate_history":
        Obj = GamestateHistory
        col_funcs = {}
    elif table == "scoreboard":
        Obj = Scoreboard
        col_funcs = {}
    elif table == "scoreboard_history":
        Obj = ScoreboardHistory
        col_funcs = {
            "timestamp": lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S"),
        }
    else:
        raise RuntimeError(f"Unknown table {table}?")

    with open(data_filename) as data_file:
        data = json.load(data_file)

        for i, row in enumerate(data):
            for key, func in col_funcs.items():
                row[key] = func(row[key])

            obj = Obj(**row)
            session.add(obj)

            if i % commit_every == 0:
                session.commit()

    session.commit()
    session.close()
