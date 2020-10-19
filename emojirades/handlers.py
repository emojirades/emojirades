import botocore
import pathlib
import logging
import boto3
import json
import csv


class WorkspaceDirectoryHandler(object):
    """
    Workspace Directory Handlers deal with extracting Workspace Configuration files
    The various implementations iterate through the expected path structure yielding workspaces
    """

    def __init__(self, *args, **kwargs):
        for arg, pos in [("workspace_path", 0)]:
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

        _, _, self._bucket, self._prefix = self.workspace_path.split("/", 3)

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

        self._folder = pathlib.Path(self.workspace_path)

    def workspaces(self):
        for entry in self._folder.iterdir():
            if not entry.is_file():
                continue

            if not entry.suffix == ".json":
                continue

            with open(entry) as workspace_file:
                yield json.load(workspace_file)


def get_workspace_directory_handler(directory):
    if directory.startswith("s3://"):
        return S3WorkspaceDirectoryHandler
    else:
        return LocalWorkspaceDirectoryHandler


class ConfigurationHandler(object):
    """
    Configuration Handlers deal with the transport of bytes to the 'file', wherever that may be
    They can have .save() and .load() called on them, which take/return bytes
    """

    def __init__(self, *args, **kwargs):
        for arg, pos in [("filename", 0)]:
            if pos is not None:
                if len(args) > pos:
                    setattr(self, arg, args[pos])
                else:
                    raise TypeError(
                        f"{self} is missing a required positional argument '{arg}' in position {pos}"
                    )
            elif arg in kwargs:
                setattr(self, arg, kwargs["filename"])
            else:
                raise TypeError(
                    f"{self} is missing a required keyword argument '{arg}'"
                )


class S3ConfiguationHandler(ConfigurationHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _, _, self._bucket, self._key = self.filename.split("/", 3)

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
            else:
                raise e

    def load(self):
        if self.exists:
            response = self._s3.get_object(
                Bucket=self._bucket,
                Key=self._key,
            )

            return response["Body"].read()
        else:
            return None

    def save(self, content):
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._key,
            Body=content,
        )


class LocalConfigurationHandler(ConfigurationHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._object = pathlib.Path(self.filename)

    @property
    def exists(self):
        return self._object.exists()

    def create(self, content=b""):
        if self.exists:
            return True

        with self._object.open("wb") as local_file:
            local_file.write(content)

    def load(self):
        if self.exists:
            with self._object.open("rb") as local_file:
                return local_file.read()
        else:
            return None

    def save(self, content):
        with self._object.open("wb") as local_file:
            local_file.write(content)


def get_configuration_handler(filename):
    if filename.startswith("s3://"):
        return S3ConfiguationHandler
    else:
        return LocalConfigurationHandler
