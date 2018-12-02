import logging
import json
import re

from collections import defaultdict

from plusplusbot.command.gamestate_commands.inferred_correct_guess_command import InferredCorrectGuess
from plusplusbot.handlers import get_configuration_handler
from plusplusbot.helpers import sanitize_emojirade, match_emojirade

from plusplusbot.command.commands import Command
from plusplusbot.helpers import ScottFactorExceededException

module_logger = logging.getLogger("PlusPlusBot.gamestate")


def get_handler(filename):
    class GameStateConfigHandler(get_configuration_handler(filename)):
        """
        Handles CRUD for the Game State configuration file
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def load(self):
            bytes_content = super().load()

            if bytes_content is None or not bytes_content:
                return None

            return json.loads(bytes_content.decode("utf-8"))

        def save(self, state):
            bytes_content = json.dumps(state).encode("utf-8")

            super().save(bytes_content)

    return GameStateConfigHandler(filename)


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

    Step transitions:
        set_winners   : new_game -> waiting
        set_emojirade : waiting  -> provided
        winner_posted : provided -> guessing
        correct_guess : guessing -> waiting
    """

    class InvalidStateException(Exception):
        pass

    def __init__(self, filename=None):
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

        if filename is not None:
            existing_state = self.config.load()

            if existing_state is not None:
                self.state.update(existing_state)
                self.logger.info("Loaded game state from {0}".format(filename))

    def in_progress(self, channel):
        return self.state[channel]["step"] not in ["new_game"]

    def actively_guessing(self, channel):
        return self.state[channel]["step"] == "guessing"

    def infer_commands(self, event):
        """
        Keeps tabs on the conversation and updates gamestate if required
        Not to be called directly, used as another command source from the bot
        """
        channel = str(event["channel"])
        user = str(event["user"])
        text = str(event["text"])
        state = self.state[channel]

        if self.is_admin(channel, user):
            # Double check if we're overriding the channel
            channel_override_match = Command.channel_override_regex.match(text)

            if channel_override_match:
                original_channel = channel
                channel = channel_override_match.groupdict()["channel_override"]

                text = text.replace(channel_override_match.groupdict()["override_cmd"], "")

            # Double check if we're overriding the user
            user_override_match = Command.user_override_regex.match(text)

            if user_override_match:
                original_user = user
                user = user_override_match.groupdict()["user_override"]

                text = text.replace(user_override_match.groupdict()["override_cmd"], "")

        # User the overridden channel if applicable
        state = self.state[channel]

        # Check to see if the winner is posting emoji's
        if state["step"] == "provided" and user == state["winner"] and ':' in text:
            # ':' means they've posted an emoji :thinking_face:
            self.winner_posted(channel)

        # Check to see if the users guess is right!
        elif state["step"] == "guessing" and user not in (state["old_winner"], state["winner"]):
            guess = sanitize_emojirade(text)

            try:
                if match_emojirade(guess, state["emojirade"]):
                    self.logger.debug("emojirades='{0}' guess='{1}' status='correct'".format('|'.join(state["emojirade"]), guess))
                    yield InferredCorrectGuess
                else:
                    self.logger.debug("emojirades='{0}' guess='{1}' status='incorrect'".format('|'.join(state["emojirade"]), guess))
            except ScottFactorExceededException as e:
                self.logger.debug("emojirade='{0}' guess='{1}' status='scott factor exceeded'")

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

    def is_admin(self, channel, user):
        admins = self.state[channel].get("admins", [])

        if not admins:
            # No admins set yet, so everyone is an admin!
            return True

        if user in admins:
            return True

        return False

    def new_game(self, channel, old_winner, winner):
        """ Winners should be the unique Slack User IDs """
        self.state[channel]["old_winner"] = old_winner
        self.state[channel]["winner"] = winner
        self.state[channel]["step"] = "waiting"
        self.state[channel]["emojirade"] = None
        self.save()

    def set_emojirade(self, channel, emojirade):
        """ New emojirade word(s), 'emojirade' is a list of accepted answers """
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
        self.state[channel]["emojirade"] = None
        self.save()

    def game_status(self, channel):
        """ Returns the game state """
        return self.state[channel]

    def fixwinner(self, channel, winner):
        """ Updates the current winner with the newly provided winner and handles score updates """
        loser = self.state[channel]["winner"]
        self.state[channel]["winner"] = winner
        self.save()

        return loser, winner

    def save(self):
        self.config.save(self.state)
