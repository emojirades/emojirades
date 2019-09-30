from pytest_bdd import when, then, scenarios, parsers
from plusplusbot.tests.step_defs.bot_setup import *


scenarios('../features/dummy_chat.feature')


@when(parsers.parse('Robbins says "{phrase}"'))
def robbins_says(robbins, phrase):
    robbins.send_message(phrase, '#random')


@then(parsers.parse('Dave says "{phrase}"'))
def dave_says(dave, phrase):
    dave.send_message(phrase, '#random')
