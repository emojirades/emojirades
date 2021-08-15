from emojirades.tests.helper import EmojiradeBotTester
from emojirades.persistence import GamestateStep

import time
import re


class TestBotScenarios(EmojiradeBotTester):
    """
    Tests various game scenarios against the bot
    """

    def test_valid_complete_game(self):
        """Performs a complete valid round"""
        assert self.step == GamestateStep.NEW_GAME
        assert self.get_xyz("previous_winner") is None
        assert self.get_xyz("current_winner") is None
        assert self.get_xyz("emojirade") is None
        assert self.get_xyz("raw_emojirade") is None
        assert len(self.scorekeeper.scoreboard(self.config.channel)) == 0

        self.send_event(self.events.new_game)
        assert self.step == GamestateStep.WAITING
        assert self.get_xyz("previous_winner") == self.config.player_1
        assert self.get_xyz("current_winner") == self.config.player_2
        assert self.get_xyz("emojirade") is None
        assert self.get_xyz("raw_emojirade") is None
        assert len(self.scorekeeper.scoreboard(self.config.channel)) == 0

        self.send_event(self.events.posted_emojirade)
        assert self.step == GamestateStep.PROVIDED
        assert self.get_xyz("previous_winner") == self.config.player_1
        assert self.get_xyz("current_winner") == self.config.player_2
        assert self.get_xyz("emojirade") == f'["{self.config.emojirade}"]'
        assert self.get_xyz("raw_emojirade") == f'["{self.config.emojirade}"]'
        assert len(self.scorekeeper.scoreboard(self.config.channel)) == 0

        self.send_event(self.events.posted_emoji)
        assert self.step == GamestateStep.GUESSING
        assert self.get_xyz("previous_winner") == self.config.player_1
        assert self.get_xyz("current_winner") == self.config.player_2
        assert self.get_xyz("emojirade") == f'["{self.config.emojirade}"]'
        assert self.get_xyz("raw_emojirade") == f'["{self.config.emojirade}"]'
        assert len(self.scorekeeper.scoreboard(self.config.channel)) == 0

        self.send_event(self.events.incorrect_guess)
        assert self.step == GamestateStep.GUESSING
        assert self.get_xyz("previous_winner") == self.config.player_1
        assert self.get_xyz("current_winner") == self.config.player_2
        assert self.get_xyz("emojirade") == f'["{self.config.emojirade}"]'
        assert self.get_xyz("raw_emojirade") == f'["{self.config.emojirade}"]'
        assert len(self.scorekeeper.scoreboard(self.config.channel)) == 0

        self.send_event(self.events.correct_guess)
        assert self.step == GamestateStep.WAITING
        assert self.get_xyz("previous_winner") == self.config.player_2
        assert self.get_xyz("current_winner") == self.config.player_3
        assert self.get_xyz("emojirade") is None
        assert self.get_xyz("raw_emojirade") is None
        assert self.scorekeeper.scoreboard(self.config.channel) == [(1, self.config.player_3, 1)]
        assert (self.config.channel, f"<@{self.config.player_3}>++") in self.responses

    def test_valid_manually_awarded_complete_game(self):
        """Performs a complete valid round but the win is manually awarded"""
        assert self.state["step"] == "new_game"
        assert self.state["old_winner"] is None
        assert self.state["winner"] is None
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None
        assert not self.scoreboard["scores"]

        self.send_event(self.events.new_game)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None
        assert not self.scoreboard["scores"]

        self.send_event(self.events.posted_emojirade)
        assert self.state["step"] == "provided"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == [self.config.emojirade]
        assert self.state["raw_emojirade"] == [self.config.emojirade]
        assert not self.scoreboard["scores"]

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == [self.config.emojirade]
        assert self.state["raw_emojirade"] == [self.config.emojirade]
        assert not self.scoreboard["scores"]

        self.send_event(self.events.incorrect_guess)
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == [self.config.emojirade]
        assert self.state["raw_emojirade"] == [self.config.emojirade]
        assert not self.scoreboard["scores"]

        self.send_event(self.events.manual_award)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None
        assert list(self.scoreboard["scores"].keys()) == [self.config.player_3]
        assert self.scoreboard["scores"][self.config.player_3] == 1

    def test_valid_responses(self):
        """
        Tests that the expected responses are bring returned
        Response order is asserted along with equality
        """

        def response(dst, msg):
            return (dst, re.compile(msg))

        def reaction(dst, emoji, ts):
            return (dst, re.compile(emoji), ts)

        total_responses = 0
        total_reactions = 0

        # Assert game hasn't started yet
        assert self.state["step"] == "new_game"
        assert len(self.responses) == total_responses

        # User starts a new round manually
        self.send_event(self.events.new_game)

        # Expected *new* responses
        responses = [
            response(
                self.config.channel,
                f"<@{self.config.player_1}> has set the old winner to <@{self.config.player_1}> and the winner to <@{self.config.player_2}>",
            ),
            response(
                self.config.channel,
                f"It's now <@{self.config.player_1}>'s turn to provide <@{self.config.player_2}> with the next 'rade!",
            ),
            response(
                self.config.player_1_channel,
                f"You'll now need to send me the new 'rade for <@{self.config.player_2}>",
            ),
            response(
                self.config.player_1_channel,
                "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade",
            ),
        ]

        # Ensure each expected response exists in actual responses
        for i, (channel, msg) in enumerate(responses):
            assert channel == self.responses[i][0]
            assert msg.match(self.responses[i][1])

        # Ensure total volume is as expected
        total_responses += len(responses)
        assert len(self.responses) == total_responses

        # User sends a 'rade
        self.send_event(self.events.posted_emojirade)

        # Expected *new* responses
        responses = [
            response(
                self.config.player_2_channel,
                f"Hey, <@{self.config.player_1}> made the emojirade `{self.config.emojirade}`, good luck!",
            ),
            response(
                self.config.channel,
                f":mailbox: 'rade sent to <@{self.config.player_2}>",
            ),
        ]

        # Ensure each expected response exists in actual responses
        for i, (channel, msg) in enumerate(responses):
            assert channel == self.responses[total_responses + i][0]
            assert msg.match(self.responses[total_responses + i][1])

        # Ensure total volume is as expected
        total_responses += len(responses)
        assert len(self.responses) == total_responses

        # Expected *new* reactions
        reactions = [
            reaction(
                self.config.player_1_channel,
                r"\+1",
                self.events.posted_emojirade["ts"],
            ),
        ]

        # Ensure each expected reaction exists
        while not self.reactions:
            time.sleep(0.5)

        for i, (channel, emoji, ts) in enumerate(reactions):
            assert channel == self.reactions[total_reactions + i][0]
            assert emoji.match(self.reactions[total_reactions + i][1])
            assert ts == self.reactions[total_reactions + i][2]

        # Ensure total volume is as expected
        total_reactions += len(reactions)
        assert len(self.reactions) == total_reactions

        # User starts posting emoji's for the current round
        self.send_event(self.events.posted_emoji)
        assert len(self.responses) == total_responses  # Bot shouldn't respond

        # User posts a correct guess
        self.send_event(self.events.correct_guess)

        # Expected *new* responses
        responses = [
            response(
                self.config.channel,
                "Holy bejesus Batman :bat::man:, they guessed it in one go! :clap:",
            ),
            response(self.config.channel, f"<@{self.config.player_3}>\\+\\+"),
            response(
                self.config.channel,
                f"Congrats <@{self.config.player_3}>, you're now at 1 point :[a-z_]+:",
            ),
            response(
                self.config.channel,
                f"The correct emojirade was `{self.config.emojirade}`",
            ),
            response(
                self.config.player_2_channel,
                f"You'll now need to send me the new 'rade for <@{self.config.player_3}>",
            ),
            response(
                self.config.player_2_channel,
                "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade",
            ),
        ]

        # Ensure each expected response exists in actual responses
        for i, (channel, msg) in enumerate(responses):
            assert channel == self.responses[total_responses + i][0]
            assert msg.match(self.responses[total_responses + i][1])

        # Ensure total volume is as expected
        total_responses += len(responses)
        assert len(self.responses) == total_responses

        # Expected *new* reactions
        reactions = [
            reaction(
                self.config.channel,
                r"[a-z_\+]+",
                self.events.correct_guess["ts"],
            ),
        ]

        # Ensure each expected reaction exists
        while not self.reactions:
            time.sleep(0.5)

        for i, (channel, emoji, ts) in enumerate(reactions):
            assert channel == self.reactions[total_reactions + i][0]
            assert emoji.match(self.reactions[total_reactions + i][1])
            assert ts == self.reactions[total_reactions + i][2]

        # Ensure total volume is as expected
        total_reactions += len(reactions)
        assert len(self.reactions) == total_reactions

    def test_only_guess_when_guessing(self):
        """Ensures we can only 'guess' correctly when state is guessing"""
        assert self.state["step"] == "new_game"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "new_game"
        assert (
            self.config.channel,
            f"<@{self.config.player_3}>++",
        ) not in self.responses

        self.send_event(self.events.new_game)
        assert self.state["step"] == "waiting"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert (
            self.config.channel,
            f"<@{self.config.player_3}>++",
        ) not in self.responses

        self.send_event(self.events.posted_emojirade)
        assert self.state["step"] == "provided"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "provided"
        assert (
            self.config.channel,
            f"<@{self.config.player_3}>++",
        ) not in self.responses

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert (self.config.channel, f"<@{self.config.player_3}>++") in self.responses

    def test_two_games_in_a_row(self):
        """Plays 2 games in a row to ensure state is maintained"""
        self.reset_and_transition_to("guessing")
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_1
        assert self.state["winner"] == self.config.player_2
        assert self.state["emojirade"] == [self.config.emojirade]
        assert self.state["raw_emojirade"] == [self.config.emojirade]

        self.send_event(self.events.correct_guess)
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None
        assert (self.config.channel, f"<@{self.config.player_3}>++") in self.responses
        assert any(
            self.config.channel == channel
            and f"Congrats <@{self.config.player_3}>, you're now at 1 point" in msg
            for channel, msg in self.responses
        )

        emojirade = "second"
        override = {"user": self.config.player_2, "text": f"emojirade {emojirade}"}
        self.send_event({**self.events.posted_emojirade, **override})
        assert self.state["step"] == "provided"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] == [emojirade]
        assert self.state["raw_emojirade"] == [emojirade]

        override = {"user": self.config.player_3}
        self.send_event({**self.events.posted_emoji, **override})
        assert self.state["step"] == "guessing"
        assert self.state["old_winner"] == self.config.player_2
        assert self.state["winner"] == self.config.player_3
        assert self.state["emojirade"] == [emojirade]
        assert self.state["raw_emojirade"] == [emojirade]

        override = {"user": self.config.player_1, "text": emojirade}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "waiting"
        assert self.state["old_winner"] == self.config.player_3
        assert self.state["winner"] == self.config.player_1
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None
        assert (self.config.channel, f"<@{self.config.player_1}>++") in self.responses
        assert any(
            self.config.channel == channel
            and f"Congrats <@{self.config.player_1}>, you're now at 1 point" in msg
            for channel, msg in self.responses
        )

    def test_emojirade_alternatives(self):
        """Performs alternative emojirades checks"""
        # Check alternative A ('foo')
        self.reset_and_transition_to("waiting")

        override = {"text": "emojirade foo | bar"}
        self.send_event({**self.events.posted_emojirade, **override})
        assert self.state["step"] == "provided"
        assert self.state["emojirade"] == ["foo", "bar"]
        assert self.state["raw_emojirade"] == ["foo", "bar"]
        assert not self.scoreboard["scores"]

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"
        assert self.state["emojirade"] == ["foo", "bar"]
        assert self.state["raw_emojirade"] == ["foo", "bar"]
        assert not self.scoreboard["scores"]

        override = {"text": "foo"}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "waiting"
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None

        # Check alternative B ('bar')
        self.reset_and_transition_to("waiting")

        override = {"text": "emojirade foo | bar"}
        self.send_event({**self.events.posted_emojirade, **override})
        assert self.state["step"] == "provided"
        assert self.state["emojirade"] == ["foo", "bar"]
        assert self.state["raw_emojirade"] == ["foo", "bar"]
        assert not self.scoreboard["scores"]

        self.send_event(self.events.posted_emoji)
        assert self.state["step"] == "guessing"
        assert self.state["emojirade"] == ["foo", "bar"]
        assert self.state["raw_emojirade"] == ["foo", "bar"]
        assert not self.scoreboard["scores"]

        override = {"text": "bar"}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "waiting"
        assert self.state["emojirade"] is None
        assert self.state["raw_emojirade"] is None

    def test_scott_factor_exceeded(self):
        """Performs tests for guesses exceeding the scott factor"""
        # Test something 'within' the scott factor
        self.reset_and_transition_to("guessing")

        assert self.state["step"] == "guessing"

        override = {"text": f"0 {self.config.emojirade} 1"}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "waiting"

        # Test something 'outside' the scott factor
        self.reset_and_transition_to("guessing")

        assert self.state["step"] == "guessing"

        override = {"text": f"blah1234567890 {self.config.emojirade} blah0987654321"}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "guessing"

    def test_word_boundary_matching(self):
        """Performs tests to ensure emojirade matches only occur on word boundaries"""
        # Test a word, should work
        self.reset_and_transition_to("guessing")

        assert self.state["step"] == "guessing"

        override = {"text": f"0 {self.events.correct_guess['text']} 1"}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "waiting"

        # Test a sub-word, shouldn't work
        self.reset_and_transition_to("guessing")

        assert self.state["step"] == "guessing"

        override = {"text": f"0 a{self.events.correct_guess['text']}b 1"}
        self.send_event({**self.events.correct_guess, **override})
        assert self.state["step"] == "guessing"

    def test_sanitization(self):
        """Test that the sanitize_text helper works as expected"""
        self.reset_and_transition_to("waiting")

        raw_rade = "Späce : THE\t\t\tfinal\v- f_r_ö_n+t/ier"
        override = {"text": f"emojirade   {raw_rade}"}
        self.send_event({**self.events.posted_emojirade, **override})

        assert self.state["step"] == "provided"
        assert self.state["emojirade"] == ["space the final frontier"]
        assert self.state["raw_emojirade"] == [raw_rade]

    def test_emoji_detection(self):
        """Performs tests to ensure when an emoji is posted the game progresses in state"""
        self.reset_and_transition_to("provided")

        # Valid emoji
        override = {"text": ":gun:"}
        self.send_event({**self.events.posted_emoji, **override})
        assert self.state["step"] == "guessing"

        # Invalid emoji
        self.reset_and_transition_to("provided")

        override = {"text": ":gun"}
        self.send_event({**self.events.posted_emoji, **override})
        assert self.state["step"] == "provided"

        # Emoji in middle of text
        self.reset_and_transition_to("provided")

        override = {"text": "gun :gun: gun"}
        self.send_event({**self.events.posted_emoji, **override})
        assert self.state["step"] == "guessing"

    def test_correct_guess_reaction(self):
        """Checks that a valid emoji is 'reacted' on the winning guess"""
        self.reset_and_transition_to("guessing")

        assert self.state["step"] == "guessing"
        self.send_event(self.events.correct_guess)

        assert self.state["step"] == "waiting"

        expected_reaction = (
            self.config.channel,
            re.compile(r"[a-z_\+]+"),
            self.events.correct_guess["ts"],
        )

        while not self.reactions:
            time.sleep(0.5)

        # First reaction is for setting the emojirade
        # We test the second one (this one)
        assert expected_reaction[0] == self.reactions[1][0]
        assert expected_reaction[1].match(self.reactions[1][1])
        assert expected_reaction[2] == self.reactions[1][2]

    def test_recent_edit_works(self):
        """Checks that a recent edit is counted as a guess"""
        self.reset_and_transition_to("guessing")

        self.send_event(self.events.incorrect_guess)
        assert self.state["step"] == "guessing"

        # This is ~20s 'after' the standard events
        edit_ts = "1000000020.000000"

        # 'edit' event
        self.send_event(
            {
                "subtype": "message_changed",
                "hidden": True,
                "message": {
                    "type": "message",
                    "text": self.events.correct_guess["text"],
                    "user": self.events.correct_guess["user"],
                    "team": self.events.correct_guess["team"],
                    "edited": {
                        "user": self.events.correct_guess["user"],
                        "ts": edit_ts,
                    },
                    "ts": edit_ts,
                    "source_team": self.events.correct_guess["team"],
                    "user_team": self.events.correct_guess["team"],
                },
                "channel": self.events.base["channel"],
                "previous_message": {
                    "type": "message",
                    "text": self.events.incorrect_guess["text"],
                    "user": self.events.incorrect_guess["user"],
                    "ts": self.events.incorrect_guess["ts"],
                    "team": self.events.incorrect_guess["team"],
                },
                "event_ts": edit_ts,
                "ts": edit_ts,
                "text": self.events.correct_guess["text"],
            }
        )

        # Edit event should trigger the transition
        assert self.state["step"] == "waiting"

    def test_recent_edit_fails(self):
        """Checks that a non-recent edit is ignored as a guess"""
        self.reset_and_transition_to("guessing")

        self.send_event(self.events.incorrect_guess)
        assert self.state["step"] == "guessing"

        # This is ~40s 'after' the standard events
        edit_ts = "1000000040.000000"

        # 'edit' event
        self.send_event(
            {
                "subtype": "message_changed",
                "hidden": True,
                "message": {
                    "type": "message",
                    "text": self.events.correct_guess["text"],
                    "user": self.events.correct_guess["user"],
                    "team": self.events.correct_guess["team"],
                    "edited": {
                        "user": self.events.correct_guess["user"],
                        "ts": edit_ts,
                    },
                    "ts": edit_ts,
                    "source_team": self.events.correct_guess["team"],
                    "user_team": self.events.correct_guess["team"],
                },
                "channel": self.events.base["channel"],
                "previous_message": {
                    "type": "message",
                    "text": self.events.incorrect_guess["text"],
                    "user": self.events.incorrect_guess["user"],
                    "ts": self.events.incorrect_guess["ts"],
                    "team": self.events.incorrect_guess["team"],
                },
                "event_ts": edit_ts,
                "ts": edit_ts,
                "text": self.events.correct_guess["text"],
            }
        )

        # Edit event should not trigger the transition
        assert self.state["step"] == "guessing"
