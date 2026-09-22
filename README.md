# remote-kvm

A web KVM: live video + real keyboard input for whatever PC, NAS, or Raspberry Pi you've
got a capture device and an HID injector plugged into. Point your browser at it and it's
like sitting in front of the machine — useful when the OS is stuck in a boot menu, GRUB,
or a crashed desktop with no other way in.

Video and keyboard input are both handled as **drivers** — small, independent
containers, each implementing one minimal contract (see [`drivers/CONTRACT.md`](drivers/CONTRACT.md)).
Today's drivers are just the first examples:

- `drivers/video/v4l2-mjpeg` — any V4L2 UVC capture device (webcam, HDMI-to-USB dongle,
  whatever `/dev/videoN` your machine exposes), streamed as MJPEG via ffmpeg.
- `drivers/hid/unifying` — a custom CC2544 radio dongle pair acting as a wireless
  keyboard-injection link.
- `drivers/hid/esp32` — an ESP32-S3 acting as a WiFi-controlled USB HID keyboard.

Swap in a different capture card, a different microcontroller, an IP-KVM chip, whatever
— add a folder under `drivers/`, a compose service, and a proxy line. Nothing else
changes.

## Running it

```
cp .env.example .env   # fill in the driver-specific settings you need
docker compose up -d --build
```

Only the `kvm-web` service publishes a port; everything else stays on the internal
compose network.

## Layout

```
drivers/
  CONTRACT.md       the two driver contracts (video, hid)
  video/v4l2-mjpeg/
  hid/unifying/
  hid/esp32/
web/                the frontend: live video + keyboard capture + driver switch
docker-compose.yml
```
