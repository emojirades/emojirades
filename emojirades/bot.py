import traceback
import logging

from emojirades.persistence import get_session, get_workspace_handler, migrate, populate
from emojirades.commands.registry import CommandRegistry
from emojirades.slack.slack_client import SlackClient
from emojirades.scorekeeper import Scorekeeper
from emojirades.commands import BaseCommand
from emojirades.gamestate import Gamestate
from emojirades.slack.event import Event


class EmojiradesBot:
    def __init__(self):
        self.logger = logging.getLogger("Emojirades.Bot")

        self.workspaces = {}
        self.onboarding_queue = None

        self.command_registry = CommandRegistry.command_patterns()

    @staticmethod
    def init_db(db_uri):
        migrate(db_uri)

    @staticmethod
    def populate_db(db_uri, table, data_filename):
        populate(db_uri, table, data_filename)

    def configure_workspace(self, db_uri, auth_uri, workspace_id=None):
        slack = SlackClient(auth_uri)

        if workspace_id is None:
            workspace_id = slack.workspace_id

        session = get_session(db_uri)

        self.workspaces[workspace_id] = {
            "scorekeeper": Scorekeeper(session, workspace_id),
            "gamestate": Gamestate(session, workspace_id),
            "slack": slack,
        }

    def configure_workspaces(
        self, workspaces_uri, workspace_ids, onboarding_queue, db_uri=None
    ):
        handler = get_workspace_handler(workspaces_uri)

        for workspace in handler.workspaces():
            if workspace_ids and workspace["workspace_id"] not in workspace_ids:
                continue

            if db_uri is not None:
                workspace["db_uri"] = db_uri

            self.configure_workspace(**workspace)

        self.onboarding_queue = onboarding_queue

    def match_event(self, event: Event, workspace: dict) -> BaseCommand:
        """
        If the event is valid and matches a command, yield the instantiated command
        :param event: the event object
        :param workspace: Workspace object containing state
        :return Command: The matched command to be executed
        """
        self.logger.debug("Handling event: %s", event.data)

        # pylint: disable=invalid-name
        for GameCommand in workspace["gamestate"].infer_commands(event):
            yield GameCommand(event, workspace)

        for Command in self.command_registry.values():
            if Command.match(event.text, me=workspace["slack"].bot_id):
                if Command.__name__ == "HelpCommand":
                    yield Command(event, workspace, commands=self.command_registry)
                else:
                    yield Command(event, workspace)
        # pylint: enable=invalid-name

    @staticmethod
    def decode_channel(channel: str, workspace: dict):
        """
        Figures out the channel destination
        """
        if channel.startswith("C"):
            # Plain old channel, just return it
            return channel

        if channel.startswith("D"):
            # Direct message channel, just return it
            return channel

        if channel.startswith("U"):
            # Channel is a User ID, which means the real channel is the DM with that user
            dm_id = workspace["slack"].find_im(channel)

            if dm_id is None:
                raise RuntimeError(
                    f"Unable to find direct message channel for '{channel}'"
                )

            return dm_id

        raise NotImplementedError(f"Returned channel '{channel}' wasn't decoded")

    def handle_event(self, **payload):
        try:
            self._handle_event(**payload)
        except Exception as exception:
            if logging.root.level == logging.DEBUG:
                traceback.print_exc()
            raise exception

    def _handle_event(self, **payload):
        if "team" in payload["data"]:
            workspace_id = payload["data"]["team"]
        elif "team" in payload["data"].get("message", {}):
            workspace_id = payload["data"]["message"]["team"]
        else:
            raise RuntimeError("Unable to run Workspace ID in message event")

        if workspace_id not in self.workspaces:
            raise RuntimeError(f"Unknown workspace_id {workspace_id}?")

        workspace = self.workspaces[workspace_id]

        event = Event(payload["data"], workspace["slack"])
        webclient = payload["web_client"]
        workspace["slack"].set_webclient(webclient)

        if not event.valid():
            self.logger.debug("Skipping event due to being invalid")
            return

        for command in self.match_event(event, workspace):
            self.logger.debug("Matched %s for event %s", command, event.data)

            for channel, response in command.execute():
                self.logger.debug("------------------------")
                self.logger.debug(
                    "Command %s executed with response: %s",
                    command,
                    (channel, response),
                )

                if channel is not None:
                    channel = self.decode_channel(channel, workspace)
                else:
                    channel = self.decode_channel(event.channel, workspace)

                if isinstance(response, str):
                    # Plain strings are assumed as 'chat_postMessage'
                    webclient.chat_postMessage(channel=channel, text=response)
                    continue

                func = getattr(webclient, response["func"], None)

                if func is None:
                    raise RuntimeError(f"Unmapped function '{response['func']}'")

                args = response.get("args", [])
                kwargs = response.get("kwargs", {})

                if kwargs.get("channel") is None:
                    kwargs["channel"] = channel

                func(*args, **kwargs)

    def listen_for_commands(self):
        self.logger.info("Starting Slack monitor(s)")

        for workspace in self.workspaces.values():
            workspace["slack"].start()
