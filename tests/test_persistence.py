from sqlalchemy import text

from emojirades.persistence import get_engine


def test_engine_replaces_stale_pooled_connections(tmp_path):
    """
    Connections that are closed while idle in the pool should be detected and
    replaced when they are next checked out.
    """
    db_uri = f"sqlite:///{tmp_path / 'stale.db'}"
    engine = get_engine(db_uri)

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        stale_dbapi_connection = connection.connection.dbapi_connection

    # Simulate the database/network closing a connection while it is idle in the pool
    stale_dbapi_connection.close()

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
