import string
import re

from functools import lru_cache

from unidecode import unidecode


class ScottFactorExceededException(Exception):
    pass


remove_punctuation = str.maketrans("", "", string.punctuation)

emoji_regex = re.compile(r":[a-zA-Z0-9-_']+:")


@lru_cache(maxsize=256)
def _get_compiled_rade(emojirades_tuple):
    # Combine all alternatives into a single regex for efficiency
    combined_pattern = "|".join(re.escape(i) for i in emojirades_tuple)
    return re.compile(rf"\b({combined_pattern})\b")


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

    # Use a tuple as cache key since emojirades is a list
    cache_key = tuple(sorted(emojirades))
    pattern = _get_compiled_rade(cache_key)

    return bool(pattern.search(guess))


def match_emoji(text):
    return bool(emoji_regex.search(text))
