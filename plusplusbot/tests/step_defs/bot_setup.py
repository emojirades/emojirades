import os
from pytest_bdd import given

from plusplusbot.dummies.bot import Bot


@given('Robbins is online')
def robbins():
    return Bot(os.environ.get("ROBBINS_BOT_TOKEN", None))


@given('Dave is online')
def dave():
    return Bot(os.environ.get("DAVE_BOT_TOKEN", None))
