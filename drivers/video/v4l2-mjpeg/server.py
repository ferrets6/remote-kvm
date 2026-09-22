import asyncio
import logging
import os

DEVICE = os.environ.get("DEVICE", "/dev/video0")
VIDEO_SIZE = os.environ.get("VIDEO_SIZE", "1920x1080")
FRAME_RATE = os.environ.get("FRAME_RATE", "30")
BOUNDARY = b"--ffmpeg"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("video")

# ffmpeg -listen serves exactly one client per process lifetime, which makes
# every browser reconnect (page reload, second tab) a coin flip: whoever
# doesn't get the single slot just hangs until timeout. Running ffmpeg once,
# reading its raw mpjpeg bytes ourselves, and fanning frames out to any
# number of subscriber queues removes that limitation entirely.
subscribers: set[asyncio.Queue] = set()


def broadcast(frame: bytes) -> None:
    for q in list(subscribers):
        try:
            q.put_nowait(frame)
        except asyncio.QueueFull:
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
            q.put_nowait(frame)


async def ffmpeg_loop() -> None:
    while True:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-f", "v4l2", "-input_format", "mjpeg",
            "-video_size", VIDEO_SIZE, "-framerate", FRAME_RATE, "-i", DEVICE,
            "-c:v", "copy", "-f", "mpjpeg", "-boundary_tag", "ffmpeg", "pipe:1",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        buf = b""
        while True:
            chunk = await proc.stdout.read(65536)
            if not chunk:
                break
            buf += chunk
            while True:
                idx = buf.find(BOUNDARY, len(BOUNDARY))
                if idx == -1:
                    break
                frame, buf = buf[:idx], buf[idx:]
                broadcast(frame)
        log.warning("ffmpeg exited, restarting in 1s")
        proc.kill()
        await asyncio.sleep(1)


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=2)
    except (asyncio.TimeoutError, asyncio.IncompleteReadError):
        pass
    writer.write(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: multipart/x-mixed-replace;boundary=ffmpeg\r\n"
        b"Connection: close\r\n\r\n"
    )
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    subscribers.add(q)
    try:
        while True:
            frame = await q.get()
            writer.write(frame)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        subscribers.discard(q)
        writer.close()


async def main() -> None:
    asyncio.create_task(ffmpeg_loop())
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8091)
    log.info("listening on :8091, device=%s", DEVICE)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
