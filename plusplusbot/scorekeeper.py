
from collections import defaultdict

import logging
import boto3
import csv
import io
import os

module_logger = logging.getLogger("PlusPlusBot.scorekeeper")

leaderboard_limit = 10
history_limit = 5


class ScoreKeeper(object):
    def __init__(self, filename):
        self.logger = logging.getLogger("PlusPlusBot.scorekeeper.ScoreKeeper")
        self.filename = filename
        self.scoreboard = defaultdict(int)
        self.history = []

        if self.filename and os.path.exists(filename) and os.stat(filename).st_size > 0:
            self.scoreboard.update(self.load_scores(filename))
            self.logger.info("Loaded scores from {0}".format(self.filename))

    def load_scores(self, filename):
        if filename.startswith("s3://"):
            s3 = boto3.resource("s3")

            _, _, bucket, key = filename.split('/', 3)

            remote_file = s3.Object(bucket, key)
            score_file = io.StringIO(remote_file.get()["Body"].read().decode("utf-8"))
        else:
            score_file = open(filename, "rt", newline='')

        return {user: int(score) for (user, score) in csv.reader(score_file)}

    def plusplus(self, user):
        self.scoreboard[user] += 1
        self.history.append((user, "++"))

    def minusminus(self, user):
        self.scoreboard[user] -= 1
        self.history.append((user, "--"))

    def overwrite(self, user, score):
        self.scoreboard[user] = score
        self.history.append((user, score))

    def leaderboard(self, limit=leaderboard_limit):
        return sorted(self.scoreboard.items(), key=lambda i: (i[1], i[0]), reverse=True)[:limit]

    def history(self, limit=history_limit):
        return self.history[::-1][:limit]

    def export(self, output=None):
        if output is None:
            output = io.StringIO()

        writer = csv.writer(output)
        writer.writerows(self.scoreboard.items())

        return output

    def flush(self, filename=None):
        if filename is None:
            filename = self.filename

        if filename.startswith("s3://"):
            s3 = boto3.resource("s3")

            _, _, bucket, key = filename.split('/', 3)

            remote_file = s3.Object(bucket, key)
            remote_file.put(Body=self.export())
        else:
            with open(filename, "w", newline='') as output_file:
                self.export(output_file)
