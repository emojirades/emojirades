import string
import re

from unidecode import unidecode


class ScottFactorExceededException(Exception):
    pass


remove_punctuation = str.maketrans("", "", string.punctuation)

emoji_regex = re.compile(r":[a-zA-Z0-9-_']+:")


def sanitize_text(text):
    # unidecode will normalize to ASCII
    normalized = unidecode(text)

    # Lowercase the text
    lowered = normalized.lower()

    # Remove any random misc chars we deem unnessesary
    scrubbed = lowered.translate(remove_punctuation)

    # Strip excess whitespace
    stripped = " ".join(scrubbed.split())

    return stripped


def match_emojirade(guess, emojirades, scott_factor=2):
    longest_emojirade = max(len(i) for i in emojirades)

    if len(guess) > (longest_emojirade * scott_factor):
        raise ScottFactorExceededException("Guess exceeded the Scott Factor")

    for emojirade in emojirades:
        if re.search(fr"\b{re.escape(emojirade)}\b", guess):
            return True

    return False


def match_emoji(text):
    return bool(emoji_regex.search(text))
