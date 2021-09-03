import traceback
import logging

from slack_sdk.rtm_v2 import RTMClient

from emojirades.persistence import (
    get_session,
    get_engine,
    get_workspace_handler,
    migrate,
    populate,
)
from emojirades.commands.registry import CommandRegistry
from emojirades.slack.slack_client import SlackClient
from emojirades.scorekeeper import Scorekeeper
from emojirades.commands import BaseCommand
from emojirades.gamestate import Gamestate
from emojirades.slack.event import Event

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker


command_registry = CommandRegistry.command_patterns()


class EmojiradesBot:
    def __init__(self):
        self.logger = logging.getLogger("Emojirades.Bot")

        self.slacks = []
        self.onboarding_queue = None

    @staticmethod
    def init_db(db_uri):
        migrate(db_uri)

    @staticmethod
    def populate_db(db_uri, table, data_filename):
        populate(db_uri, table, data_filename)

    def configure_workspace(
        self,
        db_uri,
        auth_uri,
        workspace_id=None,
        extra_slack_kwargs=None,
        session_factory=None,
    ):
        slack = SlackClient(auth_uri, extra_slack_kwargs=extra_slack_kwargs)
        self.slacks.append(slack)

        if session_factory is None:
            engine = create_engine(db_uri, future=True)
            session_factory = scoped_session(sessionmaker(bind=engine))

        def handle_event(client: RTMClient, event: dict):
            session = session_factory()

            if "team" in event:
                team_id = event["team"]
            elif "team" in event.get("message", {}):
                team_id = event["message"]["team"]
            else:
                raise RuntimeError("Unable to run Workspace ID in message event")

            event = Event(event, client)

            if not event.valid():
                client.logger.debug("Skipping event due to being invalid")
                return

            workspace = {
                "scorekeeper": Scorekeeper(session, team_id),
                "gamestate": Gamestate(session, team_id),
                "slack": SlackClient(None, existing_client=client),
            }

            client.logger.debug("Handling event: %s", event.data)

            for command in EmojiradesBot.match_event(event, workspace):
                client.logger.debug("Matched %s for event %s", command, event.data)

                for channel, response in command.execute():
                    client.logger.debug("------------------------")
                    client.logger.debug(
                        "Command %s executed with response: %s",
                        command,
                        (channel, response),
                    )

                    if channel is not None:
                        channel = EmojiradesBot.decode_channel(channel, workspace)
                    else:
                        channel = EmojiradesBot.decode_channel(event.channel, workspace)

                    if isinstance(response, str):
                        # Plain strings are assumed as 'chat_postMessage'
                        client.web_client.chat_postMessage(
                            channel=channel, text=response
                        )
                        continue

                    func = getattr(client.web_client, response["func"], None)

                    if func is None:
                        raise RuntimeError(f"Unmapped function '{response['func']}'")

                    args = response.get("args", [])
                    kwargs = response.get("kwargs", {})

                    if kwargs.get("channel") is None:
                        kwargs["channel"] = channel

                    func(*args, **kwargs)

            session.close()

        slack.rtm.on("message")(handle_event)

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

    @staticmethod
    def match_event(event: Event, workspace: dict) -> BaseCommand:
        """
        If the event is valid and matches a command, yield the instantiated command
        :param event: the event object
        :param workspace: Workspace object containing state
        :return Command: The matched command to be executed
        """

        # pylint: disable=invalid-name
        for GameCommand in workspace["gamestate"].infer_commands(event):
            yield GameCommand(event, workspace)

        for Command in command_registry.values():
            if Command.match(event.text, me=workspace["slack"].bot_id):
                if Command.__name__ == "HelpCommand":
                    yield Command(event, workspace, commands=command_registry)
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

    def listen_for_commands(self, blocking=True):
        self.logger.info("Starting Slack monitor(s)")

        for slack in self.slacks:
            slack.start(blocking)
