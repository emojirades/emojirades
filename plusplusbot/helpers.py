import re

from unidecode import unidecode


class ScottFactorExceededException(Exception):
    pass


def sanitize_emojirade(text):
    # Lowercase the text
    lowered = text.lower()

    # Strip whitespace
    stripped = lowered.strip()

    # Remove any random misc chars we deem unnessesary
    scrubbed = re.sub("['\"-_+=]", "", stripped)

    # unidecode will normalize to ASCII
    normalized = unidecode(scrubbed)

    return normalized


def match_emojirade(guess, emojirades, scott_factor=2):
    guess = re.escape(guess)

    for emojirade in emojirades:
        if len(guess) > (len(emojirade) * scott_factor):
            raise ScottFactorExceededException("Guess exceeded the Scott Factor")

        if re.search(r"\b{0}\b".format(re.escape(emojirade)), guess):
            return True

    return False
