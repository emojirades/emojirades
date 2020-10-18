# emojirades
Slack bot that understands the emojirades game and handles score keeping

[![Build Status](https://travis-ci.com/emojirades/emojirades.svg?branch=master)](https://travis-ci.org/emojirades/emojirades) [![PyPI version](https://badge.fury.io/py/Emojirades.svg)](https://badge.fury.io/py/Emojirades)

# Installation Guide
`# Preferably run on a virtualenv`

## Install the dependencies
```bash
pip3 install --upgrade pip wheel

pip3 install -r requirements.txt --upgrade

# If you're developing locally
pip3 install -r test_requirements.txt --upgrade
```

## Install the module ( For Dev )
```bash
cd emojirades
pip3 install -e .
```

## Run the tests
```bash
black .
pytest
```

## Set environment variables
If you're using the built in AWS functionality to persist your data, you'll need to set the appropriate AWS_ environment variables.

## Run the daemon for a single workspace
This command uses locally stored files to keep the game state:

`emojirades single --score-file scores.csv --state-file state.json --auth-file auth.json`

This command uses S3 stored files to keep the game state:

`emojirades single --score-file s3://bucket/scores.csv --state-file s3://bucket/state.json --auth-file s3://bucket/auth.json

## Run the daemon for multiple workspaces
Here we provide a local folder of workspaces and an optional set of workspace ids (will load all in folder by default):

`emojirades mulitple --workspaces-dir path/to/workspaces [--workspace-id A1B2C3D4E]`

Here we provide an S3 path of workspaces and an optional set of workspace ids (will load all in folder by default):

`emojirades multiple --workspaces-dir s3://bucket/path/to/workspaces [--workspace-id A1B2C3D4E]`

Here we provide an S3 path of workspaces and an AWS SQS queue to listen to for new workspaces:

`emojirades multiple --workspaces-dir s3://bucket/path/to/workspaces --onboarding-queue workspace-onboarding-queue`

The workspaces directory must be in the following format (local or s3):
```
./workspaces

./workspaces/shards
./workspaces/shards/0
./workspaces/shards/0/A1B2C3D4E.json
./workspaces/shards/0/Z9Y8X7W6V.json

./workspaces/directory
./workspaces/directory/A1B2C3D4E
./workspaces/directory/A1B2C3D4E/state.json
./workspaces/directory/A1B2C3D4E/scores.json
./workspaces/directory/A1B2C3D4E/auth.json
./workspaces/directory/Z9Y8X7W6V
./workspaces/directory/Z9Y8X7W6V/state.json
./workspaces/directory/Z9Y8X7W6V/scores.json
./workspaces/directory/Z9Y8X7W6V/auth.json
```

The concept above with the two different directories is shards to allow for the bot to scale out horizontally. As the bot(s) get busier, the operator can increase the shard (bot instance) count and new onboarded workspaces are allocated to the next available shard with capacity.

The emojirades bot will take care of running multiple games across different channels in a single workspace.

## Service configuration
```
cp emojirades.service /etc/systemd/system/
sudo chmod 0664 /etc/systemd/system/emojirades.service

# Edit the /etc/systemd/system/emojirades.service file and update the user and group

cp emojirades.config /etc/emojirades
sudo chmod 0400 /etc/emojirades

# Edit the /etc/emojirades config file with your configuration for the bot

sudo systemctl daemon-reload
sudo systemctl enable emojirades
sudo systemctl start emojirades

```
# Release process (for master branch)
1. Create release branch containing new version in setup.py and Dockerfile
2. Perform a PR into master
3. Perform release in GitHub
4. TravisCI will automatically build and deploy on a tagged commit into master (the release does this)
5. Docker Hub will automatically build and deploy on a tagged commit into master (the release does this)

## Building the Container Image
```
docker build --pull --no-cache -t emojirades/emojirades:X.Y.Z -t emojirades/emojirades:latest .
```

## Running the Container
In this example we run the game with S3 hosted configuration for a single workspace.

```
docker run -d \
  --name emojirades \
  --restart=always \
  -v "/path/to/your/.aws/:/root/.aws/:ro" \
  -e "AWS_PROFILE=emojirades" \
  emojirades/emojirades:X.Y.Z \
    --score-file s3://bucket/path/to/scores.json \
    --state-file s3://bucket/path/to/state.json \
    --auth-file s3://bucket/path/to/auth.json \
    -vv
```
