from plusplusbot.tests.helper import EmojiradeBotTester


class TestBotCommands(EmojiradeBotTester):
    """
    Tests various game commands against the bot
    """
    def test_plusplus_new_game(self):
        """ Cannot ++ someone when the game is not in progress """
        state = self.bot.gamestate.state[self.config.channel]

        assert state["step"] == "new_game"

        self.send_event(self.events.plusplus)
        assert (self.config.channel, "Sorry but we need to be actively guessing! Get the winner to start posting the next 'rade!") in self.responses

    def test_leaderboard_output(self):
        """ Ensure leaderboard output is consistent """
        self.reset_and_transition_to("guessing")

        self.send_event(self.events.correct_guess)
        self.send_event(self.events.leaderboard)

        assert (self.config.channel, "1. U00000003 [1 point]") in self.responses

    def test_fixwinner(self):
        """ Ensure fixwinner does the right thing """
        self.reset_and_transition_to("guessing")

        state = self.bot.gamestate.state[self.config.channel]

        self.send_event(self.events.correct_guess)
        assert state["old_winner"] == self.config.player_2
        assert state["winner"] == self.config.player_3
        assert self.bot.scorekeeper.current_score(self.config.player_3) == (1, True)
        assert self.bot.scorekeeper.current_score(self.config.player_4) == (0, False)

        self.send_event(self.events.fixwinner)
        assert state["old_winner"] == self.config.player_2
        assert state["winner"] == self.config.player_4
        assert self.bot.scorekeeper.current_score(self.config.player_3) == (0, False)
        assert self.bot.scorekeeper.current_score(self.config.player_4) == (1, True)

    def test_set_emojirade_banned_words(self):
        """ Ensure that the emojirade can't contain banned words """
        self.reset_and_transition_to("waiting")

        state = self.bot.gamestate.state[self.config.channel]

        banned_emojirade = dict(self.events.posted_emojirade)
        banned_emojirade["text"] = "emojirade foo :pie: bar"

        self.send_event(banned_emojirade)
        assert (self.config.bot_channel, "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?") in self.responses
        assert state["step"] == "waiting"

        self.send_event(self.events.posted_emojirade)
        assert state["step"] == "provided"
