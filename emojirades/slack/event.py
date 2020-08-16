class InvalidEvent(Exception):
    pass


class Event:
    def __init__(self, data):
        self.data = data

    def player_id(self):
        if "user" in self.data:
            return self.data["user"]
        elif "bot_id" in self.data:
            return self.data["bot_id"]
        else:
            raise InvalidEvent("Can't find user id or bot id")

