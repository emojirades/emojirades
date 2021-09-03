# Copied from these two files and munged together to form a single mocking interface
# https://github.com/slackapi/python-slack-sdk/blob/main/tests/rtm/test_rtm_client_functional.py
# https://github.com/slackapi/python-slack-sdk/blob/main/tests/rtm/mock_web_api_server.py

import threading
import logging
import json

from http.server import HTTPServer, SimpleHTTPRequestHandler
from unittest import TestCase
from http import HTTPStatus
from typing import Type


# Mock API Server
class MockHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    default_request_version = "HTTP/1.1"
    logger = logging.getLogger(__name__)

    def is_valid_token(self):
        return "authorization" in self.headers and str(
            self.headers["authorization"]
        ).startswith("Bearer xoxb-")

    def is_invalid_rtm_start(self):
        return (
            "authorization" in self.headers
            and str(self.headers["authorization"]).startswith("Bearer xoxb-rtm.start")
            and str(self.path) != "/rtm.start"
        )

    def set_common_headers(self):
        self.send_header("content-type", "application/json;charset=utf-8")
        self.send_header("connection", "close")
        self.end_headers()

    def _handle(self):
        print(self.path)
        data = self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8")

        responses = {
            "rtm_start_success": {
                "ok": True,
                "url": "ws://localhost:8765/",
                "self": {
                    "id": self.test.config.bot_id,
                    "name": self.test.config.bot_name,
                    },
                "team": {
                    "domain": self.test.config.team_url,
                    "id": self.test.config.team,
                    "name": self.test.config.team_name,
                },
            },
            "rtm_start_failure": {
                "ok": False,
                "error": "invalid_auth",
            },
            "/auth.test": {
                "ok": True,
                "url": self.test.config.team_url,
                "team": self.test.config.team_name,
                "user": "bot",
                "team_id": self.test.config.team,
                "user_id": self.test.config.bot_id,
                "bot_id": self.test.config.bot_id,
            },
            "/users.info#generic": {
                "ok": True,
                "user": {
                    "id": "U99999999",
                    "team_id": self.test.config.team,
                    "name": "Generic User",
                    "real_name": "Generic User",
                },
            },
            "/users.info#user=U00000000": {
                "ok": True,
                "user": {
                    "id": self.test.config.bot_id,
                    "team_id": self.test.config.team,
                    "name": self.test.config.bot_name,
                    "real_name": self.test.config.bot_name,
                },
            },
            "/users.info#user=U00000001": {
                "ok": True,
                "user": {
                    "id": self.test.config.player_1,
                    "team_id": self.test.config.team,
                    "name": self.test.config.player_1_name,
                    "real_name": self.test.config.player_1_name,
                },
            },
            "/users.info#user=U00000002": {
                "ok": True,
                "user": {
                    "id": self.test.config.player_2,
                    "team_id": self.test.config.team,
                    "name": self.test.config.player_2_name,
                    "real_name": self.test.config.player_2_name,
                },
            },
            "/users.info#user=U00000003": {
                "ok": True,
                "user": {
                    "id": self.test.config.player_3,
                    "team_id": self.test.config.team,
                    "name": self.test.config.player_3_name,
                    "real_name": self.test.config.player_3_name,
                },
            },
            "/users.info#user=U00000004": {
                "ok": True,
                "user": {
                    "id": self.test.config.player_4,
                    "team_id": self.test.config.team,
                    "name": self.test.config.player_4_name,
                    "real_name": self.test.config.player_4_name,
                },
            },
            "/chat.postMessage": {
                "ok": True,
            },
            "/conversations.open": {
                "ok": True,
                "channel": {
                    "id": None,
                },
            },
            "/reactions.add": {
                "ok": True,
            }
        }

        if self.is_invalid_rtm_start():
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.set_common_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.set_common_headers()

        if self.path == "/rtm.connect":
            if self.is_valid_token():
                response = responses["rtm_start_success"]
            else:
                response = responses["rtm_start_failure"]

        elif self.path == "/users.info":
            try:
                response = responses[f"/users.info#{data}"]
            except KeyError:
                response = responses["/users.info#generic"]

        elif self.path == "/conversations.open":
            response = responses["/conversations.open"]

            user_id = json.loads(data)["users"][0]
            channel_id = "D" + user_id[1:]

            response["channel"]["id"] = channel_id
        elif self.path == "/chat.postMessage":
            response = responses[self.path]

            message = json.loads(data)
            self.test.responses.append((message["channel"], message["text"]))
        elif self.path == "/reactions.add":
            response = responses[self.path]

            message = json.loads(data)
            self.test.reactions.append((message["channel"], message["name"], message["timestamp"]))
        else:
            response = responses[self.path]

        print(response)
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()


class MockServerThread(threading.Thread):
    def __init__(
        self, test: TestCase, handler: Type[SimpleHTTPRequestHandler] = MockHandler
    ):
        threading.Thread.__init__(self)
        self.handler = handler
        self.handler.test = test
        self.test = test

    def run(self):
        self.server = HTTPServer(("localhost", 8888), self.handler)
        self.test.server_url = "http://localhost:8888"
        self.test.host, self.test.port = self.server.socket.getsockname()
        self.test.server_started.set()  # threading.Event()

        self.test = None
        try:
            self.server.serve_forever(0.05)
        finally:
            self.server.server_close()

    def stop(self):
        self.server.shutdown()
        self.join()


def setup_mock_web_api_server(test: TestCase):
    test.server_started = threading.Event()
    test.thread = MockServerThread(test)
    test.thread.start()
    test.server_started.wait()


def cleanup_mock_web_api_server(test: TestCase):
    test.thread.stop()
    test.thread = None
