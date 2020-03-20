FROM python:3.8-buster

RUN pip3 install --upgrade emojirades-plusplus==0.9.2

ENTRYPOINT ["/usr/local/bin/emojirades-plusplus"]
