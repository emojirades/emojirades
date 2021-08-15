import pathlib
import json

import boto3


def set_handler_args(self, *args, handler_params, **kwargs):
    for arg, pos in handler_params:
        if pos is not None:
            if len(args) > pos:
                setattr(self, arg, args[pos])
            else:
                raise TypeError(
                    f"{self} is missing a required positional argument"
                    + f"'{arg}' in position {pos}"
                )
        elif arg in kwargs:
            setattr(self, arg, kwargs[arg])
        else:
            raise TypeError(f"{self} is missing a required keyword argument '{arg}'")


# pylint: disable=too-few-public-methods
class S3WorkspaceDirectoryHandler:
    def __init__(self, *args, **kwargs):
        self.workspace_uri = ""

        params = [("workspace_uri", 0)]
        set_handler_args(self, *args, handler_params=params, **kwargs)

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


# pylint: disable=too-few-public-methods
class LocalWorkspaceDirectoryHandler:
    def __init__(self, *args, **kwargs):
        self.workspace_uri = ""

        params = [("workspace_uri", 0)]
        set_handler_args(self, *args, handler_params=params, **kwargs)

        self._folder = pathlib.Path(self.workspace_uri[7:])

    def workspaces(self):
        for entry in self._folder.iterdir():
            if not entry.is_file():
                continue

            if not entry.suffix == ".json":
                continue

            with open(entry) as workspace_file:
                yield json.load(workspace_file)


def get_workspace_handler(uri):
    if uri.startswith("s3://"):
        return S3WorkspaceDirectoryHandler(uri)

    return LocalWorkspaceDirectoryHandler(uri)
