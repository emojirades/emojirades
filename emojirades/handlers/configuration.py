import pathlib
import sqlite3
import json

import psycopg2
import botocore
import boto3

from emojirades.handlers.base import set_handler_args


class S3ConfigFileHandler:
    def __init__(self, *args, **kwargs):
        self.uri = ""

        params = [("uri", 0)]
        set_handler_args(self, *args, handler_params=params, **kwargs)

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
        except botocore.exceptions.ClientError as exception:
            if exception.response["Error"]["Code"] == "404":
                return False

            raise exception

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


class LocalConfigFileHandler:
    def __init__(self, *args, **kwargs):
        self.uri = ""

        params = [("uri", 0)]
        set_handler_args(self, *args, handler_params=params, **kwargs)

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


# pylint: disable=too-few-public-methods
class PostgresConfigDatabaseHandler:
    def __init__(self, *args, **kwargs):
        self.database_uri = ""

        params = [("database_uri", 0)]
        set_handler_args(self, *args, handler_params=params, **kwargs)

        self._connection = psycopg2.connect(
            self.database_uri, cursor_factory=psycopg2.extras.DictCursor
        )

    def workspace(self, workspace_id):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM workspaces WHERE workspace_id=%s", (workspace_id,))
        return cur.fetchone()


# pylint: disable=too-few-public-methods
class SQLiteConfigDatabaseHandler:
    def __init__(self, *args, **kwargs):
        self.database_uri = ""

        params = [("database_uri", 0)]
        set_handler_args(self, *args, handler_params=params, **kwargs)

        # pylint: disable=no-member
        self._connection = sqlite3.connect(self.database_uri[9:], uri=True)
        self._connection.row_factory = sqlite3.Row
        # pylint: enable=no-member

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
