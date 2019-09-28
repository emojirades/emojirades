from pytest_bdd import given, when, then, scenarios, parsers

from plusplusbot.dummies.bot import Bot

scenarios('../features/dummy_chat.feature')


@given('Robbins is online')
def robbins():
    return Bot('xoxb-287903457776-778486608183-LhxEzpcdkCvu72cT0t4ryiA4')


@given('Dave is online')
def dave():
    return Bot('xoxb-287903457776-770225171793-uQ1YSPkphomPNMa3HJ9UPADM')


@when(parsers.parse('Robbins says "{phrase}"'))
def robbins_says(phrase):
    Bot('xoxb-287903457776-778486608183-LhxEzpcdkCvu72cT0t4ryiA4').send_message(phrase, '#random')


@then(parsers.parse('Dave says "{phrase}"'))
def dave_says(phrase):
    Bot('xoxb-287903457776-770225171793-uQ1YSPkphomPNMa3HJ9UPADM').send_message(phrase, '#random')
