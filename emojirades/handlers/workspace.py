import pathlib
import json

import sqlite3
import psycopg2
import boto3


class WorkspaceDirectoryHandler:
    """
    Workspace Directory Handlers deal with extracting Workspace Configuration from files
    Implementations iterate through the expected path structure yielding json blobs from the file content
    """
    def __init__(self, *args, **kwargs):
        self.workspace_uri = ""

        for pos, arg in [(0, "workspace_uri")]:
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


class S3WorkspaceDirectoryHandler(WorkspaceDirectoryHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _, _, self._bucket, self._prefix = self.workspace_uri.split("/", 3)

        self._s3 = boto3.client("s3")

    def workspaces(self):
        paginator = self._s3.get_paginator("list_objects_v2")

        response_iterator = paginator.paginate(
            Bucket=self._bucket,
            Prefix=self._prefix,
        )

        for response in response_iterator:
            for content in response["Contents"]:
                if not content["Key"].endswith(".json"):
                    continue

                s3_object = self._s3.get_object(
                    Bucket=self._bucket,
                    Key=content["Key"],
                )

                yield json.load(s3_object["Body"])


class LocalWorkspaceDirectoryHandler(WorkspaceDirectoryHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._folder = pathlib.Path(self.workspace_uri[7:])

    def workspaces(self):
        for entry in self._folder.iterdir():
            if not entry.is_file():
                continue

            if not entry.suffix == ".json":
                continue

            with open(entry) as workspace_file:
                yield json.load(workspace_file)


class WorkspaceDatabaseHandler:
    """
    Workspace Database Handlers deal with extacting Workspace Configuration from databases
    Implementations load the database and look for a specific table
    """
    def __init__(self, *args, **kwargs):
        self.database_uri = ""
        self.shard_id = None

        for pos, arg in [(0, "database_uri"), (None, "shard_id")]:
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


class PostgresWorkspaceDatabaseHandler(WorkspaceDatabaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._connection = psycopg2.connect(self.database_uri, cursor_factory=psycopg2.extras.DictCursor)

        # Check if we need to bootstrap
        cur = self._connection.cursor()
        cur.execute("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_name=%s)", ("workspaces",))

        if not cur.fetchone()[0]:
            cur.execute("""
                CREATE TABLE workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    shard_id INT,
                    score_uri TEXT,
                    state_uri TEXT,
                    auth_uri TEXT
                );
            """)

    def workspaces(self):
        cur = self._connection.cursor()
        cur.execute("SELECT score_uri, state_uri, auth_uri, workspace_id FROM workspaces WHERE shard_id=%s", (self.shard_id, ))

        for row in cur:
            yield row


class SQLiteWorkspaceDatabaseHandler(WorkspaceDatabaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._connection = sqlite3.connect(self.database_uri[9:], uri=True)
        self._connection.row_factory = sqlite3.Row

        # Check if we need to bootstrap
        cur = self._connection.cursor()
        cur.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='workspaces'")

        if cur.fetchone()[0] != 1:
            cur.execute("""
                CREATE TABLE workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    shard_id INT,
                    score_uri TEXT,
                    state_uri TEXT,
                    auth_uri TEXT
                );
            """)

    def workspaces(self):
        cursor = self._connection.cursor()
        cursor.execute("SELECT score_uri, state_uri, auth_uri, workspace_id FROM workspaces WHERE shard_id=%s", (self.shard_id, ))

        for row in cursor:
            yield row


def get_workspace_handler(uri):
    if uri.startswith("postgresql://"):
        return PostgresWorkspaceDatabaseHandler(uri)

    if uri.startswith("sqlite://"):
        return SQLiteWorkspaceDatabaseHandler(uri)

    if uri.startswith("s3://"):
        return S3WorkspaceDirectoryHandler(uri)

    if uri.startswith("file://"):
        return LocalWorkspaceDirectoryHandler(uri)

    raise RuntimeError(f"Unknown workspace uri '{uri}'")
