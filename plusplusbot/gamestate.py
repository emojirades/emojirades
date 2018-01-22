
from plusplusbot.handlers import get_configuration_handler
from plusplusbot.scorekeeper import InferredPlusPlusCommand
from plusplusbot.wrappers import only_in_progress, admin_check
from plusplusbot.commands import Command
from collections import defaultdict

import logging
import json
import csv
import re
import io

module_logger = logging.getLogger("PlusPlusBot.gamestate")

def get_handler(filename):
    class GameStateConfigurationHandler(get_configuration_handler(filename)):
        """
        Handles CRUD for the Game State configuration file
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            if bytes_content is None:
                return None

            return json.loads(bytes_content.decode("utf-8"))

        def save(self, state):
            bytes_content = json.dumps(state).encode("utf-8")

            super().save(bytes_content)

    return GameStateConfigurationHandler(filename)


class GameState(object):
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
        guessed   : The guesser has correctly guessed the emojirade

    Step transitions:
        set_winners   : new_game -> waiting
        set_emojirade : waiting  -> provided
        winner_posted : provided -> guessing
        correct_guess : guessing -> guessed
    """

    class InvalidStateException(Exception):
        pass

    def __init__(self, filename):
        self.logger = logging.getLogger("PlusPlusBot.gamestate.GameState")
        self.config = get_handler(filename)

        def state_factory():
            return {
                "step": "new_game",
                "old_winner": None,
                "winner": None,
                "emojirade": None,
                "admins": [],
            }

        self.state = defaultdict(state_factory)

        if filename:
            existing_state = self.config.load()

            if existing_state is not None:
                self.state.update(existing_state)
                self.logger.info("Loaded game state from {0}".format(filename))

    def in_progress(self, channel):
        return self.state[channel]["step"] not in ["new_game", "waiting"]

    def infer_commands(self, event):
        """ Keeps tabs on the conversation and updates gamestate if required """
        channel = event["channel"]
        user = event["user"]

        # Check to see if the winner is posting emoji's
        if self.state[channel]["step"] == "provided":
            if user == self.state[channel]["winner"]:
                if ':' in event["text"]:
                    self.winner_posted(channel)

        # Check to see if the users guess is right!
        elif self.state[channel]["step"] == "guessing":
            if user not in [self.state[channel]["old_winner"], self.state[channel]["winner"]]:
                emojirade = self.state[channel]["emojirade"].lower()
                guess = event["text"].lower()

                if guess == emojirade:
                    yield InferredCorrectGuess
                    yield InferredPlusPlusCommand

    def set_admin(self, channel, admin):
        """ Sets a new game admin! """
        if admin in self.state[channel]["admins"]:
            return False

        self.state[channel]["admins"].append(admin)
        return True

    def remove_admin(self, channel, admin):
        """ Removes the admin status of a user """
        if admin not in self.state[channel]["admins"]:
            return False

        self.state[channel]["admins"].remove(admin)
        return True

    def new_game(self, channel, old_winner, winner):
        """ Winners should be the unique Slack User IDs """
        self.state[channel]["old_winner"] = old_winner
        self.state[channel]["winner"] = winner
        self.state[channel]["step"] = "waiting"

    def set_emojirade(self, channel, emojirade):
        """ New emojirade word(s) """
        if self.state[channel]["step"] != "waiting":
            raise InvalidStateException("Expecting {channel}'s state to be 'waiting', it is actually {0}".format(channel, self.state[channel]["step"]))

        self.state[channel]["emojirade"] = emojirade
        self.state[channel]["step"] = "provided"

    def winner_posted(self, channel):
        """ Winner has posted something after receiving the emojirade """
        if self.state[channel]["step"] != "provided":
            raise InvalidStateException("Expecting GameState to be 'provided', it is actually {0}".format(self.state["step"]))

        self.state[channel]["step"] = "guessing"

    def correct_guess(self, channel, winner):
        """ Guesser has guessed the correct emojirade """
        if self.state[channel]["step"] != "guessing":
            raise InvalidStateException("Expecting GameState to be 'guessing', it is actually {0}".format(self.state[channel]["step"]))

        self.state[channel]["old_winner"] = self.state[channel]["winner"]
        self.state[channel]["winner"] = winner
        self.state[channel]["step"] = "waiting"

    @property
    def commands(self):
        return [
            SetAdmin,
            RemoveAdmin,
            NewGame,
            SetEmojirade,
        ]


class GameStateCommand(Command):
    def __init__(self, *args, **kwargs):
        self.gamestate = kwargs.pop("gamestate")
        super().__init__(*args, **kwargs)


