import asyncio
import json
import logging
import os

import websockets
import websockets.exceptions

from keymap import CODE_TO_HID, CHAR_TO_HID

ESP32_IP = os.environ["ESP32_IP"]
ESP32_URL = f"ws://{ESP32_IP}/ws"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("esp32")

esp32_ws = None  # persistent outbound connection, maintained by esp32_link()


def to_command(code: str, key: str, mod: int, down: bool) -> str | None:
    hid = CODE_TO_HID.get(code)
    if hid is None and key:
        # No usable `code` (e.g. paste: the browser only gives us resolved
        # text, not which physical keys produced it) - fall back to a
        # literal-character table instead.
        entry = CHAR_TO_HID.get(key)
        if entry:
            hid, needs_shift = entry
            if needs_shift:
                mod |= 0x02
    if hid is None:
        log.info("no HID mapping for code=%s key=%r, ignoring", code, key)
        return None
    return f"hr:{mod}:{hid}:{1 if down else 0}"


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
        except (ValueError, json.JSONDecodeError) as e:
            log.warning("bad message %r: %s", message, e)
            continue
        command = to_command(
            event.get("code", ""), event.get("key", ""),
            int(event.get("mod", 0)), bool(event.get("down")),
        )
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
