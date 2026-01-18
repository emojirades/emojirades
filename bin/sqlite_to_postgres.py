#!/usr/bin/env python3

import argparse

from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session

from emojirades.persistence.models import (
    Gamestate,
    GamestateHistory,
    Scoreboard,
    ScoreboardHistory,
)

parser = argparse.ArgumentParser()
parser.add_argument("--source-db-uri", required=True, help="Path to sqlite DB")
parser.add_argument("--target-db-uri", required=True, help="Full postgres DB URI")
args = parser.parse_args()

source_engine = create_engine(args.source_db_uri, echo=False, future=True)
target_engine = create_engine(args.target_db_uri, echo=False, future=True)

source_session = Session(source_engine)
target_session = Session(target_engine)

objects = [
    Gamestate,
    GamestateHistory,
    Scoreboard,
    ScoreboardHistory,
]

for obj in objects:
    for source_instance in source_session.execute(select(obj)).scalars().all():
        target_instance = target_session.merge(source_instance)
        target_session.add(target_instance)

    target_session.commit()

target_session.close()
source_session.close()
