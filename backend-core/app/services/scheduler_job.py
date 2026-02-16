import asyncio
import logging

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")


async def run_cycle() -> None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("http://backend-core:8000/analyze")
            response.raise_for_status()
            logger.info("Analyze cycle completed")
    except Exception as exc:  # pragma: no cover - runtime robustness
        logger.warning("Analyze cycle failed: %s", exc)


async def main() -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_cycle, "interval", minutes=5)
    scheduler.start()
    await run_cycle()
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
