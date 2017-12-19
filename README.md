# emojirades-plusplus
Slack bot that understands the emojirades game and handles score keeping

# Installation Guide
`# Preferably run on a virtualenv`

## Install the dependencies
`pip install -r requirements`

## Install the module ( For Dev )
`cd emojirades-plusplus`  
`pip install -e .`

## Set environment variable
Register your bot on slack, or pass me your email so I can add you to my Dev Slack workspace

`export SLACK_BOT_TOKEN='xoxb-*******'`

## Run the daemon
`main.py --score-file test.csv -vvv`