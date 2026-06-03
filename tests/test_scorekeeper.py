import os


class TestScorekeeper:
    def test_new_file_load(self, slack_web_api, bot):
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

    def test_existing_file_load(self, slack_web_api, bot):
        data_filename = os.path.join(os.path.dirname(__file__), "fixtures", "scoreboard.json")
        bot.bot.populate_db(bot.db_uri, "scoreboard", data_filename)

        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 2

    def test_clear_cache_invalidates_history_cache(self, slack_web_api, bot):
        # Ensure caching is True
        bot.scorekeeper.repository.caching = True

        channel = bot.config.channel
        user = bot.config.player_1

        # Retrieve history to populate the cache
        bot.scorekeeper.history(channel, user=user)

        # Check that cache has been populated
        cache_key = (channel, user, bot.scorekeeper.repository.HISTORY_LIMIT, "desc")
        assert cache_key in bot.scorekeeper.repository.history_cache

        # Clear cache for the channel
        bot.scorekeeper.repository.clear_cache(channel)

        # Verify cache_key is removed
        assert cache_key not in bot.scorekeeper.repository.history_cache
