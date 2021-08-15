import os

from emojirades.tests.helper import EmojiradeBotTester


class ScorekeeperTester(EmojiradeBotTester):
    def test_new_file_load(self):
        self.assertEqual(len(self.scorekeeper.scoreboard(self.config.channel)), 0)

    def test_existing_file_load(self):
        data_filename = os.path.join(os.path.dirname(__file__), "fixtures", "scoreboard.json")
        self.bot.populate_db(self.db_uri, "scoreboard", data_filename)

        self.assertEqual(len(self.scorekeeper.scoreboard(self.config.channel)), 2)
