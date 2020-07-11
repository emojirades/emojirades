FROM python:3.8-buster

WORKDIR /build

COPY bin /build/bin
COPY emojirades /build/emojirades
COPY setup.cfg setup.py requirements.txt README.md /build/

RUN pip3 install --upgrade -r requirements.txt
RUN rm requirements.txt

RUN pip3 install --upgrade setuptools wheel
RUN python3 setup.py bdist_wheel


FROM python:3.8-buster

COPY --from=0 /build/dist/Emojirades-*-py3-none-any.whl /tmp/
RUN pip3 install /tmp/Emojirades-*-py3-none-any.whl && rm /tmp/Emojirades-*-py3-none-any.whl

ENTRYPOINT ["/usr/local/bin/emojirades"]
