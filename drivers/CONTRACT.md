# Driver contract

Two categories of driver, each with a minimal contract. No shared library, no base
class — a driver is any container that satisfies the contract for its category.

## `video/<name>`

The container must serve an MJPEG multipart stream
(`multipart/x-mixed-replace;boundary=...`) over plain HTTP GET on its container port.
That's it — a browser `<img src="...">` can consume it natively, no JS glue needed.
How the container produces that stream internally is up to the driver.

## `hid/<name>`

The container must run a WebSocket server that accepts JSON text frames:

```json
{"code": "<KeyboardEvent.code>", "key": "<KeyboardEvent.key>", "mod": <modifier bitmask>, "down": true}
```

- `code`: the browser's `KeyboardEvent.code` (layout-independent), e.g. `"KeyA"`,
  `"Enter"`, `"ArrowLeft"`, `"F5"`. Use this for raw-HID-usage drivers (the OS on the
  other end resolves layout itself, same as a real keyboard).
- `key`: the browser's `KeyboardEvent.key` — the actual, layout/shift-resolved
  character (e.g. `"a"`, `"A"`, `"!"`). Use this if the driver types literal characters
  rather than raw HID usage codes.
- `mod`: bitmask, `ctrl=0x01 shift=0x02 alt=0x04 meta=0x08`.
- `down`: `true` on keydown, `false` on keyup.

What the driver does with that event (radio packet, WebSocket relay to another device,
anything else) is entirely up to it.

## Adding a driver

1. New folder `drivers/<category>/<name>/` with its own `Dockerfile`.
2. New service in `docker-compose.yml`.
3. One line of proxy config in `web/nginx.conf`.
4. One entry in the frontend driver switch (`web/app.js`), for `hid/` drivers.

No changes to any existing driver.
