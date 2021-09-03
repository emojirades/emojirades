import os


class TestScorekeeper:
    def test_new_file_load(self, slack_web_api, bot):
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

    def test_existing_file_load(self, slack_web_api, bot):
        data_filename = os.path.join(
            os.path.dirname(__file__), "fixtures", "scoreboard.json"
        )
        bot.bot.populate_db(bot.db_uri, "scoreboard", data_filename)

        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 2
