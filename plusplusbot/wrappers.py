# Convenience wrappers used to assert game state or permissions checks
# These are used directly by a commands execute function


def admin_check(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if self.gamestate.state[channel]["admins"] and self.args["user"] not in self.gamestate.state[channel]["admins"]:
            yield (None, "Sorry <@{user}> but you need to be a game admin to do that :upside_down_face:".format(**self.args))

            admins = ["<@{0}>".format(admin) for admin in self.gamestate.state[channel]["admins"]]
            yield (None, "Game admins currently are: {0}".format(", ".join(admins)))
            return

        yield from command(self)

    return wrapped_command


def admin_or_old_winner_check(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        is_old_winner = False
        is_admin = False

        if self.args["user"] == self.gamestate.state[channel]["old_winner"]:
            is_old_winner = True

        if self.gamestate.state[channel]["admins"] and self.args["user"] in self.gamestate.state[channel]["admins"]:
            is_admin = True

        if not is_old_winner and not is_admin:
            yield (None, "Sorry <@{user}> but you need to be the old winner (or a game admin) to do that :upside_down_face:".format(**self.args))

            admins = ["<@{0}>".format(admin) for admin in self.gamestate.state[channel]["admins"]]
            yield (None, "Game admins currently are: {0}".format(", ".join(admins)))
            return

        yield from command(self)

    return wrapped_command


def only_in_progress(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.in_progress(channel):
            yield (None, "Sorry, but we need the game to be in progress first! Get someone to kick it off!")
            return

        yield from command(self)

    return wrapped_command


def only_not_in_progress(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.not_in_progress(channel):
            yield (None, "Sorry, but the game cannot be in progress! Wait for the round to finish or manually fix it!")
            return

        yield from command(self)

    return wrapped_command


def only_guessing(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.guessing(channel):
            yield (None, "Sorry, but we need to be guessing! Get the winner to start posting the next 'rade!")
            return

        yield from command(self)

    return wrapped_command


def only_as_direct_message(command):
    def wrapped_command(self):
        # We need to check the 'original_channel'
        # As the 'channel' is overridden by prepare_args
        channel = self.args["original_channel"]

        if not channel.startswith("D"):
            yield (self.args["user"], "Sorry, but this command can only be sent as a direct message!")
            return

        yield from command(self)

    return wrapped_command
