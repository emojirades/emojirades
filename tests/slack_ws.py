#!/usr/bin/env python3

import logging

import asyncio

from websockets.exceptions import ConnectionClosed
from websockets import serve

# logger = logging.getLogger("websockets.server")
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


async def echo(websocket):
    try:
        async for message in websocket:
            await websocket.send(message)
            # print(message)
    except ConnectionClosed:
        pass


async def main():
    async with serve(echo, host="localhost", port=8765, compression=None):
        await asyncio.Future()


# logger.info("Starting ws://localhost:8765/")
asyncio.run(main())
