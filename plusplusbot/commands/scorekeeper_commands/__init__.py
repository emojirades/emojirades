from plusplusbot.commands.command import Command

from history_command import HistoryCommand
from leaderboard_command import LeaderboardCommand
from minusminus_command import MinusMinusCommand
from set_command import SetCommand


class ScoreKeeperCommand(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    def execute(self):
        yield from super().execute()


scorekeeper_commands_list = [
    HistoryCommand,
    LeaderboardCommand,
    MinusMinusCommand,
    SetCommand,
]
