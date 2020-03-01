from plusplusbot.commands.general_commands.help_command import HelpCommand

from plusplusbot.commands.gamestate_commands.set_emojirade_command import SetEmojiradeCommand
from plusplusbot.commands.gamestate_commands.correct_guess_command import CorrectGuessCommand
from plusplusbot.commands.gamestate_commands.remove_admin_command import RemoveAdminCommand
from plusplusbot.commands.gamestate_commands.fixwinner_command import FixWinnerCommand
from plusplusbot.commands.gamestate_commands.set_admin_command import SetAdminCommand
from plusplusbot.commands.gamestate_commands.newgame_command import NewGameCommand
from plusplusbot.commands.gamestate_commands.game_status import GameStatusCommand

from plusplusbot.commands.scorekeeper_commands.leaderboard_command import LeaderboardCommand
from plusplusbot.commands.scorekeeper_commands.minusminus_command import MinusMinusCommand
from plusplusbot.commands.scorekeeper_commands.history_command import HistoryCommand
from plusplusbot.commands.scorekeeper_commands.set_command import SetCommand


class CommandRegistry:
    registered_commands = {
        HelpCommand,

        SetEmojiradeCommand,
        CorrectGuessCommand,
        RemoveAdminCommand,
        FixWinnerCommand,
        SetAdminCommand,
        NewGameCommand,
        GameStatusCommand,

        LeaderboardCommand,
        MinusMinusCommand,
        HistoryCommand,
        SetCommand,
    }

    @classmethod
    def command_patterns(cls, commands=None):
        if commands is None:
            commands = cls.registered_commands

        return {Command.patterns: Command for Command in commands if Command.patterns}

    @classmethod
    def command_names(cls, commands=None):
        if commands is None:
            commands = cls.registered_commands

        return {Command.__name__: Command for Command in commands}
