from plusplusbot.tests.helper import EmojiradeBotTester

import re


class TestBotCommands(EmojiradeBotTester):
    """
    Tests various game commands against the bot
    """
    def test_plusplus_new_game(self):
        """ Cannot ++ someone when the game is not in progress """
        state = self.bot.gamestate.state[self.config.channel]

        assert state["step"] == "new_game"

        self.send_event(self.events.plusplus)
        assert (self.config.channel, "Sorry, but we need to be guessing! Get the winner to start posting the next 'rade!") in self.responses

    def test_leaderboard_output(self):
        """ Ensure leaderboard output is consistent """
        self.reset_and_transition_to("waiting")

        self.bot.scorekeeper.scoreboard[self.config.channel] = {
            "scores": {
                "David Pham": 168,
                "fendy Haman": 120,
                "Michael Mitchell": 118,
                "Timothy Sinclair": 100,
                "Stephen Verschuren": 81,
                "Mark Chaves": 81,
                "Andres Quillian": 30,
                "Justin Fendi": 24,
                "Scott Burke": 23,
                "Steve Robbins": 16,
                "Agung Alford": 9,
                "James Gream": 1
            },
        }

        expected = """```
 1. David Pham         [ 168 points ]
 2. fendy Haman        [ 120 points ]
 3. Michael Mitchell   [ 118 points ]
 4. Timothy Sinclair   [ 100 points ]
 5. Stephen Verschuren [  81 points ]
 6. Mark Chaves        [  81 points ]
 7. Andres Quillian    [  30 points ]
 8. Justin Fendi       [  24 points ]
 9. Scott Burke        [  23 points ]
10. Steve Robbins      [  16 points ]
11. Agung Alford       [   9 points ]
12. James Gream        [   1 point  ]
```"""

        self.send_event(self.events.leaderboard)

        assert (self.config.channel, expected) in self.responses

    def test_fixwinner(self):
        """ Ensure fixwinner does the right thing """
        self.reset_and_transition_to("guessed")

        state = self.bot.gamestate.state[self.config.channel]

        self.send_event(self.events.fixwinner)
        assert state["old_winner"] == self.config.player_2
        assert state["winner"] == self.config.player_4
        assert self.bot.scorekeeper.current_score(self.config.channel, self.config.player_3) == (0, False)
        assert self.bot.scorekeeper.current_score(self.config.channel, self.config.player_4) == (1, True)

        # Check the user cannot award to themselves
        self.reset_and_transition_to("guessed")

        state = self.bot.gamestate.state[self.config.channel]

        override = {"text": "<@{0}> fixwinner <@{1}>".format(self.config.bot_id, self.config.player_2)}
        self.send_event({**self.events.fixwinner, **override})

        expected = ":face_palm: You can't award yourself the win"
        assert (self.config.channel, expected) in self.responses

        assert state["old_winner"] == self.config.player_2
        assert state["winner"] == self.config.player_3
        assert self.bot.scorekeeper.current_score(self.config.channel, self.config.player_3) == (1, True)
        assert self.bot.scorekeeper.current_score(self.config.channel, self.config.player_4) == (0, False)

        # Check the user cannot award to the winner (no-op)
        self.reset_and_transition_to("guessed")

        state = self.bot.gamestate.state[self.config.channel]

        override = {"text": "<@{0}> fixwinner <@{1}>".format(self.config.bot_id, self.config.player_3)}
        self.send_event({**self.events.fixwinner, **override})

        expected = "This won't actually do anything? :shrug::face_with_monocle:"
        assert (self.config.channel, expected) in self.responses

        assert state["old_winner"] == self.config.player_2
        assert state["winner"] == self.config.player_3
        assert self.bot.scorekeeper.current_score(self.config.channel, self.config.player_3) == (1, True)
        assert self.bot.scorekeeper.current_score(self.config.channel, self.config.player_4) == (0, False)

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

    def test_set_emojirade_raw_output(self):
        """ Ensure that the emojirade passed to the winner isn't sanitized """
        self.reset_and_transition_to("waiting")

        emojirade = "test-123-test_123"

        override = {"text": "emojirade {0}".format(emojirade)}
        self.send_event({**self.events.posted_emojirade, **override})

        assert (self.config.player_2_channel,
                "Hey, <@{old_winner}> made the emojirade `{emojirade}`, good luck!".format(
                    old_winner=self.config.player_1,
                    emojirade=emojirade
                )) in self.responses

    def test_set_emojirade_plurals(self):
        """ Ensure depluralization is as expected """
        cases = [
            ("when the cow's come home", "when the cows come home"),  # No action
            ("australian banks", "australian bank"),                  # Action
            ("Michael Rogers", "michael roger"),                      # Action
        ]

        for emojirade, expected in cases:
            self.reset_and_transition_to("waiting")

            override = {"text": "emojirade {0}".format(emojirade)}
            self.send_event({**self.events.posted_emojirade, **override})

            state = self.bot.gamestate.state[self.config.channel]
            assert state["emojirade"][0] == expected

    def test_set_emojirade_alternatives_output(self):
        """ Ensure that the emojirade alternatives output is expected """
        self.reset_and_transition_to("waiting")

        emojirade = "foo | bar"

        override = {"text": "emojirade {0}".format(emojirade)}
        self.send_event({**self.events.posted_emojirade, **override})

        assert (self.config.player_2_channel,
                "Hey, <@{old_winner}> made the emojirade `foo`, with alternatives `bar`, good luck!".format(
                    old_winner=self.config.player_1,
                    emojirade=emojirade
                )) in self.responses

    def test_user_override(self):
        self.reset_and_transition_to("guessing")

        state = self.bot.gamestate.state[self.config.channel]

        # Player 4 is not involved in this round
        override = {"user": self.config.player_4, "text": "<@{0}>++ player=<@{1}>".format(self.config.player_3, self.config.player_2)}
        self.send_event({**self.events.manual_award, **override})

        assert state["step"] == "waiting"
        assert state["winner"] == self.config.player_3

    def test_channel_override(self):
        self.reset_and_transition_to("guessing")

        state = self.bot.gamestate.state[self.config.channel]

        override = {
            "channel": self.config.bot_channel,
            "text": "{0} channel=<#{1}|emojirades>".format(self.config.emojirade, self.config.channel)
        }
        self.send_event({**self.events.correct_guess, **override})

        assert state["step"] == "waiting"
        assert state["winner"] == self.config.player_3

    def test_help(self):
        from plusplusbot.command.command_registry import CommandRegistry

        self.send_event(self.events.help)

        commands = CommandRegistry.prepare_commands()

        for command in commands.values():
            assert re.compile(r"{0}\s+{1}".format(re.escape(command.example), re.escape(command.short_description))) \
                     .search(self.responses[-2][1])
