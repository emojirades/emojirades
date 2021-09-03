import os


class TestGamestate:
    def test_new_file_load(self, slack_web_api, bot):
        assert len(bot.gamestate.get_channels()) == 0

    def test_existing_file_load(self, slack_web_api, bot):
        data_filename = os.path.join(
            os.path.dirname(__file__), "fixtures", "gamestate.json"
        )
        bot.bot.populate_db(bot.db_uri, "gamestate", data_filename)

        assert len(bot.gamestate.get_channels()) == 1
