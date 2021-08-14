from emojirades.commands.general_commands.help_command import HelpCommand

from emojirades.commands.gamestate_commands.set_emojirade_command import (
    SetEmojiradeCommand,
)
from emojirades.commands.gamestate_commands.correct_guess_command import (
    CorrectGuessCommand,
)
from emojirades.commands.gamestate_commands.remove_admin_command import (
    RemoveAdminCommand,
)
from emojirades.commands.gamestate_commands.fixwinner_command import FixWinnerCommand
from emojirades.commands.gamestate_commands.set_admin_command import SetAdminCommand
from emojirades.commands.gamestate_commands.newgame_command import NewGameCommand
from emojirades.commands.gamestate_commands.game_status import GameStatusCommand

from emojirades.commands.scorekeeper_commands.scoreboard_command import (
    ScoreboardCommand,
)
from emojirades.commands.scorekeeper_commands.minusminus_command import (
    MinusMinusCommand,
)
from emojirades.commands.scorekeeper_commands.history_command import HistoryCommand
from emojirades.commands.scorekeeper_commands.set_command import SetCommand


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
        ScoreboardCommand,
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
