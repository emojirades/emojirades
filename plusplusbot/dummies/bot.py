import slack


class Bot:
    def __init__(self, app_token):
        self.client = slack.WebClient(app_token)

    def send_message(self, message, channel):
        self.client.chat_postMessage(text=message, channel=channel)
