import logging
import os
import time

from plusplusbot.command.command_registry import CommandRegistry
from plusplusbot.scorekeeper import ScoreKeeper
from plusplusbot.gamestate import GameState
from plusplusbot.slack import SlackClient

module_logger = logging.getLogger("PlusPlusBot.bot")


class PlusPlusBot(object):
    def __init__(self, scorefile, statefile):
        self.logger = logging.getLogger("PlusPlusBot.bot.Bot")

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

        self.logger.debug("Handling event: {}".format(event))

        if "text" not in event:
            self.logger.debug("Event match ignored due to no 'text' field")
            raise StopIteration

        for pattern, (Command, description) in commands.items():
            if Command.match(event["text"], me=self.slack.bot_id):
                yield Command(self.slack, event, scorekeeper=self.scorekeeper, gamestate=self.gamestate)

    def decode_channel(self, channel):
        """
        Figures out the channel destination
        """
        if channel.startswith("C"):
            # Plain old channel, just return it
            return channel
        elif channel.startswith("U"):
            # Channel is a User ID, which means the real channel is the IM with that user
            return self.slack.find_im(channel)
        else:
            raise NotImplementedError("Returned channel '{0}' wasn't decoded".format(channel))

    def listen_for_actions(self):
        commands = CommandRegistry.prepare_commands()

        if not self.slack.ready:
            raise RuntimeError("is_ready has not been called/returned false")

        if not self.slack.sc.rtm_connect():
            raise RuntimeError("Failed to connect to the Slack API")

        self.logger.info("Slack is connected and listening for commands")

        while True:
            for event in self.slack.sc.rtm_read():
                if not event or "text" not in event or "channel" not in event:
                    self.logger.debug("Skipping event due to being invalid")
                    continue

                for GameCommand in self.gamestate.infer_commands(event):
                    action = GameCommand(self.slack, event, scorekeeper=self.scorekeeper, gamestate=self.gamestate)
                    self.logger.debug("Matched {0} for event {1}".format(action, event))

                    for channel, response in action.execute():
                        if channel is not None:
                            channel = self.decode_channel(channel)
                        else:
                            channel = event["channel"]

                        self.slack.sc.rtm_send_message(channel, response)

                for action in self.match_event(event, commands):
                    self.logger.debug("Matched {0} for event {1}".format(action, event))
                    for channel, response in action.execute():
                        if channel is not None:
                            channel = self.decode_channel(channel)
                        else:
                            channel = event["channel"]

                        self.slack.sc.rtm_send_message(channel, response)

            time.sleep(1)
