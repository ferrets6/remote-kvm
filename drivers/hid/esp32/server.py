import asyncio
import json
import logging
import os

import websockets
import websockets.exceptions

from keymap import SPECIAL_KEYS, MOD_NAMES

ESP32_IP = os.environ["ESP32_IP"]
ESP32_URL = f"ws://{ESP32_IP}/ws"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("esp32")

esp32_ws = None  # persistent outbound connection, maintained by esp32_link()


def mods_prefix(mod: int) -> str:
    return ",".join(name for bit, name in MOD_NAMES if mod & bit)


def to_command(event: dict) -> str | None:
    if not event.get("down"):
        return None  # ESP32 side does full press+release per command already
    code = event.get("code", "")
    mods = mods_prefix(int(event.get("mod", 0)))
    if code in SPECIAL_KEYS:
        name = SPECIAL_KEYS[code]
        return f"kg:{mods}:{name}" if mods else f"kk:{name}"
    key = event.get("key", "")
    if not key or len(key) != 1:
        return None
    return f"kg:{mods}:{key}" if mods else f"kt:{key}"


async def esp32_link():
    """Keeps a persistent connection to the ESP32 open, reconnecting on drop."""
    global esp32_ws
    while True:
        try:
            async with websockets.connect(ESP32_URL) as ws:
                log.info("connected to ESP32 at %s", ESP32_URL)
                esp32_ws = ws
                await ws.wait_closed()
        except OSError as e:
            log.warning("can't reach ESP32 at %s: %s", ESP32_URL, e)
        esp32_ws = None
        await asyncio.sleep(2)


async def handle(browser_ws):
    async for message in browser_ws:
        try:
            event = json.loads(message)
            command = to_command(event)
        except (ValueError, json.JSONDecodeError) as e:
            log.warning("bad message %r: %s", message, e)
            continue
        if command is None:
            continue
        if esp32_ws is None:
            log.warning("ESP32 not connected, dropping %r", command)
            continue
        try:
            await esp32_ws.send(command)
        except websockets.exceptions.ConnectionClosed:
            log.warning("ESP32 connection closed, dropping %r", command)


async def main():
    asyncio.create_task(esp32_link())
    async with websockets.serve(handle, "0.0.0.0", 8096):
        log.info("listening on :8096, forwarding to %s", ESP32_URL)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
