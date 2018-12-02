from plusplusbot.command.commands import Command


class GameStateCommand(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_args(self, event):
        super().prepare_args(event)

    def execute(self):
        yield from super().execute()
