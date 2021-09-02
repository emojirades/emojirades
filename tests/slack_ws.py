#!/usr/bin/env python3

import logging

import asyncio

from websockets import serve


logger = logging.getLogger("websockets.server")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


async def echo(websocket, path):
    async for message in websocket:
        await websocket.send(message)
        print(message)


async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()


logger.info("Starting ws://localhost:8765/")
asyncio.run(main())