class SetAdmin(GameStateCommand):
    pattern = "<@{me}> promote <@([0-9A-Z]+)>"
    description = "Promotes a user to a game admin!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]

        rendered_pattern = self.pattern.format(me=self.slack.bot_id)
        self.args["admin"] = re.match(rendered_pattern, event["text"]).group(1)

    @admin_check
    def execute(self):
        if self.gamestate.set_admin(self.args["channel"], self.args["admin"]):
            yield (None, "<@{user}> has promoted <@{admin}> to a game admin :tada:".format(**self.args))
        else:
            yield (None, "<@{admin}> is already an admin :face_with_rolling_eyes:".format(**self.args))


class RemoveAdmin(GameStateCommand):
    pattern = "<@{me}> demote <@([0-9A-Z]+)>"
    description = "Removes a user from the admins group"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]

        rendered_pattern = self.pattern.format(me=self.slack.bot_id)
        self.args["admin"] = re.match(rendered_pattern, event["text"]).group(1)

    @admin_check
    def execute(self):
        if self.gamestate.remove_admin(self.args["channel"], self.args["admin"]):
            yield (None, "<@{user}> has demoted <@{admin}> to a pleb :cold_sweat:".format(**self.args))
        else:
            yield (None, "<@{admin}> isn't an admin :face_with_rolling_eyes:".format(**self.args))


class NewGame(GameStateCommand):
    pattern = "<@{me}> new game <@([0-9A-Z]+)> <@([0-9A-Z]+)>"
    description = "Initiate a new game by setting the Old Winner and the Winner"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        rendered_pattern = self.pattern.format(me=self.slack.bot_id)

        self.args["user"] = event["user"]
        self.args["channel"] = event["channel"]
        self.args["old_winner"] = re.match(rendered_pattern, event["text"]).group(1)
        self.args["winner"] = re.match(rendered_pattern, event["text"]).group(2)

    @admin_check
    def execute(self):
        if self.args["winner"] == self.args["old_winner"]:
            yield (None, "Sorry, but the old and current winner cannot be the same person (<@{winner}>)...".format(**self.args))
            raise StopIteration

        self.gamestate.new_game(self.args["channel"], self.args["old_winner"], self.args["winner"])
        yield (None, "<@{user}> has set the old winner to <@{old_winner}> and the winner to <@{winner}>".format(**self.args))
        yield (None, "It's now <@{old_winner}>'s turn to provide <@{winner}> with the next 'rade!".format(**self.args))
        yield (self.args["old_winner"], "You'll now need to send me the new 'rade for <@{winner}>".format(**self.args))
        yield (self.args["old_winner"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")


class SetEmojirade(GameStateCommand):
    pattern = "^emojirade (.+)$"
    description = "Sets the current Emojirade to be guessed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["user"] = event["user"]
        self.args["emojirade"] = re.match(self.pattern, event["text"]).group(1)

        # Figure out the channel to use
        # TODO: Decide if we should be getting the user to enter the channel or not?
        for channel in self.gamestate.state.keys():
            if self.gamestate.state[channel]["step"] == "waiting":
                self.args["channel"] = channel

    @only_in_progress
    def execute(self):
        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            yield (None, "Err <@{user}> it's not your turn to provide the new 'rade :sweat:")
            raise StopIteration

        self.gamestate.set_emojirade(self.args["channel"], self.args["emojirade"])

        winner = self.gamestate.state[self.args["channel"]]["winner"]

        # DM the winner with the new rade
        yield (winner, "Hey, <@{user}> made the 'rade `{emojirade}`, good luck!".format(**self.args))

        # Let everyone else know
        yield (self.args["channel"], ":mailbox: <@{user}> has sent the 'rade to <@{winner}>".format(**self.args, winner=winner))

class InferredCorrectGuess(GameStateCommand):
    pattern = None
    description = "Takes the user that send the event as the winner, this is only ever fired internally"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = event["user"]
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])

        old_winner = self.gamestate.state[self.args["channel"]]["old_winner"]

        yield (None, "<@{target_user}>++".format(**self.args))
        yield (old_winner, "You'll now need to send me the new 'rade for <@{target_user}>".format(**self.args))
        yield (old_winner, "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")


class CorrectGuess(GameStateCommand):
    pattern = "<@([0-9A-Z]+)>[\s]*\+\+"
    description = "Indicates the player has correctly guessed!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["target_user"] = re.match(self.pattern, event["text"]).group(1)
        self.args["channel"] = event["channel"]
        self.args["user"] = event["user"]

    @only_in_progress
    def execute(self):
        if self.args["user"] == self.args["target_user"]:
            yield (None, "You're not allowed to award yourself the win >.>")
            raise StopIteration

        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            yield (None, "You're not the old winner, stop awarding other people the win >.>")
            raise StopIteration

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        yield (None, "<@{target_user}>++".format(**self.args))
        yield (self.args["user"], "You'll now need to send me the new 'rade for <@{target_user}>".format(**self.args))
        yield (self.args["user"], "Please reply back in the format `emojirade Point Break` if `Point Break` was the new 'rade")
