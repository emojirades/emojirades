FROM python:3.7-stretch

RUN pip3 install --upgrade emojirades-plusplus

CMD emojirades-plusplus --score-file $SCORE_FILE --state-file $STATE_FILE -vv
