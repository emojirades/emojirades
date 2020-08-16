class Event:
    def __init__(self, data):
        self.data = data

    def player_id(self):
        return self.data.get("user", self.data.get("bot_id"))
