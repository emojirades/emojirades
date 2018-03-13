import re
import json
import logging

from collections import defaultdict

from plusplusbot.command.commands import Command
from plusplusbot.handlers import get_configuration_handler
from plusplusbot.command.gamestate_commands.inferred_correct_guess_command import InferredCorrectGuess
from plusplusbot.command.scorekeeper_commands.inferred_plusplus_command import InferredPlusPlusCommand

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
        return self.state[channel]["step"] not in ["new_game"]

    def infer_commands(self, event):
        """ Keeps tabs on the conversation and updates gamestate if required """
        channel = event["channel"]
        user = event["user"]

        # Check to see if the winner is posting emoji's
        if self.state[channel]["step"] == "provided":
            if user == self.state[channel]["winner"]:
                if ':' in event["text"]:  # ':' means they've posted an emoji :thinking_face:
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
        self.save()

        return True

    def remove_admin(self, channel, admin):
        """ Removes the admin status of a user """
        if admin not in self.state[channel]["admins"]:
            return False

        self.state[channel]["admins"].remove(admin)
        self.save()

        return True

    def new_game(self, channel, old_winner, winner):
        """ Winners should be the unique Slack User IDs """
        self.state[channel]["old_winner"] = old_winner
        self.state[channel]["winner"] = winner
        self.state[channel]["step"] = "waiting"
        self.save()

    def set_emojirade(self, channel, emojirade):
        """ New emojirade word(s) """
        if self.state[channel]["step"] != "waiting":
            raise self.InvalidStateException("Expecting {0}'s state to be 'waiting', it is actually {1}".format(channel, self.state[channel]["step"]))

        self.state[channel]["emojirade"] = emojirade
        self.state[channel]["step"] = "provided"
        self.save()

    def winner_posted(self, channel):
        """ Winner has posted something after receiving the emojirade """
        if self.state[channel]["step"] != "provided":
            raise self.InvalidStateException("Expecting {0}'s state to be 'provided', it is actually {1}".format(channel, self.state["step"]))

        self.state[channel]["step"] = "guessing"
        self.save()

    def correct_guess(self, channel, winner):
        """ Guesser has guessed the correct emojirade """
        if self.state[channel]["step"] != "guessing":
            raise self.InvalidStateException("Expecting {0}'s state to be 'guessing', it is actually {1}".format(channel, self.state[channel]["step"]))

        self.state[channel]["old_winner"] = self.state[channel]["winner"]
        self.state[channel]["winner"] = winner
        self.state[channel]["step"] = "waiting"
        self.save()

    def game_status(self, channel):
        """ Returns a string-ified version of the game state """
        status = []

        for k, v in self.state[channel].items():
            if k == "old_winner" or k == "winner":
                v = "<@{0}>".format(v)
            elif k == "admins":
                v = ", ".join(["<@{0}>".format(i) for i in v])
            elif k == "emojirade":
                v = "********"
            else:
                v = str(v)

            status.append((k, v))

        return "\n".join("{0}: {1}".format(k, v) for k, v in status)

    def save(self):
        self.config.save(self.state)
