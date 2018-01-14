
from handlers import get_configuration_handler

import logging
import boto3
import csv

def get_handler(filename):
    class EmojiradesConfigurationHandler(get_configuration_handler(filename)):
        """
        Handles CRUD for the Emojirades Game State configuration file
        """
        def __init__(self, filename):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            self._content = bytes_content.decode("utf-8")

        def save(self):
            bytes_content = self._content.encode("utf-8")

            super().save(bytes_content)

    return EmojiradesConfigurationHandler(filename)


class EmojiradesGame(object):
    def __init__(self, filename):
        self.config = get_handler(filename)


