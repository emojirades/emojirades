from plusplusbot.commands.command import Command

from correct_guess_command import CorrectGuess
from fixwinner_command import FixWinner
from game_status import GameStatus
from inferred_correct_guess_command import InferredCorrectGuess
from newgame_command import NewGame
from remove_admin_command import RemoveAdmin
from set_admin_command import SetAdmin
from set_emojirade_command import SetEmojirade


class GameStateCommand(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    def execute(self):
        yield from super().execute()


gamestate_commands_list = [
    CorrectGuess,
    FixWinner,
    GameStatus,
    InferredCorrectGuess,
    NewGame,
    RemoveAdmin,
    SetAdmin,
    SetEmojirade,
]
