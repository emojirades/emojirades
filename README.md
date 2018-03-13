# emojirades-plusplus
Slack bot that understands the emojirades game and handles score keeping

[![Build Status](https://travis-ci.org/michael-robbins/emojirades-plusplus.svg?branch=master)](https://travis-ci.org/michael-robbins/emojirades-plusplus)

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

# Release process (for master branch)
1. Create release branch containing new version in setup.py
2. Perform a PR into master
3. Perform release in GitHub
4. TravisCI will automatically build and deploy on a tagged commit into master (the release does this)
