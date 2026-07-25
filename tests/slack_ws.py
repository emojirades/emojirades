import asyncio
import threading
import time

from websockets import serve
from websockets.exceptions import ConnectionClosed


async def echo(websocket):
    try:
        async for message in websocket:
            await websocket.send(message)
    except ConnectionClosed:
        pass


class MockWsServerThread(threading.Thread):
    def __init__(self, host="localhost", port=8765):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.loop = None
        self.server = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def _main():
            self.server = await serve(echo, host=self.host, port=self.port, compression=None)
            await self.server.wait_closed()

        try:
            self.loop.run_until_complete(_main())
        except Exception:
            pass

    def stop(self):
        if self.loop and self.server:
            self.loop.call_soon_threadsafe(self.server.close)
            time.sleep(0.1)
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.join(timeout=2)


def start_mock_ws_server(host="localhost", port=8765):
    thread = MockWsServerThread(host=host, port=port)
    thread.start()
    time.sleep(0.5)
    return thread


def stop_mock_ws_server(thread):
    if thread:
        thread.stop()


async def main():
    async with serve(echo, host="localhost", port=8765, compression=None):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
