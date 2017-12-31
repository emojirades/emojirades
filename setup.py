from setuptools import setup, find_packages

setup(
    name="Emojirades PlusPlus",
    version="0.0.1",
    description="A Slack bot that understands the Emojirades game!",
    url="https://github.com/michael-robbins/emojirades-plusplus",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
    ],
    keywords="slack slackbot emojirades",
    license="GNU",
    packages=["plusplusbot"],
    install_requires=[
        "slackclient>=1.1,<2",
    ],
    python_requires="~=3.6",
    extra_requires={
        "test": ["pytest>=3.3,<4"],
    },
    scripts=["bin/emojirades-plusplus"]
)
