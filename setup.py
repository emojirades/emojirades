from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Emojirades",
    version="0.16.1",
    description="A Slack bot that understands the Emojirades game!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emojirades/emojirades",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
    ],
    keywords="slack slackbot emojirades plusplus game",
    packages=find_packages(),
    install_requires=[
        "slackclient",
        "requests",
        "boto3",
        "Unidecode",
        "pendulum",
        "expiringdict",
        "SQLAlchemy",
        "alembic",
        "psycopg2-binary",
    ],
    python_requires="~=3.8",
    extras_require={
        "test": ["boto3", "pytest", "black"],
    },
    scripts=["bin/emojirades"],
    author="The Emojirades Team",
    author_email="support@emojirades.io",
)
