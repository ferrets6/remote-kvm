import asyncio
import json
import logging

import usb.core
import usb.backend.libusb1
import websockets

from keymap import CODE_TO_HID, CHAR_TO_HID

VID = 0x1209
PID = 0x0030
SEND_KEY = 0x13

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("unifying")

# pyusb/libusb keep one context alive for the process's whole lifetime. A
# device that gets reset out from under it (e.g. reflashed from the host,
# outside this container, while it's already running) can leave that context
# holding a handle libusb itself still thinks is valid but the kernel
# doesn't - every transfer then fails with "No such device" even though a
# fresh find() still lists the device by VID/PID. A plain unplug/replug
# doesn't hit this (libusb notices a real disconnect fine); resetting the
# backend is the standard fix for the narrower "device changed underneath an
# already-open context" case.
_backend = None


def _get_backend():
    global _backend
    if _backend is None:
        _backend = usb.backend.libusb1.get_backend()
    return _backend


def _reset_backend():
    global _backend
    _backend = None


def find_tx_dongle():
    """VID:PID 1209:0030 is shared by app_tx and app_rx; only app_tx should
    ever be plugged into this host, but if more than one shows up, prefer
    the one whose iProduct says TX rather than silently guessing."""
    candidates = list(usb.core.find(idVendor=VID, idProduct=PID, find_all=True, backend=_get_backend()))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    for dev in candidates:
        try:
            if "TX" in (dev.product or ""):
                return dev
        except (ValueError, usb.core.USBError):
            continue
    log.warning("multiple 1209:0030 devices found, none identifiable as TX; using the first")
    return candidates[0]


def send_key(code: str, key: str, mod: int, down: bool) -> bool:
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
        return False
    dev = find_tx_dongle()
    if dev is None:
        log.warning("no unifying TX dongle found on the bus")
        return False
    w_value = (mod << 8) | hid
    payload = bytes([1 if down else 0])
    try:
        dev.ctrl_transfer(0x40, SEND_KEY, w_value, 0, payload)
    except usb.core.USBError:
        log.warning("USB transfer failed, resetting libusb context and retrying once")
        _reset_backend()
        dev = find_tx_dongle()
        if dev is None:
            log.warning("no unifying TX dongle found on the bus after reset")
            return False
        dev.ctrl_transfer(0x40, SEND_KEY, w_value, 0, payload)
    return True


async def handle(ws):
    async for message in ws:
        try:
            event = json.loads(message)
            send_key(event.get("code", ""), event.get("key", ""), int(event.get("mod", 0)), bool(event["down"]))
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            log.warning("bad message %r: %s", message, e)
        except usb.core.USBError as e:
            log.warning("USB error sending key: %s", e)


async def main():
    async with websockets.serve(handle, "0.0.0.0", 8095):
        log.info("listening on :8095")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
