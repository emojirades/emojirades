import re

from emojirades.tests.helper import EmojiradeBotTester
from emojirades.persistence import GamestateStep


class TestBotCommands(EmojiradeBotTester):
    """
    Tests various game commands against the bot
    """

    def test_plusplus_new_game(self):
        """Cannot ++ someone when the game is not in progress"""
        assert self.step == GamestateStep.NEW_GAME

        self.send_event(self.events.plusplus)
        assert (
            self.config.channel,
            "Sorry, but we need to be guessing! Get the winner to start posting the next 'rade!",
        ) in self.responses

    def test_new_game_by_old_winner(self):
        """The old winner is allowed to 'reset' their rade if the game isn't in progress"""
        self.reset_and_transition_to("provided")
        self.gamestate.set_admin(self.config.channel, self.config.player_4)

        # Should be allowed
        self.send_event(self.events.new_game)
        assert self.step == GamestateStep.WAITING

        # Reset
        self.reset_and_transition_to("guessing")
        self.gamestate.set_admin(self.config.channel, self.config.player_4)

        # Should not be allowed
        self.send_event(self.events.new_game)
        assert self.step == GamestateStep.GUESSING

    def test_leaderboard_output(self):
        """Ensure leaderboard output is consistent"""
        self.reset_and_transition_to("waiting")

        user_scores = {
            "U00000001": ("David Pham", 168),
            "U00000002": ("fendy Haman", 120),
            "U00000003": ("Michael Mitchell", 118),
            "U00000004": ("Timothy Sinclair", 100),
            "U00000005": ("Stephen Verschuren", 81),
            "U00000006": ("Mark Chaves", 81),
            "U00000007": ("Andres Quillian", 81),
            "U00000008": ("Justin Fendi", 24),
            "U00000009": ("Scott Burke", 23),
            "U00000010": ("Steve Robbins", 9),
            "U00000011": ("Agung Alford", 9),
            "U00000012": ("James Gream", 1),
        }

        for user_id, (user_name, score) in user_scores.items():
            self.scorekeeper.overwrite(self.config.channel, user_id, score)

        self.workspace["slack"].pretty_name = lambda x: user_scores[x][0]

        expected = """```
 :: All Time leaderboard ::

 1. David Pham         [ 168 points ]
 2. fendy Haman        [ 120 points ]
 3. Michael Mitchell   [ 118 points ]
 4. Timothy Sinclair   [ 100 points ]
 5. Stephen Verschuren [  81 points ]
 5. Mark Chaves        [  81 points ]
 5. Andres Quillian    [  81 points ]
 8. Justin Fendi       [  24 points ]
 9. Scott Burke        [  23 points ]
10. Steve Robbins      [   9 points ]
10. Agung Alford       [   9 points ]
12. James Gream        [   1 point  ]
```"""

        self.send_event(self.events.leaderboard)

        self.workspace["slack"].pretty_name = self.pretty_name

        assert (self.config.channel, expected) in self.responses

    def test_fixwinner(self):
        """Ensure fixwinner does the right thing"""
        self.reset_and_transition_to("guessed")
        self.send_event(self.events.fixwinner)

        previous_winner, current_winner = self.gamestate.winners(self.config.channel)

        assert previous_winner == self.config.player_2
        assert current_winner == self.config.player_4

        # (position, score)
        assert self.scorekeeper.user_score(
            self.config.channel, self.config.player_4
        ) == (1, 1)
        assert self.scorekeeper.user_score(
            self.config.channel, self.config.player_3
        ) == (2, 0)

        # Check the user cannot award to themselves
        self.reset_and_transition_to("guessed")

        override = {
            "text": f"<@{self.config.bot_id}> fixwinner <@{self.config.player_2}>"
        }
        self.send_event({**self.events.fixwinner, **override})

        expected = ":face_palm: You can't award yourself the win"
        assert (self.config.channel, expected) in self.responses

        previous_winner, current_winner = self.gamestate.winners(self.config.channel)

        assert previous_winner == self.config.player_2
        assert current_winner == self.config.player_3

        # (position, score)
        assert self.scorekeeper.user_score(
            self.config.channel, self.config.player_3
        ) == (1, 1)
        assert self.scorekeeper.user_score(
            self.config.channel, self.config.player_4
        ) == (None, None)

        # Check the user cannot award to the winner (no-op)
        self.reset_and_transition_to("guessed")

        override = {
            "text": f"<@{self.config.bot_id}> fixwinner <@{self.config.player_3}>"
        }
        self.send_event({**self.events.fixwinner, **override})

        expected = "This won't actually do anything? :shrug::face_with_monocle:"
        assert (self.config.channel, expected) in self.responses

        previous_winner, current_winner = self.gamestate.winners(self.config.channel)

        assert previous_winner == self.config.player_2
        assert current_winner == self.config.player_3

        # (position, score)
        assert self.scorekeeper.user_score(
            self.config.channel, self.config.player_3
        ) == (1, 1)
        assert self.scorekeeper.user_score(
            self.config.channel, self.config.player_4
        ) == (None, None)

    def test_set_emojirade_banned_words(self):
        """Ensure that the emojirade can't contain banned words"""
        self.reset_and_transition_to("waiting")

        banned_emojirade = dict(self.events.posted_emojirade)
        banned_emojirade["text"] = "emojirade foo :pie: bar"

        self.send_event(banned_emojirade)
        assert (
            self.config.bot_channel,
            "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?",
        ) in self.responses

        assert self.step == GamestateStep.WAITING

        banned_emojirade = dict(self.events.posted_emojirade)
        banned_emojirade["text"] = "emojirade foo :+1: bar"

        self.send_event(banned_emojirade)
        assert (
            self.config.bot_channel,
            "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?",
        ) in self.responses
        assert self.step == GamestateStep.WAITING

        self.send_event(self.events.posted_emojirade)
        assert self.step == GamestateStep.PROVIDED

    def test_set_emojirade_raw_output(self):
        """Ensure that the emojirade passed to the winner isn't sanitized"""
        self.reset_and_transition_to("waiting")

        emojirade = "test-123-test_123"

        override = {"text": f"emojirade {emojirade}"}
        self.send_event({**self.events.posted_emojirade, **override})

        assert (
            self.config.player_2_channel,
            f"Hey, <@{self.config.player_1}> made the emojirade `{emojirade}`, good luck!",
        ) in self.responses

    def test_set_emojirade_alternatives_output(self):
        """Ensure that the emojirade alternatives output is expected"""
        self.reset_and_transition_to("waiting")

        emojirade = "foo | bar"

        override = {"text": f"emojirade {emojirade}"}
        self.send_event({**self.events.posted_emojirade, **override})

        assert (
            self.config.player_2_channel,
            f"Hey, <@{self.config.player_1}> made the emojirade `foo`, with alternatives `bar`, good luck!",
        ) in self.responses

    def test_set_emojirade_public_channel(self):
        """Ensure that the emojirade can only be set in a DM channel"""
        self.reset_and_transition_to("waiting")

        override = {"channel": self.config.channel}
        self.send_event({**self.events.posted_emojirade, **override})

        assert (
            self.config.player_1_channel,
            "Sorry, but this command can only be sent as a direct message!",
        ) in self.responses

    def test_redo_emojirade(self):
        """Ensure that a user can 'redo' an emojirade eg. typo"""
        self.reset_and_transition_to("provided")

        emojirade = "this_has_no typo"

        override = {"text": f"emojirade {emojirade}"}
        self.send_event({**self.events.posted_emojirade, **override})

        assert (
            self.config.player_2_channel,
            f"Hey, <@{self.config.player_1}> made the emojirade `{emojirade}`, good luck!",
        ) in self.responses

    def test_user_override(self):
        self.reset_and_transition_to("guessing")

        # Player 4 is not involved in this round
        override = {
            "user": self.config.player_4,
            "text": f"<@{self.config.player_3}>++ player=<@{self.config.player_2}>",
        }
        self.send_event({**self.events.manual_award, **override})

        _, current_winner = self.gamestate.winners(self.config.channel)

        assert self.step == GamestateStep.WAITING
        assert current_winner == self.config.player_3

    def test_channel_override(self):
        self.reset_and_transition_to("guessing")

        override = {
            "channel": self.config.bot_channel,
            "text": f"{self.config.emojirade} channel=<#{self.config.channel}|emojirades>",
        }
        self.send_event({**self.events.correct_guess, **override})

        _, current_winner = self.gamestate.winners(self.config.channel)

        assert self.step == GamestateStep.WAITING
        assert current_winner == self.config.player_3

    def test_help(self):
        from emojirades.commands.registry import CommandRegistry

        self.send_event(self.events.help)

        commands = CommandRegistry.command_patterns()

        for command in commands.values():
            for example, description in command.examples:
                assert re.compile(
                    fr"{re.escape(example)}\s+{re.escape(description)}"
                ).search(self.responses[-2][1])

    def test_game_status(self):
        self.reset_and_transition_to("waiting")
        self.send_event(self.events.game_status)

        assert (
            self.config.channel,
            f"Status: Waiting for <@{self.config.player_1}> to provide a 'rade to {self.config.player_2}",
        ) in self.responses

        self.reset_and_transition_to("provided")
        self.send_event(self.events.game_status)

        assert (
            self.config.channel,
            f"Status: Waiting for <@{self.config.player_2}> to post an emoji to kick off the round!",
        ) in self.responses
