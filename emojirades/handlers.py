import botocore
import pathlib
import logging
import boto3
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

        self._s3 = boto3.resource("s3")

    def workspaces(self):
        paginator = self._s3.get_paginator("list_objects_v2")

        response_iterator = paginator.paginate(
            Bucket=self._bucket,
            Prefix=self._prefix,
        )

        for response in response_iterator:
            for workspace in response["Contents"]:
                workspace_path = workspace["Key"]
                print(workspace)
                # TODO: Extract Workspace ID, score/state/auth file

                yield {
                    "workspace_id": workspace_id,
                    "score_file": score_file,
                    "state_file": state_file,
                    "auth_file": auth_file,
                }


class LocalWorkspaceDirectoryHandler(WorkspaceDirectoryHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._folder = pathlib.Path(self.workspace_path)

    def workspaces(self):
        for workspace in self._folder.iterdir():
            if not workspace.is_dir():
                continue

            print(workspace)
            # TODO: Extract Workspace ID, score/state/auth file

            yield {
                "workspace_id": workspace_id,
                "score_file": score_file,
                "state_file": state_file,
                "auth_file": auth_file,
            }


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

        self._s3 = boto3.resource("s3")
        self._object = self._s3.Object(self._bucket, self._key)

    @property
    def exists(self):
        try:
            self._s3.Object(self._bucket, self._key).load()
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                raise e

    def load(self):
        if self.exists:
            return self._object.get()["Body"].read()
        else:
            return None

    def save(self, content):
        self._object.put(Body=content)


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
