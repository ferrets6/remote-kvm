# remote-kvm

Web KVM: live video + real HID keyboard input, delivered as pluggable Docker drivers
behind one static frontend. See `README.md` for what it does and how to run it.

## Architecture

- `web/` — static frontend (nginx). Serves the page, proxies `/video` to the video
  driver and `/ws/hid/<name>` to each HID driver. This is the only piece the browser
  ever talks to directly.
- `drivers/video/<name>/` and `drivers/hid/<name>/` — one container per driver, each
  independent (own `Dockerfile`, own dependencies). The contract each category must
  satisfy is in `drivers/CONTRACT.md` — read that before touching or adding a driver.
- `docker-compose.yml` wires it all together. One driver = one service.

Drivers never talk to each other or share code. If you're tempted to add a shared
helper library across drivers, that's a sign the contract should absorb it instead.

## Adding a driver

1. New folder under `drivers/video/` or `drivers/hid/`, own `Dockerfile`.
2. Satisfy the contract in `drivers/CONTRACT.md` — nothing else is required.
3. Add it as a service in `docker-compose.yml`.
4. Add a proxy line in `web/nginx.conf` (and, for HID, an entry in `web/app.js`'s
   driver switch).

Don't touch existing drivers to add a new one. If you find yourself needing to, the
contract is probably wrong — fix the contract, not the drivers.

## Conventions

- Comments and commit messages: English, regardless of what language the conversation
  that produced them was in.
- Keep drivers minimal: stdlib + the one library the transport actually needs
  (`pyusb`, `websockets`). No shared framework across them.
- `.env` (not committed) holds host-specific values: capture device path, HID device
  IPs. `.env.example` is the source of truth for what's expected there.

## Known rough edges (intentionally not "fixed" here)

- `drivers/hid/unifying`: fast input (fast typing, paste) can drop or garble
  characters — the RX dongle's USB-HID report queue is a single non-blocking slot
  (see the `unifying-cc2544-radiokey` firmware's own `TODO.md`). No throttling has
  been added on this side on purpose; if you want to fix it, it belongs either in that
  firmware or as an explicit, opt-in rate limit here — not a silent sleep().
- `drivers/hid/esp32`: character mapping goes through the ESP32 firmware's own
  keyboard-layout table (currently Italian). If the target machine's OS keymap doesn't
  match, symbols come out wrong (this is a layout mismatch, not a bug in this repo).
