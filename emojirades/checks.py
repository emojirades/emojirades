import re

# 'rade regexes that are banned
banned_emojirades = [
    re.compile(r":[a-zA-Z0-9-_\+]+:"),  # User is not allowed to include emojis
]


def emojirade_is_banned(emojirade):
    return any(i.search(emojirade) for i in banned_emojirades)
