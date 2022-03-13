import time
import re

from emojirades.persistence import GamestateStep
from emojirades.commands.gamestate_commands.correct_guess_command import (
    CorrectGuessCommand,
)


class TestBotScenarios:
    """
    Tests various game scenarios against the bot
    """

    def test_valid_complete_game(self, slack_web_api, bot):
        """Performs a complete valid round"""
        assert bot.step == GamestateStep.NEW_GAME
        assert bot.get_xyz("previous_winner") is None
        assert bot.get_xyz("current_winner") is None
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.new_game)
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.posted_emojirade)
        assert bot.step == GamestateStep.PROVIDED
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.posted_emoji)
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.incorrect_guess)
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.correct_guess)
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("previous_winner") == bot.config.player_2
        assert bot.get_xyz("current_winner") == bot.config.player_3
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None
        assert bot.scorekeeper.scoreboard(bot.config.channel) == [
            (1, bot.config.player_3, 1)
        ]

    def test_valid_manually_awarded_complete_game(self, slack_web_api, bot):
        """Performs a complete valid round but the win is manually awarded"""
        assert bot.step == GamestateStep.NEW_GAME
        assert bot.get_xyz("previous_winner") is None
        assert bot.get_xyz("current_winner") is None
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.new_game)
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.posted_emojirade)
        assert bot.step == GamestateStep.PROVIDED
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.posted_emoji)
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.incorrect_guess)
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.manual_award)
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("previous_winner") == bot.config.player_2
        assert bot.get_xyz("current_winner") == bot.config.player_3
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None
        assert bot.scorekeeper.scoreboard(bot.config.channel) == [
            (1, bot.config.player_3, 1)
        ]

    def test_valid_responses(self, slack_web_api, bot):
        """
        Tests that the expected responses are bring returned
        Response order is asserted along with equality
        """

        def response(dst, msg):
            if isinstance(msg, list):
                return (dst, [re.compile(i) for i in msg])

            return (dst, re.compile(msg))

        def reaction(dst, emoji, ts):
            return (dst, re.compile(emoji), ts)

        total_responses = 0
        total_reactions = 0

        # Assert game hasn't started yet
        assert bot.step == GamestateStep.NEW_GAME
        assert len(slack_web_api.responses) == total_responses

        # User starts a new round manually
        bot.send(bot.events.new_game)

        # Expected *new* responses
        responses = [
            response(
                bot.config.channel,
                f"<@{bot.config.player_1}> has set the old winner to {bot.config.player_1_name} and the winner to {bot.config.player_2_name}",
            ),
            response(
                bot.config.channel,
                f"It's now <@{bot.config.player_1}>'s turn to provide {bot.config.player_2_name} with the next 'rade!",
            ),
            response(
                bot.config.player_1_channel,
                f"You'll now need to send me the new 'rade for <@{bot.config.player_2}>",
            ),
            response(
                bot.config.player_1_channel,
                "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade",
            ),
        ]

        # Ensure each expected response exists in actual responses
        for i, (channel, msg) in enumerate(responses):
            assert channel == slack_web_api.responses[i][0]
            assert msg.match(slack_web_api.responses[i][1])

        # Ensure total volume is as expected
        total_responses += len(responses)
        assert len(slack_web_api.responses) == total_responses

        # User sends a 'rade
        bot.send(bot.events.posted_emojirade)

        # Expected *new* responses
        responses = [
            response(
                bot.config.player_2_channel,
                f"Hey, <@{bot.config.player_1}> made the emojirade `{bot.config.emojirade}`, good luck!",
            ),
            response(
                bot.config.channel,
                f":mailbox: 'rade sent to <@{bot.config.player_2}>",
            ),
        ]

        # Ensure each expected response exists in actual responses
        for i, (channel, msg) in enumerate(responses):
            assert channel == slack_web_api.responses[total_responses + i][0]
            assert msg.match(slack_web_api.responses[total_responses + i][1])

        # Ensure total volume is as expected
        total_responses += len(responses)
        assert len(slack_web_api.responses) == total_responses

        # Expected *new* reactions
        reactions = [
            reaction(
                bot.config.player_1_channel,
                r"(\+1|ok)",
                bot.events.posted_emojirade["ts"],
            ),
        ]

        # Ensure each expected reaction exists
        while not slack_web_api.reactions:
            time.sleep(0.5)

        for i, (channel, emoji, ts) in enumerate(reactions):
            assert channel == slack_web_api.reactions[total_reactions + i][0]
            assert emoji.match(slack_web_api.reactions[total_reactions + i][1])
            assert ts == slack_web_api.reactions[total_reactions + i][2]

        # Ensure total volume is as expected
        total_reactions += len(reactions)
        assert len(slack_web_api.reactions) == total_reactions

        # User starts posting emoji's for the current round
        bot.send(bot.events.posted_emoji)
        assert len(slack_web_api.responses) == total_responses  # Bot shouldn't respond

        # User posts a correct guess
        bot.send(bot.events.correct_guess)

        # Expected *new* responses
        responses = [
            response(bot.config.channel, CorrectGuessCommand.first_guess_messages),
            response(bot.config.channel, f"<@{bot.config.player_3}>\\+\\+"),
            response(
                bot.config.channel,
                f"Congrats <@{bot.config.player_3}>, you're now at 1 point :[a-z_]+:",
            ),
            response(
                bot.config.channel,
                f"The correct emojirade was `{bot.config.emojirade}`",
            ),
            response(
                bot.config.player_2_channel,
                f"You'll now need to send me the new 'rade for <@{bot.config.player_3}>",
            ),
            response(
                bot.config.player_2_channel,
                "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade",
            ),
        ]

        # Ensure each expected response exists in actual responses
        for i, (channel, msg) in enumerate(responses):
            assert channel == slack_web_api.responses[total_responses + i][0]

            if isinstance(msg, list):
                assert any(
                    j.match(slack_web_api.responses[total_responses + i][1])
                    for j in msg
                )
            else:
                assert msg.match(slack_web_api.responses[total_responses + i][1])

        # Ensure total volume is as expected
        total_responses += len(responses)
        assert len(slack_web_api.responses) == total_responses

        # Expected *new* reactions
        reactions = [
            reaction(
                bot.config.channel,
                r"[a-z_\+]+",
                bot.events.correct_guess["ts"],
            ),
        ]

        # Ensure each expected reaction exists
        while not slack_web_api.reactions:
            time.sleep(0.5)

        for i, (channel, emoji, ts) in enumerate(reactions):
            assert channel == slack_web_api.reactions[total_reactions + i][0]
            assert emoji.match(slack_web_api.reactions[total_reactions + i][1])
            assert ts == slack_web_api.reactions[total_reactions + i][2]

        # Ensure total volume is as expected
        total_reactions += len(reactions)
        assert len(slack_web_api.reactions) == total_reactions

    def test_only_guess_when_guessing(self, slack_web_api, bot):
        """Ensures we can only 'guess' correctly when state is guessing"""
        assert bot.step == GamestateStep.NEW_GAME

        bot.send(bot.events.correct_guess)
        assert bot.step == GamestateStep.NEW_GAME
        assert (
            bot.config.channel,
            f"<@{bot.config.player_3}>++",
        ) not in slack_web_api.responses

        bot.send(bot.events.new_game)
        assert bot.step == GamestateStep.WAITING

        bot.send(bot.events.correct_guess)
        assert bot.step == GamestateStep.WAITING
        assert (
            bot.config.channel,
            f"<@{bot.config.player_3}>++",
        ) not in slack_web_api.responses

        bot.send(bot.events.posted_emojirade)
        assert bot.step == GamestateStep.PROVIDED

        bot.send(bot.events.correct_guess)
        assert bot.step == GamestateStep.PROVIDED
        assert (
            bot.config.channel,
            f"<@{bot.config.player_3}>++",
        ) not in slack_web_api.responses

        bot.send(bot.events.posted_emoji)
        assert bot.step == GamestateStep.GUESSING

        bot.send(bot.events.correct_guess)
        assert bot.step == GamestateStep.WAITING
        assert (
            bot.config.channel,
            f"<@{bot.config.player_3}>++",
        ) in slack_web_api.responses

    def test_two_games_in_a_row(self, slack_web_api, bot):
        """Plays 2 games in a row to ensure state is maintained"""
        bot.reset_and_transition_to("guessing")
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("previous_winner") == bot.config.player_1
        assert bot.get_xyz("current_winner") == bot.config.player_2
        assert bot.get_xyz("emojirade") == f'["{bot.config.emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{bot.config.emojirade}"]'

        bot.send(bot.events.correct_guess)
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("previous_winner") == bot.config.player_2
        assert bot.get_xyz("current_winner") == bot.config.player_3
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None

        assert (
            bot.config.channel,
            f"<@{bot.config.player_3}>++",
        ) in slack_web_api.responses
        assert any(
            bot.config.channel == channel
            and f"Congrats <@{bot.config.player_3}>, you're now at 1 point" in msg
            for channel, msg in slack_web_api.responses
        )

        emojirade = "second"
        override = {"user": bot.config.player_2, "text": f"emojirade {emojirade}"}
        bot.send({**bot.events.posted_emojirade, **override})
        assert bot.step == GamestateStep.PROVIDED
        assert bot.get_xyz("previous_winner") == bot.config.player_2
        assert bot.get_xyz("current_winner") == bot.config.player_3
        assert bot.get_xyz("emojirade") == f'["{emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{emojirade}"]'

        override = {"user": bot.config.player_3}
        bot.send({**bot.events.posted_emoji, **override})
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("previous_winner") == bot.config.player_2
        assert bot.get_xyz("current_winner") == bot.config.player_3
        assert bot.get_xyz("emojirade") == f'["{emojirade}"]'
        assert bot.get_xyz("raw_emojirade") == f'["{emojirade}"]'

        override = {"user": bot.config.player_1, "text": emojirade}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("previous_winner") == bot.config.player_3
        assert bot.get_xyz("current_winner") == bot.config.player_1
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None

        assert (
            bot.config.channel,
            f"<@{bot.config.player_1}>++",
        ) in slack_web_api.responses
        assert any(
            bot.config.channel == channel
            and f"Congrats <@{bot.config.player_1}>, you're now at 1 point" in msg
            for channel, msg in slack_web_api.responses
        )

    def test_emojirade_alternatives(self, slack_web_api, bot):
        """Performs alternative emojirades checks"""
        # Check alternative A ('foo')
        bot.reset_and_transition_to("waiting")

        override = {"text": "emojirade foo | bar"}
        bot.send({**bot.events.posted_emojirade, **override})
        assert bot.step == GamestateStep.PROVIDED
        assert bot.get_xyz("emojirade") == f'["foo", "bar"]'
        assert bot.get_xyz("raw_emojirade") == f'["foo", "bar"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.posted_emoji)
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("emojirade") == f'["foo", "bar"]'
        assert bot.get_xyz("raw_emojirade") == f'["foo", "bar"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        override = {"text": "foo"}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None

        # Check alternative B ('bar')
        bot.reset_and_transition_to("waiting")

        override = {"text": "emojirade foo | bar"}
        bot.send({**bot.events.posted_emojirade, **override})
        assert bot.step == GamestateStep.PROVIDED
        assert bot.get_xyz("emojirade") == f'["foo", "bar"]'
        assert bot.get_xyz("raw_emojirade") == f'["foo", "bar"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        bot.send(bot.events.posted_emoji)
        assert bot.step == GamestateStep.GUESSING
        assert bot.get_xyz("emojirade") == f'["foo", "bar"]'
        assert bot.get_xyz("raw_emojirade") == f'["foo", "bar"]'
        assert len(bot.scorekeeper.scoreboard(bot.config.channel)) == 0

        override = {"text": "bar"}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.WAITING
        assert bot.get_xyz("emojirade") is None
        assert bot.get_xyz("raw_emojirade") is None

    def test_scott_factor_exceeded(self, slack_web_api, bot):
        """Performs tests for guesses exceeding the scott factor"""
        # Test something 'within' the scott factor
        bot.reset_and_transition_to("guessing")

        assert bot.step == GamestateStep.GUESSING

        override = {"text": f"0 {bot.config.emojirade} 1"}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.WAITING

        # Test something 'outside' the scott factor
        bot.reset_and_transition_to("guessing")

        assert bot.step == GamestateStep.GUESSING

        override = {"text": f"blah1234567890 {bot.config.emojirade} blah0987654321"}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.GUESSING

    def test_word_boundary_matching(self, slack_web_api, bot):
        """Performs tests to ensure emojirade matches only occur on word boundaries"""
        # Test a word, should work
        bot.reset_and_transition_to("guessing")

        assert bot.step == GamestateStep.GUESSING

        override = {"text": f"0 {bot.events.correct_guess['text']} 1"}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.WAITING

        # Test a sub-word, shouldn't work
        bot.reset_and_transition_to("guessing")

        assert bot.step == GamestateStep.GUESSING

        override = {"text": f"0 a{bot.events.correct_guess['text']}b 1"}
        bot.send({**bot.events.correct_guess, **override})
        assert bot.step == GamestateStep.GUESSING

    def test_sanitization(self, slack_web_api, bot):
        """Test that the sanitize_text helper works as expected"""
        bot.reset_and_transition_to("waiting")

        raw_rade = "Späce : THE\t\t\tfinal\v- f_r_ö_n+t/ier"
        override = {"text": f"emojirade   {raw_rade}"}
        bot.send({**bot.events.posted_emojirade, **override})

        assert bot.step == GamestateStep.PROVIDED
        assert bot.get_xyz("emojirade") == f'["space the final frontier"]'
        assert (
            bot.get_xyz("raw_emojirade").encode().decode("unicode-escape")
            == f'["{raw_rade}"]'
        )

    def test_emoji_detection(self, slack_web_api, bot):
        """Performs tests to ensure when an emoji is posted the game progresses in state"""
        bot.reset_and_transition_to("provided")

        # Valid emoji
        override = {"text": ":gun:"}
        bot.send({**bot.events.posted_emoji, **override})
        assert bot.step == GamestateStep.GUESSING

        # Invalid emoji
        bot.reset_and_transition_to("provided")

        override = {"text": ":gun"}
        bot.send({**bot.events.posted_emoji, **override})
        assert bot.step == GamestateStep.PROVIDED

        # Emoji in middle of text
        bot.reset_and_transition_to("provided")

        override = {"text": "gun :gun: gun"}
        bot.send({**bot.events.posted_emoji, **override})
        assert bot.step == GamestateStep.GUESSING

    def test_correct_guess_reaction(self, slack_web_api, bot):
        """Checks that a valid emoji is 'reacted' on the winning guess"""
        bot.reset_and_transition_to("guessing")

        assert bot.step == GamestateStep.GUESSING
        bot.send(bot.events.correct_guess)

        assert bot.step == GamestateStep.WAITING

        expected_reaction = (
            bot.config.channel,
            re.compile(r"[a-z_\+]+"),
            bot.events.correct_guess["ts"],
        )

        while not slack_web_api.reactions:
            time.sleep(0.5)

        # First reaction is for setting the emojirade
        # We test the second one (this one)
        assert expected_reaction[0] == slack_web_api.reactions[1][0]
        assert expected_reaction[1].match(slack_web_api.reactions[1][1])
        assert expected_reaction[2] == slack_web_api.reactions[1][2]

    def test_recent_edit_works(self, slack_web_api, bot):
        """Checks that a recent edit is counted as a guess"""
        bot.reset_and_transition_to("guessing")

        bot.send(bot.events.incorrect_guess)
        assert bot.step == GamestateStep.GUESSING

        # This is ~20s 'after' the standard events
        edit_ts = "1000000020.000000"

        # 'edit' event
        bot.send(
            {
                "type": "message",
                "subtype": "message_changed",
                "hidden": True,
                "message": {
                    "type": "message",
                    "text": bot.events.correct_guess["text"],
                    "user": bot.events.correct_guess["user"],
                    "team": bot.events.correct_guess["team"],
                    "edited": {
                        "user": bot.events.correct_guess["user"],
                        "ts": edit_ts,
                    },
                    "ts": edit_ts,
                    "source_team": bot.events.correct_guess["team"],
                    "user_team": bot.events.correct_guess["team"],
                },
                "channel": bot.events.base["channel"],
                "previous_message": {
                    "type": "message",
                    "text": bot.events.incorrect_guess["text"],
                    "user": bot.events.incorrect_guess["user"],
                    "ts": bot.events.incorrect_guess["ts"],
                    "team": bot.events.incorrect_guess["team"],
                },
                "event_ts": edit_ts,
                "ts": edit_ts,
                "text": bot.events.correct_guess["text"],
            }
        )

        # Edit event should trigger the transition
        assert bot.step == GamestateStep.WAITING

    def test_recent_edit_fails(self, slack_web_api, bot):
        """Checks that a non-recent edit is ignored as a guess"""
        bot.reset_and_transition_to("guessing")

        bot.send(bot.events.incorrect_guess)
        assert bot.step == GamestateStep.GUESSING

        # This is ~40s 'after' the standard events
        edit_ts = "1000000040.000000"

        # 'edit' event
        bot.send(
            {
                "subtype": "message_changed",
                "hidden": True,
                "message": {
                    "type": "message",
                    "text": bot.events.correct_guess["text"],
                    "user": bot.events.correct_guess["user"],
                    "team": bot.events.correct_guess["team"],
                    "edited": {
                        "user": bot.events.correct_guess["user"],
                        "ts": edit_ts,
                    },
                    "ts": edit_ts,
                    "source_team": bot.events.correct_guess["team"],
                    "user_team": bot.events.correct_guess["team"],
                },
                "channel": bot.events.base["channel"],
                "previous_message": {
                    "type": "message",
                    "text": bot.events.incorrect_guess["text"],
                    "user": bot.events.incorrect_guess["user"],
                    "ts": bot.events.incorrect_guess["ts"],
                    "team": bot.events.incorrect_guess["team"],
                },
                "event_ts": edit_ts,
                "ts": edit_ts,
                "text": bot.events.correct_guess["text"],
            }
        )

        # Edit event should not trigger the transition
        assert bot.step == GamestateStep.GUESSING
