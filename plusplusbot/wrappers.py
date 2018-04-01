
# Convenience wrappers used to assert game state or permissions checks
# These are used directly by a commands execute function

def admin_check(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if self.gamestate.state[channel]["admins"] and self.args["user"] not in self.gamestate.state[channel]["admins"]:
            yield (None, "Sorry <@{user}> but you need to be a game admin to do that :upside_down_face:".format(**self.args))

            admins = ["<@{0}>".format(admin) for admin in self.gamestate.state[channel]["admins"]]
            yield (None, "Game admins currently are: {0}".format(", ".join(admins)))
            raise StopIteration

        for channel, response in command(self):
            yield channel, response

    return wrapped_command

def only_in_progress(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.in_progress(channel):
            yield (None, "Sorry but we need the game to be in progress first! Get someone to kick it off!")
            raise StopIteration

        for channel, response in command(self):
            yield channel, response

    return wrapped_command

def only_actively_guessing(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.actively_guessing(channel):
            yield (None, "Sorry but we need to be actively guessing! Get the winner to start posting the next 'rade!")
            raise StopIteration

        for channel, response in command(self):
            yield channel, response

    return wrapped_command
