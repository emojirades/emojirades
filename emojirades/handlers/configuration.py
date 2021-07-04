import pathlib
import sqlite3
import json

import psycopg2
import botocore
import boto3


class ConfigFileHandler:
    """
    Configuration Handlers deal with the transport of bytes to the 'file', wherever that may be
    They can have .save() and .load() called on them, which take/return bytes
    """

    def __init__(self, *args, **kwargs):
        self.uri = ""

        for arg, pos in [("uri", 0)]:
            if pos is not None:
                if len(args) > pos:
                    setattr(self, arg, args[pos])
                else:
                    raise TypeError(
                        f"{self} is missing a required positional argument '{arg}' in position {pos}"
                    )
            elif arg in kwargs:
                setattr(self, arg, kwargs[arg])
            else:
                raise TypeError(
                    f"{self} is missing a required keyword argument '{arg}'"
                )


class S3ConfigFileHandler(ConfigFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _, _, self._bucket, self._key = self.uri.split("/", 3)

        self._s3 = boto3.client("s3")

    @property
    def exists(self):
        try:
            self._s3.head_object(
                Bucket=self._bucket,
                Key=self._key,
            )
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False

            raise e

    def load(self):
        if self.exists:
            response = self._s3.get_object(
                Bucket=self._bucket,
                Key=self._key,
            )

            data = response["Body"].read().decode("utf-8")

            if not data:
                return None

            return json.loads(data)

        return None

    def save(self, content):
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._key,
            Body=json.dumps(content).encode("utf-8"),
        )


class LocalConfigFileHandler(ConfigFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._object = pathlib.Path(self.uri[7:])

    @property
    def exists(self):
        return self._object.exists()

    def create(self, content=None):
        if self.exists:
            return

        if content is None:
            content = {}

        with self._object.open("wb") as local_file:
            local_file.write(json.dumps(content).encode("utf-8"))

    def load(self):
        if self.exists:
            with self._object.open("rb") as local_file:
                data = local_file.read().decode("utf-8")

            if not data:
                return None

            return json.loads(data)

        return None

    def save(self, content):
        with self._object.open("wb") as local_file:
            local_file.write(json.dumps(content).encode("utf-8"))


class ConfigDatabaseHandler:
    """
    Configuration Database Handlers deal with extacting Workspace Configuration from databases
    Implementations load the database and look for a specific table yielding json blobs from the rows
    """

    def __init__(self, *args, **kwargs):
        self.database_uri = ""

        for pos, arg in [(0, "database_uri")]:
            if pos is not None:
                if len(args) > pos:
                    setattr(self, arg, args[pos])
                else:
                    raise TypeError(
                        f"{self} is missing a required positional argument '{arg}' in position {pos}"
                    )
            elif arg in kwargs:
                setattr(self, arg, kwargs[arg])
            else:
                raise TypeError(
                    f"{self} is missing a required keyword argument '{arg}'"
                )


class PostgresConfigDatabaseHandler(ConfigDatabaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._connection = psycopg2.connect(
            self.database_uri, cursor_factory=psycopg2.extras.DictCursor
        )

        # Check if we need to bootstrap
        cur = self._connection.cursor()
        cur.execute(
            "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)",
            ("workspaces",),
        )

        if not cur.fetchone()[0]:
            cur.execute(
                """
                CREATE TABLE workspaces (
                    workspace_id VARCHAR(12) PRIMARY KEY,
                    shard INT,
                    -- TODO
                );
            """
            )

    def workspace(self, workspace_id):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM workspaces WHERE workspace_id=%s", (workspace_id,))
        return cur.fetchone()


class SQLiteConfigDatabaseHandler(ConfigDatabaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._connection = sqlite3.connect(self.database_uri[9:], uri=True)
        self._connection.row_factory = sqlite3.Row

        # Check if we need to bootstrap
        cur = self._connection.cursor()
        cur.execute(
            "SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='workspaces'"
        )

        if cur.fetchone()[0] != 1:
            cur.execute(
                """
                CREATE TABLE workspaces (
                    workspace_id VARCHAR(12) PRIMARY KEY,
                    shard INT,
                    -- TODO
                );
            """
            )

    def workspace(self, workspace_id):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM workspaces WHERE workspace_id=%s", (workspace_id,))
        return cur.fetchone()


def get_config_handler(uri):
    if uri.startswith("postgresql://"):
        return PostgresConfigDatabaseHandler(uri)

    if uri.startswith("sqlite://"):
        return SQLiteConfigDatabaseHandler(uri)

    if uri.startswith("s3://"):
        return S3ConfigFileHandler(uri)

    if uri.startswith("file://"):
        return LocalConfigFileHandler(uri)

    raise RuntimeError(f"Unknown configuration uri '{uri}'")
