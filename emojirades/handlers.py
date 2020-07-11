import botocore
import pathlib
import logging
import boto3
import csv


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
