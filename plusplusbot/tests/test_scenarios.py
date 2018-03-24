from plusplusbot.tests.helper import EmojiradeBotTester

class TestBotScenarios(EmojiradeBotTester):
    """
    Tests various game scenarios against the bot
    """
    def test_valid_complete_game(self):
        """ Performs a complete valid round """
        assert self.state["step"] == "new_game"
        assert self.state["old_winner"] is None
        assert self.state["winner"] is None
        assert self.state["emojirade"] is None
        assert not self.scoreboard

        self.send_event(self.events.new_game)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] is None
        assert not self.scoreboard

        self.send_event(self.events.posted_emojirade)
        assert self.state["step"] == "provided"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == self.config.emojirade
        assert not self.scoreboard

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == self.config.emojirade
        assert not self.scoreboard

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] is None
        assert list(self.scoreboard.keys()) == [self.config.player_3]
        assert self.scoreboard[self.config.player_3] == 1

    def test_responses(self):
        """
        Tests that the expected responses are bring returned
        Response order is asserted along with equality
        """
        assert self.state["step"] == "new_game"
        assert len(self.responses) == 0

        self.send_event(self.events.new_game)
        assert len(self.responses) == 4

        responses = [
            (self.config.channel, "<@{0}> has set the old winner to <@{0}> and the winner to <@{1}>".format(self.config.player_1, self.config.player_2)),
            (self.config.channel, "It's now <@{0}>'s turn to provide <@{1}> with the next 'rade!".format(self.config.player_1, self.config.player_2)),
            (self.config.player_1_channel, "You'll now need to send me the new 'rade for <@{0}>".format(self.config.player_2)),
            (self.config.player_1_channel, "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade"),
        ]

        for i, response in enumerate(responses):
            assert response == self.responses[i]

        self.send_event(self.events.posted_emojirade)
        assert len(self.responses) == 6

        responses = [
            (self.config.player_2_channel, "Hey, <@{0}> made the 'rade `{1}`, good luck!".format(self.config.player_1, self.config.emojirade)),
            (self.config.channel, ":mailbox: <@{0}> has sent the 'rade to <@{1}>".format(self.config.player_1, self.config.player_2)),
        ]

        for i, response in enumerate(responses):
            assert response == self.responses[4 + i]

        self.send_event(self.events.posted_emoji)
        assert len(self.responses) == 6

        self.send_event(self.events.correct_guess)
        assert len(self.responses) == 10

        responses = [
            (self.config.channel, "<@{0}>++".format(self.config.player_3)),
            (self.config.player_2_channel, "You'll now need to send me the new 'rade for <@{0}>".format(self.config.player_3)),
            (self.config.player_2_channel, "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade"),
            (self.config.channel, "Congrats <@{0}>, you're now at 1 point".format(self.config.player_3)),
        ]

        for i, response in enumerate(responses):
            assert response == self.responses[6 + i]

    def test_only_guess_when_guessing(self):
        """ Ensures we can only 'guess' correctly when state is guessing """
        assert self.state["step"] == "new_game"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "new_game"

        self.send_event(self.events.new_game)
        assert self.state["step"] == "waiting"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"

        self.send_event(self.events.posted_emojirade)
        assert self.state["step"] == "provided"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "provided"

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"

        # Only this correct guess will trigger the transition to waiting
        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) in self.responses
