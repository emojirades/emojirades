import logging
import time
import json

import boto3

from pythonjsonlogger import jsonlogger
from slack_sdk.rtm_v2 import RTMClient

from emojirades.persistence import (
    get_session_factory,
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


command_registry = CommandRegistry.command_patterns()


def configure_parent_logger(level, name="Emojirades"):
    logger = logging.getLogger(name)
    logger.propagate = False

    field_keys = [
        "asctime",
        "name",
        "levelname",
        "filename",
        "module",
        "threadName",
        "message",
    ]

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(" ".join(f"%({i})s" for i in field_keys))
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


class EmojiradesBot:
    def __init__(self):
        self.logger = logging.getLogger("Emojirades.Bot")

        self.workspaces = {}
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
        extra_slack_kwargs=None,
    ):
        slack = SlackClient(auth_uri, extra_slack_kwargs=extra_slack_kwargs)

        if slack.workspace_id in self.workspaces:
            self.logger.info("Deleting previous workspace: %s", slack.workspace_id)

            self.workspaces[slack.workspace_id].rtm.close()
            time.sleep(1)
            del self.workspaces[slack.workspace_id]

        self.workspaces[slack.workspace_id] = slack

        session_factory = get_session_factory(db_uri)
        logger = self.logger

        def handle_event(client: RTMClient, event: dict):
            event = Event(event, client)

            if not event.valid():
                client.logger.debug("Skipping event due to being invalid")
                return

            # Get a per-thread session
            session = session_factory()

            workspace = {
                "scorekeeper": Scorekeeper(session, client.workspace_id),
                "gamestate": Gamestate(session, client.workspace_id),
                "slack": SlackClient(None, existing_client=client),
            }

            logger.debug("Handling event: %s", event.data)

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

        return slack

    def configure_workspaces(
        self, workspaces_uri, workspace_ids, onboarding_queue, db_uri=None
    ):
        handler = get_workspace_handler(workspaces_uri)

        for workspace in handler.workspaces():
            if workspace_ids and workspace["workspace_id"] not in workspace_ids:
                continue

            if db_uri is not None:
                workspace["db_uri"] = db_uri

            if "workspace_id" in workspace:
                workspace.pop("workspace_id")

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

        for slack in self.workspaces.values():
            slack.start(blocking=blocking)

    def listen_for_onboarding(self, workspaces_uri, db_uri=None, blocking=True):
        sqs = boto3.client("sqs")

        response = sqs.get_queue_url(QueueName=self.onboarding_queue)
        queue_url = response["QueueUrl"]

        handler = get_workspace_handler(workspaces_uri)

        if blocking:
            oneshot = False
        else:
            oneshot = True

        while not oneshot:
            response = sqs.receive_message(QueueUrl=queue_url)

            for message in response.get("Messages", []):
                try:
                    body = json.loads(message["Body"])
                except json.JSONDecodeError:
                    self.logger.debug(
                        "Onboarding message not JSON: %s", message["Body"]
                    )
                    continue

                if "workspace_id" not in body:
                    self.logger.debug("Unable to parse onboarding payload: %s", body)
                    continue

                self.logger.debug(
                    "Bot received onboarding for %s", body["workspace_id"]
                )

                workspace = handler.workspace(body["workspace_id"])

                if db_uri is not None:
                    workspace["db_uri"] = db_uri

                if "workspace_id" in workspace:
                    workspace.pop("workspace_id")

                slack = self.configure_workspace(**workspace)
                self.workspaces[slack.workspace_id].start(blocking=False)
                self.logger.info("Bot has onboarded workspace %s", slack.workspace_id)

                # Onboarding was successful, clean up the workspace
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message["ReceiptHandle"],
                )
                self.logger.debug("Deleted onboarding request from SQS Queue")

            time.sleep(60)
