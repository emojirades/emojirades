import slack


class SlackClient(object):
    def __init__(self, token, logger):
        self.token = token
        self.logger = logger

        self.rtmclient = slack.RTMClient(token=token)
        self.webclient = slack.WebClient(token=token, timeout=30)

        self.last_ts = float(0)

        self.bot_id = self.webclient.auth_test()["user_id"]
        self.bot_name = self.user_info(self.bot_id)["real_name"]

        self.pretty_names = dict()

    def start(self):
        self.rtmclient.start()

    def set_webclient(self, webclient):
        self.webclient = webclient

    def user_info(self, user_id):
        return self.webclient.users_info(user=user_id)["user"]

    def is_bot(self, user_id):
        return self.user_info(user_id)["is_bot"] or userid == "USLACKBOT"

    def is_admin(self, user_id):
        return self.user_info(user_id)["is_admin"]

    def get_names(self, user_id):
        user = self.user_info(user_id)

        return {
            "name": user["name"],
            "real_name": user["real_name"],
        }

    def pretty_name(self, user_id):
        if user_id not in self.pretty_names:
            self.pretty_names[user_id] = self.user_info(user_id)

        user = self.pretty_names[user_id]

        return user.get("real_name", user.get("name", "Unknown User"))

    def find_im(self, user_id):
        # Find an existing IM (direct message) ID
        response = self.webclient.im_open(user=user_id)

        if response["ok"]:
            return response["channel"]["id"]

        # Attemp to locate an existing IM
        for im in self.webclient.im_list()["ims"]:
            if im["user"] == userid:
                return im["id"]

        return None
