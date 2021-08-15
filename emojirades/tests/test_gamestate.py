import os

from emojirades.tests.helper import EmojiradeBotTester


class GamestateTester(EmojiradeBotTester):
    def test_new_file_load(self):
        self.assertEqual(len(self.gamestate.get_channels()), 0)

    def test_existing_file_load(self):
        data_filename = os.path.join(
            os.path.dirname(__file__), "fixtures", "gamestate.json"
        )
        self.bot.populate_db(self.db_uri, "gamestate", data_filename)

        self.assertEqual(len(self.gamestate.get_channels()), 1)
