import os


class FileFixture:
    """
    Test helper to read fixtures files with relative path
    path: pass in the path after `fixtures`
    """

    def __init__(self, path):
        dirname = os.path.dirname(__file__)
        self.filename = os.path.join(dirname, os.path.join("fixtures", path))

    def open(self):
        return open(self.filename, "r")
