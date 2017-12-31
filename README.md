# emojirades-plusplus
Slack bot that understands the emojirades game and handles score keeping

[![Build Status](https://travis-ci.org/michael-robbins/emojirades-plusplus.svg?branch=master)](https://travis-ci.org/michael-robbins/emojirades-plusplus)

# Installation Guide
`# Preferably run on a virtualenv`

## Install the dependencies
`pip install -r requirements.txt --upgrade`

## Install the module ( For Dev )
```
cd emojirades-plusplus
pip install -e .
```

## Run the tests
```
pip install -r test_requirements.txt --upgrade
pytest
```

## Set environment variable
Register your bot on slack, or pass me your email so I can add you to my Dev Slack workspace

`export SLACK_BOT_TOKEN='xoxb-*******'`

## Run the daemon
`main.py --score-file test.csv -vvv`

# Release process (for master branch)
1. Bump version in setup.py
2. Perform release in GitHub
3. TravisCI will automatically build and deploy on a tagged commit
