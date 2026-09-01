import asyncio
import logging
from aiohttp import web

from aiogram.types import BotCommand

from bot import bot, dp
from database import init_db
from handlers import user, proof, admin

logging.basicConfig(level=logging.INFO)


async def health_handler(request):
    return web.Response(text="OK")


async def run_web():
    app = web.Application()
    app.router.add_get("/", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("Health server started on :8080")
    await asyncio.Event().wait()


async def main():
    await init_db()
    dp.include_router(user.router)
    dp.include_router(proof.router)
    dp.include_router(admin.router)

    await bot.set_my_commands(
        [
            BotCommand(command="/start", description="Bosh menyu"),
            BotCommand(command="/admin", description="Admin panel"),
        ]
    )

    await asyncio.gather(
        dp.start_polling(bot),
        run_web(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
