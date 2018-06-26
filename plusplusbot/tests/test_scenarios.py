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
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) in self.responses

    def test_valid_manually_awarded_complete_game(self):
        """ Performs a complete valid round but the win is manually awarded """
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

        self.send_event(self.events.incorrect_guess)
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == self.config.emojirade
        assert not self.scoreboard

        self.send_event(self.events.manual_award)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] is None
        assert list(self.scoreboard.keys()) == [self.config.player_3]
        assert self.scoreboard[self.config.player_3] == 1

    def test_valid_responses(self):
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

        for i, (channel, msg) in enumerate(responses):
            assert channel == self.responses[i][0]
            assert msg in self.responses[i][1]

        self.send_event(self.events.posted_emojirade)
        assert len(self.responses) == 6

        responses = [
            (self.config.player_2_channel, "Hey, <@{0}> made the 'rade `{1}`, good luck!".format(self.config.player_1, self.config.emojirade)),
            (self.config.channel, ":mailbox: 'rade sent to <@{1}>".format(self.config.player_1, self.config.player_2)),
        ]

        for i, (channel, msg) in enumerate(responses):
            assert channel == self.responses[4 + i][0]
            assert msg in self.responses[4 + i][1]

        self.send_event(self.events.posted_emoji)
        assert len(self.responses) == 6

        self.send_event(self.events.correct_guess)
        assert len(self.responses) == 10

        responses = [
            (self.config.channel, "<@{0}>++".format(self.config.player_3)),
            (self.config.channel, "Congrats <@{0}>, you're now at 1 point".format(self.config.player_3)),
            (self.config.player_2_channel, "You'll now need to send me the new 'rade for <@{0}>".format(self.config.player_3)),
            (self.config.player_2_channel, "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade"),
        ]

        for i, (channel, msg) in enumerate(responses):
            assert channel == self.responses[6 + i][0]
            assert msg in self.responses[6 + i][1]

    def test_only_guess_when_guessing(self):
        """ Ensures we can only 'guess' correctly when state is guessing """
        assert self.state["step"] == "new_game"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "new_game"
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) not in self.responses

        self.send_event(self.events.new_game)
        assert self.state["step"] == "waiting"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) not in self.responses

        self.send_event(self.events.posted_emojirade)
        assert self.state["step"] == "provided"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "provided"
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) not in self.responses

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) in self.responses

    def test_two_games_in_a_row(self):
        """ Plays 2 games in a row to ensure state is maintained """
        self.reset_and_transition_to("guessing")
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == self.config.emojirade

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] is None
        assert (self.config.channel, "<@{0}>++".format(self.config.player_3)) in self.responses
        assert any(
            self.config.channel == channel and
            "Congrats <@{0}>, you're now at 1 point".format(self.config.player_3) in msg
            for channel, msg in self.responses
        )

        emojirade = "second"
        override = {"user": self.config.player_2, "text": "emojirade {0}".format(emojirade)}
        self.send_event({**self.events.posted_emojirade, **override})
        assert self.state["step"] == "provided"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] == emojirade

        override = {"user": self.config.player_3}
        self.send_event({**self.events.posted_emoji, **override})
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] == emojirade

        override = {"user": self.config.player_1, "text": emojirade}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_3
        assert self.state["winner"] == self.config.player_1
        assert self.state["emojirade"] is None
        assert (self.config.channel, "<@{0}>++".format(self.config.player_1)) in self.responses
        assert any(
            self.config.channel == channel and
            "Congrats <@{0}>, you're now at 1 point".format(self.config.player_1) in msg
            for channel, msg in self.responses
        )
