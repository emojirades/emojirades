FROM python:3.8-buster

RUN pip3 install --upgrade emojirades==0.10.0

ENTRYPOINT ["/usr/local/bin/emojirades"]
