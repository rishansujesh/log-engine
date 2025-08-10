import asyncio
import logging
import signal
from typing import Optional

from .kafka_consumer import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

_shutdown: Optional[asyncio.Event] = None


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    global _shutdown
    _shutdown = asyncio.Event()

    def _sig(*_):
        if _shutdown and not _shutdown.is_set():
            _shutdown.set()

    for s in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(s, _sig)
        except NotImplementedError:
            # On Windows
            pass


async def _main() -> None:
    loop = asyncio.get_running_loop()
    _install_signal_handlers(loop)
    consumer_task = asyncio.create_task(run())

    await _shutdown.wait()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(_main())
