FROM python:3.8-buster

WORKDIR /build

COPY bin /build/bin
COPY emojirades /build/emojirades
COPY setup.cfg pyproject.toml README.md LICENSE /build/

RUN pip3 install --upgrade setuptools wheel build
RUN python3 -m build


FROM python:3.8-buster

COPY --from=0 /build/dist/emojirades-*-py3-none-any.whl /tmp/
RUN pip3 install /tmp/emojirades-*-py3-none-any.whl && rm /tmp/emojirades-*-py3-none-any.whl

ENTRYPOINT ["/usr/local/bin/emojirades"]
