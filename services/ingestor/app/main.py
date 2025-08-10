import asyncio
import logging
import signal

from .kafka_consumer import run_consumer
from .kafka_producer import close_producer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

async def _main():
    stop = asyncio.Event()

    def _graceful(*_):
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _graceful)

    await run_consumer(stop)
    await close_producer()

if __name__ == "__main__":
    asyncio.run(_main())
