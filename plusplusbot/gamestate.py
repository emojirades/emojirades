
from plusplusbot.handlers import get_configuration_handler
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
        def __init__(self, filename):
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
        bootstrap : The game has no previous winner, manual intervention required
        waiting   : The old winner has not provided the winner with the new emojirade
        provided  : The winner has not posted anything since having recieved the emojirade
        guessing  : The winner has posted since having recieved the emojirade
        guessed   : The guesser has correctly guessed the emojirade

    Step transitions:
        set_winners   : bootstrap -> waiting
        set_emojirade : waiting -> provided
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
            self.state.update(self.config.load())
            self.logger.info("Loaded game state from {0}".format(filename))

    @property
    def in_progress(self, channel):
        return self.state[channel]["step"] != "bootstrap"

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
                    return CorrectGuess

    def set_admin(self, channel, admin):
        """ Sets a new game admin! """
        if admin in self.state[channel]["admins"]:
            return False

        self.state[channel]["admins"].append(admin)
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
        self.state[channel]["step"] = "guessed"

    @property
    def commands(self):
        return [
            SetAdmin,
            NewGame,
            SetEmojirade,
        ]


class GameStateCommand(Command):
    def __init__(self, *args, **kwargs):
        kwargs["handles"] = ["gamestate"]
        super().__init__(*args, **kwargs)


def admin_check(f):
    def wrapped_command(self):
        if self.state[channel]["admins"] and self.args["user"] not in self.state[channel]["admins"]:
            yield (None, "Sorry {user} but you need to be a game admin to do that :upside_down_face:".format(**self.args))
            return (None, "Game admins currently are: {0}".format("<@{0}>".join(self.state[channel]["admins"])))

        f()

    return wrapped_command


class SetAdmin(GameStateCommand):
    pattern = "<@{me}> promote <@([0-9A-Z]+)>"
    description = "Promotes a user to a game admin!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["channel"] = event["channel"]
        self.args["admin"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    @admin_check
    def execute(self):
        if self.gamestate.set_admin(self.args["channel"], self.args["admin"]):
            return (None, "{user} has promoted {admin} to a game admin :tada:".format(**self.args))
        else:
            return (None, "{admin} is already an admin :face_with_rolling_eyes:".format(**self.args))


class NewGame(GameStateCommand):
    pattern = "<@{me}> new game <@([0-9A-Z]+)> <@([0-9A-Z]+)>"
    description = "Initiate a new game by setting the Old Winner and the Winner"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["channel"] = event["channel"]
        self.args["old_winner"] = re.match(self.pattern, event["text"])[1]
        self.args["winner"] = re.match(self.pattern, event["text"])[2]
        self.args["user"] = event["user"]

    @admin_check
    def execute(self):
        if self.args["winner"] == self.args["old_winner"]:
            return (None, "Sorry, but the old and current winner cannot be the same person ({winner})...".format(**self.args))

        self.gamestate.new_game(self.args["channel"], self.args["old_winner"], self.args["winner"])
        yield (None, "{user} has set the old winner to {old_winner} and the winner to {winner}".format(**self.args))
        return (None, "It's now {old_winner}'s turn to provide {winner} with the next 'rade!".format(**self.args))


class SetEmojirade(GameStateCommand):
    pattern = "^emojirade (.+)$"
    description = "Sets the current Emojirade to be guessed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["channel"] = event["channel"]
        self.args["emojirade"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):
        if self.args["user"] != self.gamestate.state[self.args["channel"]]["old_winner"]:
            return (None, "Err {user} it's not your turn to provide the new 'rade :sweat:")

        self.gamestate.set_emojirade(self.args["channel"], self.args["emojirade"])

        winner = self.gamestate.state[self.args["channel"]]["winner"]
        game_channel = self.gamestate.state[self.args["channel"]]["channel"]

        # DM the winner with the new rade
        yield (winner, "Hey, {user} just set the new 'rade to '{emojirade}'".format(**self.args))

        # Let everyone else know
        return (game_channel, ":mailbox: {user} has sent the 'rade to {winner}".format(**self.args, winner=winner))


class CorrectGuess(GameStateCommand):
    pattern = "<@([0-9A-Z]+)>[\s]*\+\+"
    description = "Indicates the player has correctly guessed!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        self.args["channel"] = event["channel"]
        self.args["target_user"] = re.match(self.pattern, event["text"])[1]
        self.args["user"] = event["user"]

    def execute(self):
        if self.args["user"] == self.args["target_user"]:
            return (None, "You're not allowed to award yourself the win >.>")

        if self.args["user"] != self.gamestate.state[channel]["old_winner"]:
            return (None, "You're not the old winner, stop awarding other people the win >.>")

        self.gamestate.correct_guess(self.args["channel"], self.args["target_user"])
        yield (None, "Congratz :tada: {target_user}".format(**self.args))
        yield (self.args["user"], "You'll now need to send me the new 'rade for {target_user}".format(**self.args))
        yield (self.args["user"], "Please reply back in the format 'emojirade Point Break' if 'Point Break' was the new 'rade")
