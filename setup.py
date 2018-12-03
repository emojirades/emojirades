from setuptools import setup, find_packages

setup(
    name="Emojirades PlusPlus",
    version="0.4.0",
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
        "slackclient>=1.1,<2",
        "boto3>=1.5,<2",
        "Unidecode>=1,<2"
    ],
    python_requires="~=3.7",
    extras_require={
        "test": ["pytest"],
    },
    scripts=["bin/emojirades-plusplus"]
)
