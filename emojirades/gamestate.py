import logging
import json

from emojirades.commands.gamestate_commands.inferred_correct_guess_command import (
    InferredCorrectGuessCommand,
)
from emojirades.helpers import sanitize_text, match_emojirade, match_emoji
from emojirades.helpers import ScottFactorExceededException
from emojirades.persistence import GamestateStep, GamestateDB
from emojirades.commands import BaseCommand
from emojirades.slack.event import Event


module_logger = logging.getLogger("EmojiradesBot.gamestate")


class Gamestate:
    """
    Game State Machine:
    Winner     1: Communicates emojirade with emojis
    Guessers   2: Anyone else who isn't the Winner/Old Winner
    Guessers   3: Attempt guesses at the emojirade
    Guesser    4: Wins by guessing the emojirade
    Winner     5: Is now the Old Winner
    Guesser    6: Is now the Winner
    Old Winner 7: Makes a new emojirade and sends it to the Winner
               8: Go to step 1

    Steps of the game:
        new_game  : The game has no previous winner, manual intervention required
        waiting   : The old winner has not provided the winner with the new emojirade
        provided  : The winner has not posted anything since having recieved the emojirade
        guessing  : The winner has posted since having recieved the emojirade

    Step transitions:
        set_winners   : new_game -> waiting
        set_emojirade : waiting  -> provided
        winner_posted : provided -> guessing
        correct_guess : guessing -> waiting

    Step Overview
        new_game -(set_winners)-> waiting -(set_emojirade)-> provided -(winner_posted)-> guessing -|
                                     ^-----------------------(correct_guess)-----------------------|
    """

    class InvalidStateException(Exception):
        pass

    def __init__(self, session, workspace_id):
        self.handler = GamestateDB(session, workspace_id)

        self.logger = logging.getLogger("EmojiradesBot.gamestate.Gamestate")

    def in_progress(self, channel):
        invalid_steps = (GamestateStep.NEW_GAME,)

        return self.handler.get_xyz(channel, "step") not in invalid_steps

    def not_in_progress(self, channel):
        valid_steps = (GamestateStep.NEW_GAME, GamestateStep.WAITING)
        return self.handler.get_xyz(channel, "step") in valid_steps

    def guessing(self, channel):
        valid_steps = (GamestateStep.GUESSING,)
        return self.handler.get_xyz(channel, "step") in valid_steps

    def infer_commands(self, event: Event):
        """
        Keeps tabs on the conversation and updates gamestate if required
        Not to be called directly, used as another command source from the bot
        """
        channel = str(event.channel)
        user = str(event.player_id)
        text = str(event.text)

        if self.is_admin(channel, user):
            # Double check if we're overriding the channel
            channel_override_match = BaseCommand.channel_override_regex.match(text)

            if channel_override_match:
                channel = channel_override_match.groupdict()["channel_override"]

                text = text.replace(
                    channel_override_match.groupdict()["override_cmd"], ""
                )

            # Double check if we're overriding the user
            user_override_match = BaseCommand.user_override_regex.match(text)

            if user_override_match:
                user = user_override_match.groupdict()["user_override"]

                text = text.replace(user_override_match.groupdict()["override_cmd"], "")

        # Check to see if the winner is posting emoji's
        if (
            self.handler.get_xyz(channel, "step") == GamestateStep.PROVIDED
            and user == self.handler.get_xyz(channel, "current_winner")
            and match_emoji(text)
        ):
            self.winner_posted(channel, user)

        # If a user has edited an old (>30s) message, ignore it
        elif event.is_edit and not event.is_recent_edit:
            pass

        # Check to see if the users guess is right!
        elif self.handler.get_xyz(
            channel, "step"
        ) == GamestateStep.GUESSING and user not in (
            self.handler.get_xyz(channel, "previous_winner"),
            self.handler.get_xyz(channel, "current_winner"),
        ):
            guess = sanitize_text(text)

            try:
                emojirade = json.loads(self.handler.get_xyz(channel, "emojirade"))

                if match_emojirade(guess, emojirade):
                    self.logger.debug(
                        "emojirades='%s' guess='%s' status='correct'",
                        "|".join(emojirade),
                        guess,
                    )

                    yield InferredCorrectGuessCommand
                else:
                    self.logger.debug(
                        "emojirades='%s' guess='%s' status='incorrect'",
                        "|".join(emojirade),
                        guess,
                    )
            except ScottFactorExceededException:
                self.logger.debug(
                    "emojirade='%s' guess='%s' status='scott factor exceeded'",
                    "|".join(emojirade),
                    guess,
                )

            if self.handler.is_first_guess(channel):
                self.handler.set_xyz(channel, user, "first_guess", False)

    def get_admins(self, channel):
        return json.loads(self.handler.get_xyz(channel, "admins"))

    def set_admin(self, channel, user_id):
        return self.handler.add_admin(channel, user_id)

    def remove_admin(self, channel, user_id):
        return self.handler.remove_admin(channel, user_id)

    def is_admin(self, channel, user_id):
        admins = json.loads(self.handler.get_xyz(channel, "admins"))

        if not admins:
            # If no one is an admin, everyone is an admin!
            return True

        return user_id in admins

    def new_game(self, channel, previous_winner, current_winner):
        self.handler.new_game(channel, previous_winner, current_winner)

    def get_emojirade(self, channel):
        return json.loads(self.handler.get_xyz(channel, "emojirade"))

    def set_emojirade(self, channel, emojirades, user):
        valid_steps = (GamestateStep.WAITING, GamestateStep.PROVIDED)
        step = self.handler.get_xyz(channel, "step")

        if step not in valid_steps:
            raise self.InvalidStateException(
                f"Expecting state to be WAITING or PROVIDED, was {step}"
            )

        self.handler.set_many_xyz(
            channel,
            user,
            [
                ("emojirade", json.dumps([sanitize_text(i) for i in emojirades])),
                ("raw_emojirade", json.dumps(emojirades)),
                ("step", GamestateStep.PROVIDED),
            ],
        )

    def winner_posted(self, channel, user):
        valid_steps = (GamestateStep.PROVIDED,)
        step = self.handler.get_xyz(channel, "step")

        if step not in valid_steps:
            raise self.InvalidStateException(
                f"Expecting state to be PROVIDED, was {step}"
            )

        self.handler.set_many_xyz(
            channel,
            user,
            [
                ("step", GamestateStep.GUESSING),
                ("first_guess", True),
            ],
        )

    def correct_guess(self, channel, winner):
        valid_steps = (GamestateStep.GUESSING,)
        step = self.handler.get_xyz(channel, "step")

        if step not in valid_steps:
            raise self.InvalidStateException(
                f"Expecting state to be GUESSING, was {step}"
            )

        self.handler.set_many_xyz(
            channel,
            winner,
            [
                ("previous_winner", self.handler.get_xyz(channel, "current_winner")),
                ("current_winner", winner),
                ("step", GamestateStep.WAITING),
                ("emojirade", None),
                ("raw_emojirade", None),
            ],
        )

    def fixwinner(self, channel, winner):
        loser = self.handler.get_xyz(channel, "current_winner")

        self.handler.set_xyz(channel, winner, "current_winner", winner)

        return loser, winner

    def winners(self, channel):
        return (
            self.handler.get_xyz(channel, "previous_winner"),
            self.handler.get_xyz(channel, "current_winner"),
        )

    def step(self, channel):
        return self.handler.get_xyz(channel, "step")

    def get_channels(self):
        return self.handler.get_channels()

    def get_pending_channel(self, user):
        return self.handler.get_pending_channel(user)
