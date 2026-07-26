from emojirades.commands import BaseCommand
from emojirades.commands.gamestate_commands.correct_guess_command import CorrectGuessCommand
from emojirades.commands.gamestate_commands.fixwinner_command import FixWinnerCommand
from emojirades.commands.gamestate_commands.game_status import GameStatusCommand
from emojirades.commands.gamestate_commands.inferred_correct_guess_command import (
    InferredCorrectGuessCommand,
)
from emojirades.commands.gamestate_commands.newgame_command import NewGameCommand
from emojirades.commands.gamestate_commands.remove_admin_command import RemoveAdminCommand
from emojirades.commands.gamestate_commands.set_admin_command import SetAdminCommand
from emojirades.commands.gamestate_commands.set_emojirade_command import SetEmojiradeCommand
from emojirades.commands.general_commands.help_command import HelpCommand
from emojirades.commands.registry import CommandRegistry
from emojirades.commands.scorekeeper_commands.history_command import HistoryCommand
from emojirades.commands.scorekeeper_commands.minusminus_command import MinusMinusCommand
from emojirades.commands.scorekeeper_commands.scoreboard_command import ScoreboardCommand
from emojirades.commands.scorekeeper_commands.set_command import SetCommand


class TestCommandRegistry:
    def test_auto_registration_populates_registered_commands(self):
        expected_commands = {
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

        registered_set = set(BaseCommand.registered_commands)
        assert expected_commands.issubset(registered_set)

    def test_registry_references_base_command_registered_commands(self):
        assert CommandRegistry.registered_commands == BaseCommand.registered_commands

    def test_inferred_correct_guess_command_not_registered(self):
        assert InferredCorrectGuessCommand not in BaseCommand.registered_commands

    def test_command_patterns_and_names(self):
        patterns = CommandRegistry.command_patterns()
        assert len(patterns) >= 12

        names = CommandRegistry.command_names()
        assert "HelpCommand" in names
        assert names["HelpCommand"] == HelpCommand
        assert "ScoreboardCommand" in names

    def test_dynamic_subclass_registration(self):
        initial_count = len(BaseCommand.registered_commands)

        class DummyCustomCommand(BaseCommand):
            patterns = (r"dummy_pattern",)

        assert DummyCustomCommand in BaseCommand.registered_commands
        assert len(BaseCommand.registered_commands) == initial_count + 1
        assert "DummyCustomCommand" in CommandRegistry.command_names()
