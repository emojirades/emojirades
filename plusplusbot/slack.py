from slackclient import SlackClient as SC


class SlackClient(object):
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.sc = SC(config)

        epp_bot = self.sc.api_call("auth.test")
        self.bot_id = epp_bot["user_id"]
        # self.channel_id = config.get("channel_id", None)
        # self.channel_id = None

        self.ready = True
        self.last_ts = float(0)

    def is_bot(self, userid):
        return self.sc.api_call("users.info", user=userid)['user']['is_bot'] or userid == "USLACKBOT"

    def is_admin(self, userid):
        return self.sc.api_call("users.info", user=userid)['user']['is_admin']

    def find_im(self, userid):
        for im in self.sc.api_call("im.list")["ims"]:
            if im["user"] == userid:
                return im["id"]

        return None
