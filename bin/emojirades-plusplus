#!/usr/bin/env python3

from plusplusbot.bot import PlusPlusBot

import argparse
import logging
import sys


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="count", dest="v", default=0, help="Logging level")
    parser.add_argument("--log-file", default=sys.stderr, help="File we will log to")
    parser.add_argument("--score-file", help="CSV file we use to persist scores", required=True)

    args = parser.parse_args()

    if args.v >= 2:
        log_level = logging.DEBUG
    elif args.v >= 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level)
    logger = logging.getLogger("PlusPlusBot")
    logger.debug("Initialised application")

    bot = PlusPlusBot(args.score_file)
    logger.info("Listening for commands")
    bot.listen_for_actions()
