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
