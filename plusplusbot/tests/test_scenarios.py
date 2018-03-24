from plusplusbot.tests.helper import EmojiradeBotTester

class TestBotScenarios(EmojiradeBotTester):
    """
    Tests various game scenarios against the bot
    """
    def test_valid_game(self):
        """ Feeds state transition events to the bot asserting expected state """
        state = self.bot.gamestate.state[self.config.channel]
        scoreboard = self.bot.scorekeeper.scoreboard

        assert state["step"] == "new_game"
        assert state["old_winner"] is None
        assert state["winner"] is None
        assert state["emojirade"] is None
        assert not scoreboard

        self.send_event(self.events.new_game)
        assert state["step"] == "waiting"
        assert state["old_winner"] == self.config.player_1
        assert state["winner"] == self.config.player_2
        assert state["emojirade"] is None
        assert not scoreboard

        self.send_event(self.events.posted_emojirade)
        assert state["step"] == "provided"
        assert state["old_winner"] == self.config.player_1
        assert state["winner"] == self.config.player_2
        assert state["emojirade"] == self.config.emojirade
        assert not scoreboard

        self.send_event(self.events.posted_emoji)
        assert state["step"] == "guessing"
        assert state["old_winner"] == self.config.player_1
        assert state["winner"] == self.config.player_2
        assert state["emojirade"] == self.config.emojirade
        assert not scoreboard

        self.send_event(self.events.correct_guess)
        assert state["step"] == "waiting"
        assert state["old_winner"] == self.config.player_2
        assert state["winner"] == self.config.player_3
        assert state["emojirade"] is None
        assert list(scoreboard.keys()) == [self.config.player_3]
        assert scoreboard[self.config.player_3] == 1
