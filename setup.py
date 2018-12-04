from setuptools import setup, find_packages

setup(
    name="Emojirades PlusPlus",
    version="0.4.6",
    description="A Slack bot that understands the Emojirades game!",
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
        "slackclient",
        "boto3",
        "Unidecode"
    ],
    python_requires="~=3.7",
    extras_require={
        "test": ["pytest"],
    },
    scripts=["bin/emojirades-plusplus"],
    author="Michael Robbins",
    author_email="dont-spam-me@dont-spam-me.com"
)
