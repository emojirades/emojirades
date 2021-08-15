# Convenience wrappers used to assert game state or permissions checks
# These are used directly by a commands execute function


def admin_check(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.is_admin(channel, self.args["user"]):
            yield (
                None,
                f"Sorry <@{self.args['user']}> but you need to be "
                "a game admin to do that :upside_down_face:",
            )

            admins = [f"<@{admin}>" for admin in self.gamestate.get_admins(channel)]
            yield (None, f"Game admins currently are: {', '.join(admins)}")
            return

        yield from command(self)

    return wrapped_command


def admin_or_old_winner_check(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        is_old_winner = False
        is_admin = False

        previous_winner, _ = self.gamestate.winners(channel)

        if self.args["user"] == previous_winner:
            is_old_winner = True

        if self.gamestate.is_admin(channel, self.args["user"]):
            is_admin = True

        if not is_old_winner and not is_admin:
            yield (
                None,
                f"Sorry <@{self.args['user']}> but you need to be the old winner "
                "(or a game admin) to do that :upside_down_face:",
            )

            admins = [f"<@{admin}>" for admin in self.gamestate.get_admins(channel)]
            yield (None, f"Game admins currently are: {', '.join(admins)}")
            return

        yield from command(self)

    return wrapped_command


def admin_or_old_winner_set_check(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        is_old_winner = False
        is_admin = False

        previous_winner, _ = self.gamestate.winners(channel)

        if self.args["user"] == previous_winner:
            is_old_winner = True

        if self.gamestate.is_admin(channel, self.args["user"]):
            is_admin = True

        # Game can only be in the 'set' state if the user isn't an admin
        if (not is_admin and is_old_winner) and self.gamestate.guessing(channel):
            yield (
                None,
                f"Sorry <@{self.args['user']}> but the game has already started :snail:",
            )
            return

        if not is_old_winner and not is_admin:
            yield (
                None,
                f"Sorry <@{self.args['user']}> but you need to be the old winner "
                "(or a game admin) to do that :upside_down_face:",
            )

            admins = [f"<@{admin}>" for admin in self.gamestate.get_admins(channel)]
            yield (None, f"Game admins currently are: {', '.join(admins)}")
            return

        yield from command(self)

    return wrapped_command


def only_in_progress(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.in_progress(channel):
            yield (
                None,
                "Sorry, but we need the game to be in progress first! Get someone to kick it off!",
            )
            return

        yield from command(self)

    return wrapped_command


def only_not_in_progress(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.not_in_progress(channel):
            yield (
                None,
                "Sorry, but the game cannot be in progress! "
                "Wait for the round to finish or manually fix it!",
            )
            return

        yield from command(self)

    return wrapped_command


def only_guessing(command):
    def wrapped_command(self):
        channel = self.args["channel"]

        if not self.gamestate.guessing(channel):
            yield (
                None,
                "Sorry, but we need to be guessing! "
                "Get the winner to start posting the next 'rade!",
            )
            return

        yield from command(self)

    return wrapped_command


def only_as_direct_message(command):
    def wrapped_command(self):
        # We need to check the 'original_channel'
        # As the 'channel' is overridden by prepare_args
        channel = self.args["original_channel"]

        if not channel.startswith("D"):
            yield (
                self.args["user"],
                "Sorry, but this command can only be sent as a direct message!",
            )
            return

        yield from command(self)

    return wrapped_command
