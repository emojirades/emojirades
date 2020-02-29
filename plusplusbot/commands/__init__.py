from plusplusbot.commands.general_commands import general_commands_list
from plusplusbot.commands.gamestate_commands import gamestate_commands_list
from plusplusbot.commands.scorekeeper_commands import scorekeeper_commands_list


registered_commands = []
registered_commands.extend(general_commands_list)
registered_commands.extend(gamestate_commands_list)
registered_commands.extend(scorekeeper_commands_list)


def prepare_commands(commands=None):
    if commands is None:
        commands = registered_commands

    return {command.patterns: command for command in commands if command.patterns}
