import logging
import time
import os

from emojirades.commands.registry import CommandRegistry
from emojirades.slack import SlackClient, slack
from emojirades.scorekeeper import ScoreKeeper
from emojirades.gamestate import GameState


module_logger = logging.getLogger("EmojiradesBot.bot")


class EmojiradesBot(object):
    def __init__(self, scorefile, statefile):
        self.logger = logging.getLogger("EmojiradesBot.bot.Bot")

        self.scorekeeper = ScoreKeeper(scorefile)
        self.gamestate = GameState(statefile)

        slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", None)

        if not slack_bot_token:
            raise RuntimeError("Missing SLACK_BOT_TOKEN from environment vars")

        self.slack = SlackClient(slack_bot_token, self.logger)
        self.logger.debug("Initialised application instance")

    def match_event(self, event, commands):
        """
        If the event is valid and matches a command, yield the instantiated command
        :param event:
        :return Command:
        """
        self.logger.debug(f"Handling event: {event}")

        for GameCommand in self.gamestate.infer_commands(event):
            yield GameCommand(event, self.slack, self.scorekeeper, self.gamestate)

        for Command in commands.values():
            if Command.match(event["text"], me=self.slack.bot_id):
                yield Command(event, self.slack, self.scorekeeper, self.gamestate)

    def valid_event(self, event):
        """
        Assert the lowest level of things we need to see in an event to be parseable
        :param event:
        :return bool:
        """
        expected_keys = {
            "text",
            "channel",
            "user",
        }

        if not event:
            return False
        elif not expected_keys.issubset(event.keys()):
            return False

        return True

    def decode_channel(self, channel):
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
            dm_id = self.slack.find_im(channel)

            if dm_id is None:
                raise RuntimeError(
                    f"Unable to find direct message channel for '{channel}'"
                )

            return dm_id
        else:
            raise NotImplementedError(f"Returned channel '{channel}' wasn't decoded")

    def handle_event(self, **payload):
        commands = CommandRegistry.command_patterns()

        event = payload["data"]
        webclient = payload["web_client"]
        self.slack.set_webclient(webclient)

        if not self.valid_event(event):
            self.logger.debug("Skipping event due to being invalid")
            return

        for command in self.match_event(event, commands):
            self.logger.debug(f"Matched {command} for event {event}")

            for channel, response in command.execute():
                self.logger.debug(
                    f"Command {command} executed with response: {(channel, response)}"
                )
                if channel is not None:
                    channel = self.decode_channel(channel)
                else:
                    channel = self.decode_channel(event["channel"])

                webclient.chat_postMessage(channel=channel, text=response)

    def listen_for_commands(self):
        self.logger.info("Starting Slack monitor")
        self.slack.start()
