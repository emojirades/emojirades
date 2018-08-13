# emojirades-plusplus
Slack bot that understands the emojirades game and handles score keeping

[![Build Status](https://travis-ci.org/michael-robbins/emojirades-plusplus.svg?branch=master)](https://travis-ci.org/michael-robbins/emojirades-plusplus) [![PyPI version](https://badge.fury.io/py/Emojirades-PlusPlus.svg)](https://badge.fury.io/py/Emojirades-PlusPlus)

# Installation Guide
`# Preferably run on a virtualenv`

## Install the dependencies
`pip3 install -r requirements.txt --upgrade`

## Install the module ( For Dev )
```
cd emojirades-plusplus
pip3 install -e .
```

## Run the tests
```
pip3 install -r test_requirements.txt --upgrade
pycodestyle
pytest
```

## Set environment variables
Register your bot on slack, or pass me your email so I can add you to my Dev Slack workspace

`export SLACK_BOT_TOKEN='xoxb-*******'`


Optionally if you are saving data into S3, you might need to set the profile to use

`export AWS_PROFILE='dev-profile'`

## Run the daemon
`emojirades-plusplus --score-file scores.csv --state-file state.json -vv`

## Service configuration
```
cp emojirades.service /etc/systemd/system/
sudo chmod 0664 /etc/systemd/system/emojirades.service

# Edit the /etc/systemd/system/emojirades.service file and update the user and group

cp emojiradesplusplus.config /etc/emojiradesplusplus
sudo chmod 0400 /etc/emojiradesplusplus

# Edit the /etc/emojiradesplusplus config file with your configuration for the bot

sudo systemctl daemon-reload
sudo systemctl enable emojirades
sudo systemctl start emojirades
```


# Release process (for master branch)
1. Create release branch containing new version in setup.py
2. Perform a PR into master
3. Perform release in GitHub
4. TravisCI will automatically build and deploy on a tagged commit into master (the release does this)
