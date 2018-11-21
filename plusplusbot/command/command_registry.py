from plusplusbot.command.general_commands.help_command import HelpCommand

from plusplusbot.command.gamestate_commands.game_status import GameStatus
from plusplusbot.command.gamestate_commands.newgame_command import NewGame
from plusplusbot.command.gamestate_commands.set_admin_command import SetAdmin
from plusplusbot.command.gamestate_commands.remove_admin_command import RemoveAdmin
from plusplusbot.command.gamestate_commands.correct_guess_command import CorrectGuess
from plusplusbot.command.gamestate_commands.set_emojirade_command import SetEmojirade
from plusplusbot.command.gamestate_commands.fixwinner_command import FixWinner

from plusplusbot.command.scorekeeper_commands.set_command import SetCommand
from plusplusbot.command.scorekeeper_commands.history_command import HistoryCommand
from plusplusbot.command.scorekeeper_commands.minusminus_command import MinusMinusCommand
from plusplusbot.command.scorekeeper_commands.leaderboard_command import LeaderboardCommand


class CommandRegistry:
    registered_commands = [
        HelpCommand,
        MinusMinusCommand,
        LeaderboardCommand,
        SetCommand,
        HistoryCommand,
        CorrectGuess,
        NewGame,
        RemoveAdmin,
        SetAdmin,
        SetEmojirade,
        GameStatus,
        FixWinner,
    ]

    @classmethod
    def prepare_commands(cls, commands=None):
        if commands is None:
            commands = cls.registered_commands

        return {command.patterns: command for command in commands if command.patterns}
