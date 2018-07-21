import re


# 'rade regexes that are banned
banned_emojirades = [
    re.compile(":[a-zA-Z-_]+:"),  # User is now allowed to include emojis
]

def emojirade_is_banned(emojirade):
    return any(i.match(emojirade) for i in banned_emojirades)
