import re
import string
import inflect

from unidecode import unidecode


class ScottFactorExceededException(Exception):
    pass


remove_punctuation = str.maketrans('', '', string.punctuation)
inflect_engine = inflect.engine()

emoji_regex = re.compile(r":[a-zA-Z0-9-_']+:")


def depluralize(text):
    """
    Splits text into tokens
    Singularizes the last token
    Returns the joined together tokens
    """

    # We're assuming this has already been passed through the sanitizer
    if not text.endswith("s"):
        return text

    tokens = text.split(' ')

    singular_noun = inflect_engine.singular_noun(tokens[-1])

    if singular_noun:
        tokens[-1] = singular_noun

    return ' '.join(tokens)


def sanitize_text(text):
    # unidecode will normalize to ASCII
    normalized = unidecode(text)

    # Lowercase the text
    lowered = normalized.lower()

    # Strip whitespace
    stripped = lowered.strip()

    # Remove any random misc chars we deem unnessesary
    scrubbed = stripped.translate(remove_punctuation)

    # De-pluralized
    depluralized = depluralize(scrubbed)

    return depluralized


def match_emojirade(guess, emojirades, scott_factor=2):
    for emojirade in emojirades:
        if len(guess) > (len(emojirade) * scott_factor):
            raise ScottFactorExceededException("Guess exceeded the Scott Factor")

        if re.search(r"\b{0}\b".format(re.escape(emojirade)), guess):
            return True

    return False


def match_emoji(text):
    return bool(emoji_regex.match(text))
