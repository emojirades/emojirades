from slackclient import SlackClient as SC


class SlackClient(object):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.sc = SC(config)
        self.ready = False
        self.last_ts = float(0)

        self.bot_id = self.sc.api_call("auth.test")["user_id"]
        self.bot_name = self.user_info(self.bot_id)["real_name"]

        if self.sc.rtm_connect():
            self.ready = True

    def user_info(self, user_id):
        return self.sc.api_call("users.info", user=user_id)["user"]

    def is_bot(self, user_id):
        return self.user_info(user_id)["is_bot"] or userid == "USLACKBOT"

    def is_admin(self, user_id):
        return self.user_info(user_id)["is_admin"]

    def find_im(self, user_id):
        # Find an existing IM (direct message) ID
        response = self.sc.api_call("im.open", user=user_id)

        if response["ok"]:
            return response["channel"]["id"]

        # Attemp to locate an existing IM
        for im in self.sc.api_call("im.list")["ims"]:
            if im["user"] == userid:
                return im["id"]

        return None
