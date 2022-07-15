import time
import re

from emojirades.persistence import GamestateStep


class TestBotCommands:
    """
    Tests various game commands against the bot
    """

    def test_plusplus_new_game(self, slack_web_api, bot):
        """Cannot ++ someone when the game is not in progress"""
        assert bot.step == GamestateStep.NEW_GAME

        bot.send(bot.events.plusplus)

        assert (
            bot.config.channel,
            "Sorry, but we need to be guessing! Get the winner to start posting the next 'rade!",
        ) in slack_web_api.responses

    def test_new_game_by_old_winner(self, slack_web_api, bot):
        """The old winner is allowed to 'reset' their rade if the game isn't in progress"""
        bot.reset_and_transition_to("provided")
        bot.gamestate.set_admin(bot.config.channel, bot.config.player_4)

        # Should be allowed
        bot.send(bot.events.new_game)
        assert bot.step == GamestateStep.WAITING

        # Reset
        bot.reset_and_transition_to("guessing")
        bot.gamestate.set_admin(bot.config.channel, bot.config.player_4)

        # Should not be allowed
        bot.send(bot.events.new_game)
        assert bot.step == GamestateStep.GUESSING

    def test_scoreboard_output(self, slack_web_api, bot):
        """Ensure leaderboard output is consistent"""
        bot.reset_and_transition_to("waiting")

        user_scores = {
            "U00000001": ("Player 1", 168),
            "U00000002": ("Player 2", 120),
            "U00000003": ("Player 3", 118),
            "U00000004": ("Player 4", 100),
            "U00000005": ("Generic User", 81),
            "U00000006": ("Generic User", 81),
            "U00000007": ("Generic User", 81),
            "U00000008": ("Generic User", 24),
            "U00000009": ("Generic User", 23),
            "U00000010": ("Generic User", 9),
            "U00000011": ("Generic User", 9),
            "U00000012": ("Generic User", 1),
            "U00000013": ("Last Player", 0),  # Should be ignored as it's <= 0
        }

        for user_id, (user_name, score) in user_scores.items():
            bot.scorekeeper.overwrite(bot.config.channel, user_id, score)

        expected = """```
 :: All Time leaderboard ::

 1. Player 1     [ 168 points ]
 2. Player 2     [ 120 points ]
 3. Player 3     [ 118 points ]
 4. Player 4     [ 100 points ]
 5. Generic User [  81 points ]
 5. Generic User [  81 points ]
 5. Generic User [  81 points ]
 8. Generic User [  24 points ]
 9. Generic User [  23 points ]
10. Generic User [   9 points ]
10. Generic User [   9 points ]
12. Generic User [   1 point  ]
```"""

        bot.send(bot.events.leaderboard)

        assert (bot.config.channel, expected) in slack_web_api.responses

    def test_fixwinner(self, slack_web_api, bot):
        """Ensure fixwinner does the right thing"""
        bot.reset_and_transition_to("guessed")
        bot.send(bot.events.fixwinner)

        previous_winner, current_winner = bot.gamestate.winners(bot.config.channel)

        assert previous_winner == bot.config.player_2
        assert current_winner == bot.config.player_4

        # (position, score)
        assert bot.scorekeeper.user_score(bot.config.channel, bot.config.player_4) == (
            1,
            1,
        )
        assert bot.scorekeeper.user_score(bot.config.channel, bot.config.player_3) == (
            2,
            0,
        )

        # Check the user cannot award to themselves
        bot.reset_and_transition_to("guessed", delete=True)

        override = {
            "text": f"<@{bot.config.bot_id}> fixwinner <@{bot.config.player_2}>"
        }
        bot.send({**bot.events.fixwinner, **override})

        expected = ":face_palm: You can't award yourself the win"
        assert (bot.config.channel, expected) in slack_web_api.responses

        previous_winner, current_winner = bot.gamestate.winners(bot.config.channel)

        assert previous_winner == bot.config.player_2
        assert current_winner == bot.config.player_3

        # (position, score)
        assert bot.scorekeeper.user_score(bot.config.channel, bot.config.player_3) == (
            1,
            1,
        )
        assert bot.scorekeeper.user_score(bot.config.channel, bot.config.player_4) == (
            None,
            None,
        )

        # Check the user cannot award to the winner (no-op)
        bot.reset_and_transition_to("guessed", delete=True)

        override = {
            "text": f"<@{bot.config.bot_id}> fixwinner <@{bot.config.player_3}>"
        }
        bot.send({**bot.events.fixwinner, **override})

        expected = "This won't actually do anything? :shrug::face_with_monocle:"
        assert (bot.config.channel, expected) in slack_web_api.responses

        previous_winner, current_winner = bot.gamestate.winners(bot.config.channel)

        assert previous_winner == bot.config.player_2
        assert current_winner == bot.config.player_3

        # (position, score)
        assert bot.scorekeeper.user_score(bot.config.channel, bot.config.player_3) == (
            1,
            1,
        )
        assert bot.scorekeeper.user_score(bot.config.channel, bot.config.player_4) == (
            None,
            None,
        )

    def test_set_emojirade_banned_words(self, slack_web_api, bot):
        """Ensure that the emojirade can't contain banned words"""
        bot.reset_and_transition_to("waiting")

        banned_emojirade = dict(bot.events.posted_emojirade)
        banned_emojirade["text"] = "emojirade foo :pie: bar"

        bot.send(banned_emojirade)
        assert (
            bot.config.bot_channel,
            "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?",
        ) in slack_web_api.responses

        assert bot.step == GamestateStep.WAITING

        banned_emojirade = dict(bot.events.posted_emojirade)
        banned_emojirade["text"] = "emojirade foo :+1: bar"

        bot.send(banned_emojirade)
        assert (
            bot.config.bot_channel,
            "Sorry, but that emojirade contained a banned word/phrase :no_good:, try again?",
        ) in slack_web_api.responses
        assert bot.step == GamestateStep.WAITING

        bot.send(bot.events.posted_emojirade)
        assert bot.step == GamestateStep.PROVIDED

    def test_set_emojirade_raw_output(self, slack_web_api, bot):
        """Ensure that the emojirade passed to the winner isn't sanitized"""
        bot.reset_and_transition_to("waiting")

        emojirade = "test-123-test_123"

        override = {"text": f"emojirade {emojirade}"}
        bot.send({**bot.events.posted_emojirade, **override})

        assert (
            bot.config.player_2_channel,
            f"Hey, <@{bot.config.player_1}> made the emojirade `{emojirade}`, good luck!",
        ) in slack_web_api.responses

    def test_set_emojirade_alternatives_output(self, slack_web_api, bot):
        """Ensure that the emojirade alternatives output is expected"""
        bot.reset_and_transition_to("waiting")

        emojirade = "foo | bar"

        override = {"text": f"emojirade {emojirade}"}
        bot.send({**bot.events.posted_emojirade, **override})

        assert (
            bot.config.player_2_channel,
            f"Hey, <@{bot.config.player_1}> made the emojirade `foo`, with alternatives `bar`, good luck!",
        ) in slack_web_api.responses

    def test_set_emojirade_alternatives_empty_variant(self, slack_web_api, bot):
        """Ensure that the emojirade alternatives cannot have an 'empty' variant"""
        bot.reset_and_transition_to("waiting")

        emojirade = "foo | | bar"

        override = {"text": f"emojirade {emojirade}"}
        bot.send({**bot.events.posted_emojirade, **override})

        assert (
            bot.config.player_2_channel,
            f"Hey, <@{bot.config.player_1}> made the emojirade `foo`, with alternatives `bar`, good luck!",
        ) in slack_web_api.responses

    def test_set_emojirade_public_channel(self, slack_web_api, bot):
        """Ensure that the emojirade can only be set in a DM channel"""
        bot.reset_and_transition_to("waiting")

        override = {"channel": bot.config.channel}
        bot.send({**bot.events.posted_emojirade, **override})

        assert (
            bot.config.player_1_channel,
            "Sorry, but this command can only be sent as a direct message!",
        ) in slack_web_api.responses

    def test_set_emojirade_linebreaks(self, slack_web_api, bot):
        """Ensure an emojirade can contain linebreaks"""
        bot.reset_and_transition_to("waiting")

        emojirade = "foo\nbar"

        override = {"text": f"emojirade {emojirade}"}
        bot.send({**bot.events.posted_emojirade, **override})

        assert (
            bot.config.player_2_channel,
            f"Hey, <@{bot.config.player_1}> made the emojirade `foo bar`, good luck!",
        ) in slack_web_api.responses

    def test_redo_emojirade(self, slack_web_api, bot):
        """Ensure that a user can 'redo' an emojirade eg. typo"""
        bot.reset_and_transition_to("provided")

        emojirade = "this_has_no typo"

        override = {"text": f"emojirade {emojirade}"}
        bot.send({**bot.events.posted_emojirade, **override})

        assert (
            bot.config.player_2_channel,
            f"Hey, <@{bot.config.player_1}> made the emojirade `{emojirade}`, good luck!",
        ) in slack_web_api.responses

    def test_user_override(self, slack_web_api, bot):
        bot.reset_and_transition_to("guessing")

        # Player 4 is not involved in this round
        override = {
            "user": bot.config.player_4,
            "text": f"<@{bot.config.player_3}>++ player=<@{bot.config.player_2}>",
        }
        bot.send({**bot.events.manual_award, **override})

        _, current_winner = bot.gamestate.winners(bot.config.channel)

        assert bot.step == GamestateStep.WAITING
        assert current_winner == bot.config.player_3

    def test_channel_override(self, slack_web_api, bot):
        bot.reset_and_transition_to("guessing")

        override = {
            "channel": bot.config.bot_channel,
            "text": f"{bot.config.emojirade} channel=<#{bot.config.channel}|emojirades>",
        }
        bot.send({**bot.events.correct_guess, **override})

        _, current_winner = bot.gamestate.winners(bot.config.channel)

        assert bot.step == GamestateStep.WAITING
        assert current_winner == bot.config.player_3

    def test_help(self, slack_web_api, bot):
        from emojirades.commands.registry import CommandRegistry

        bot.send(bot.events.help)

        commands = CommandRegistry.command_patterns()

        for command in commands.values():
            for example, description in command.examples:
                assert re.compile(
                    rf"{re.escape(example)}\s+{re.escape(description)}"
                ).search(slack_web_api.ephemeral_responses[-2][1])

    def test_game_status(self, slack_web_api, bot):
        bot.reset_and_transition_to("waiting")
        bot.send(bot.events.game_status)

        assert (
            bot.config.channel,
            f"Status: Waiting for <@{bot.config.player_1}> to provide a 'rade to {bot.config.player_2_name}",
        ) in slack_web_api.responses

        bot.reset_and_transition_to("provided")
        bot.send(bot.events.game_status)

        assert (
            bot.config.channel,
            f"Status: Waiting for <@{bot.config.player_2}> to post an emoji to kick off the round!",
        ) in slack_web_api.responses
