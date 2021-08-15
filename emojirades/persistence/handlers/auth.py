import json

import boto3


# pylint: disable=too-few-public-methods
class S3AuthFileHandler:
    def __init__(self, auth_uri):
        _, _, self._bucket, self._key = auth_uri.split("/", 3)

        self._s3 = boto3.client("s3")

    def load(self):
        response = self._s3.get_object(
            Bucket=self._bucket,
            Key=self._key,
        )

        return json.load(response["Body"])


# pylint: disable=too-few-public-methods
class LocalAuthFileHandler:
    def __init__(self, auth_uri):
        self.auth_uri = auth_uri

    def load(self):
        with open(self.auth_uri, "rt") as auth_file:
            return json.load(auth_file)


def get_auth_handler(uri):
    if uri.startswith("s3://"):
        return S3AuthFileHandler(uri)

    return LocalAuthFileHandler(uri)
