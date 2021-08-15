# Emojirades
Slack bot that understands the emojirades game and handles score keeping.

[![Build Status](https://travis-ci.com/emojirades/emojirades.svg?branch=master)](https://travis-ci.org/emojirades/emojirades) [![PyPI version](https://badge.fury.io/py/Emojirades.svg)](https://badge.fury.io/py/Emojirades)

# Developing
## Install the dependencies
```bash
pip3 install --upgrade pip wheel

pip3 install -r requirements.txt --upgrade
pip3 install -r test_requirements.txt --upgrade
```

## Install the module
```bash
pip3 install -e .
```

## Run the tests
```bash
# Linter
pylint emojirades

# Formatter
black --check .

# Tests
pytest
```

## Creating new DB revisions
If you make changes to `emojirades/persistence/models` you'll need to generate new revisions. This tracks the changes and applies them to the DB at each bots startup
```
cd emojirades/persistence/models
alembic revision --autogenerate --message "<useful insightful few words>"
```

# Running
## Set Environment Variables
If you're using an auth file from AWS S3 you'll need to set the appropriate `AWS_` environment variables!

## Separate Database
Using a database like PostgreSQL, you'll need to have created a database with a username and password before starting this.

If you've just created a fresh DB, you'll need to load the initial database:
```
emojirades -vv init --db-uri "sqlite:///emojirades.db"
```

After initialising the DB you can load in any optional pre-existing state:
```
emojirades -vv populate --db-uri "sqlite:///emojirades.db" --table gamestate --data-file path/to/gamestate.json
```

The json files must be a list of objects, with each objects `key: value` representing a column in the associated model

If you are coming from the old style of state.json and scores.json you can run the following to produce json files that can be used in the above populate command

```
./bin/old_to_new_persistence.py --workspace-id TABC123 --state-file state.json --score-file scores.json
```

This will produce `state.json.processed`, `scores.json.processed_scores` and `scores.json.processed_score_history`

They can be populated by running:
```
emojirades -vv populate --db-uri "sqlite:///emojirades.db" --table gamestate --data-file state.json.processed
emojirades -vv populate --db-uri "sqlite:///emojirades.db" --table scoreboard --data-file scores.json.processed_scores
emojirades -vv populate --db-uri "sqlite:///emojirades.db" --table scoreboard_history --data-file scores.json.processed_score_history
```

## Run the daemon for a single workspace
This command uses locally stored files to keep the game state:

`emojirades single --db-uri sqlite:///emojirades.db --auth-uri auth.json`

This command uses a separate PostgreSQL DB and an auth file from AWS S3:

`emojirades single --db-uri postgresql://user:pass@hostname/database --auth-uri s3://bucket/auth.json

## Run the daemon for multiple workspaces
Here we provide a local folder of workspaces and an optional set of workspace ids (will load all in folder by default):

`emojirades mulitple --workspaces-dir path/to/workspaces [--workspace-id A1B2C3D4E]`

Here we provide an S3 path of workspaces and an optional set of workspace ids (will load all in folder by default):

`emojirades multiple --workspaces-dir s3://bucket/path/to/workspaces [--workspace-id A1B2C3D4E]`

Here we provide an S3 path of workspaces and an AWS SQS queue to listen to for new workspaces:

`emojirades multiple --workspaces-dir s3://bucket/path/to/workspaces --onboarding-queue workspace-onboarding-queue`

Here we provide an S3 path of workspaces and override the db_uri:

`emojirades multiple --workspaces-dir s3://bucket/path/to/workspaces --db-uri sqlite:///emojirades.db

The workspaces directory must be in the following format (local or s3):
```
./workspaces

./workspaces/shards
./workspaces/shards/0
./workspaces/shards/0/A1B2C3D4E.json
./workspaces/shards/0/Z9Y8X7W6V.json

./workspaces/directory
./workspaces/directory/A1B2C3D4E
./workspaces/directory/A1B2C3D4E/auth.json
./workspaces/directory/Z9Y8X7W6V
./workspaces/directory/Z9Y8X7W6V/auth.json
```

Each instance of the bot will listen to a specific shard (specified as the --workspaces-dir).

The contents of the shard config (eg. `./workspaces/shards/0/A1B2C3D4E.json`) will be a file similar to:
```
{
  "workspace_id": "A1B2C3D4E",
  "db_uri": "sqlite:////data/emojirades.db",
  "auth_uri": "s3://bucket/workspaces/directory/A1B2C3D4E/auth.json",
}
```

The concept above with the two different directories is shards to allow for the bot to scale out horizontally. As the bot(s) get busier, the operator can increase the shard count (number of bot instances) and new onboarded workspaces are allocated to the next available shard with capacity.

The emojirades bot will take care of running multiple games across different channels in a single workspace. This is a limitation in the design currently where you need a bot-per-workspace.

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
1. Update `setup.py` with the new version (vX.Y.Z)
2. Commit into the master branch
3. Tag the commit with vX.Y.Z
4. Github Actions will trigger the Release Job when a tagged commit to master is detected
    1. Changelog will be generated and a Github Release as well with the changelog
    2. New python wheel will be built and published to PyPI and attached to the Release
    3. New container image will be built and published to Docker Hub

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
  -v "emojirades-data:/data" \
  -e "AWS_PROFILE=emojirades" \
  emojirades/emojirades:X.Y.Z \
    --db-uri sqlite:////data/emojirades.db \
    --auth-uri s3://bucket/path/to/auth.json \
    -vv
```
