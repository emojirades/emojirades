import logging
import time
import os
import traceback

from emojirades.handlers import get_workspace_directory_handler
from emojirades.commands.registry import CommandRegistry
from emojirades.slack.slack_client import SlackClient
from emojirades.scorekeeper import ScoreKeeper
from emojirades.commands import BaseCommand
from emojirades.gamestate import GameState
from emojirades.slack.event import Event


class EmojiradesBot(object):
    DEFAULT_WORKSPACE = "_default"

    def __init__(self):
        self.logger = logging.getLogger("Emojirades.Bot")

        self.workspaces = {}
        self.onboarding_queue = None

        self.command_registry = CommandRegistry.command_patterns()

    def configure_workspace(self, score_file, state_file, auth_file, workspace_id=None):
        if workspace_id is None:
            workspace_id = EmojiradesBot.DEFAULT_WORKSPACE

        self.workspaces[workspace_id] = {
            "scorekeeper": ScoreKeeper(score_file),
            "gamestate": GameState(state_file),
            "slack": SlackClient(auth_file, self.logger),
        }

    def configure_workspaces(self, workspaces_dir, workspace_ids, onboarding_queue):
        WorkspaceHandler = get_workspace_directory_handler(workspaces_dir)
        handler = WorkspaceHandler(workspaces_dir)

        for workspace in handler.workspaces():
            self.configure_workspace(**workspace)

        self.onboarding_queue = onboarding_queue

    def match_event(self, event: Event, workspace: dict) -> BaseCommand:
        """
        If the event is valid and matches a command, yield the instantiated command
        :param event: the event object
        :param workspace: Workspace object containing state
        :return Command: The matched command to be executed
        """
        self.logger.debug(f"Handling event: {event.data}")

        for GameCommand in workspace["gamestate"].infer_commands(event):
            yield GameCommand(event, workspace)

        for Command in self.command_registry.values():
            if Command.match(event.text, me=workspace["slack"].bot_id):
                yield Command(event, workspace)

    def decode_channel(self, channel, workspace):
        """
        Figures out the channel destination
        """
        if channel.startswith("C"):
            # Plain old channel, just return it
            return channel
        elif channel.startswith("D"):
            # Direct message channel, just return it
            return channel
        elif channel.startswith("U"):
            # Channel is a User ID, which means the real channel is the DM with that user
            dm_id = workspace["slack"].find_im(channel)

            if dm_id is None:
                raise RuntimeError(
                    f"Unable to find direct message channel for '{channel}'"
                )

            return dm_id
        else:
            raise NotImplementedError(f"Returned channel '{channel}' wasn't decoded")

    def handle_event(self, **payload):
        try:
            self._handle_event(**payload)
        except Exception as e:
            if logging.root.level == logging.DEBUG:
                traceback.print_exc()
            raise e

    def _handle_event(self, **payload):
        if "team" in payload["data"]:
            workspace_id = payload["data"]["team"]
        elif "team" in payload["data"]["message"]:
            workspace_id = payload["data"]["message"]["team"]
        else:
            raise RuntimeError(f"Unable to run Workspace ID in message event")

        if workspace_id not in self.workspaces:
            workspace_id = EmojiradesBot.DEFAULT_WORKSPACE

        workspace = self.workspaces[workspace_id]

        event = Event(payload["data"], workspace["slack"])
        webclient = payload["web_client"]
        workspace["slack"].set_webclient(webclient)

        if not event.valid():
            self.logger.debug("Skipping event due to being invalid")
            return

        for command in self.match_event(event, workspace):
            self.logger.debug(f"Matched {command} for event {event.data}")

            for channel, response in command.execute():
                self.logger.debug("------------------------")

                self.logger.debug(
                    f"Command {command} executed with response: {(channel, response)}"
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
