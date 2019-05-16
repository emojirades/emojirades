from setuptools import setup, find_packages

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Emojirades PlusPlus",
    version="0.6.2",
    description="A Slack bot that understands the Emojirades game!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/michael-robbins/emojirades-plusplus",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
    ],
    keywords="slack slackbot emojirades",
    license="GNU",
    packages=find_packages(),
    install_requires=[
        "requests",
        "slackclient",
        "boto3",
        "Unidecode",
        "inflect",
    ],
    python_requires="~=3.7",
    extras_require={
        "test": ["pytest"],
    },
    scripts=["bin/emojirades-plusplus"],
    author="Michael Robbins",
    author_email="support@emojirades.io",
)
