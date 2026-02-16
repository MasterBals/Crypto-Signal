import asyncio

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def run_cycle() -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post("http://backend-core:8000/analyze")


async def main() -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_cycle, "interval", minutes=5)
    scheduler.start()
    await run_cycle()
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
