import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot import admin, db, user
from bot.config import ADMIN_IDS, BOT_TOKEN


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi (.env faylini tekshiring)")
    if not ADMIN_IDS:
        logging.warning("ADMIN_IDS bo'sh — admin panel hech kimga ochiq emas")
    await db.init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(admin.router)
    dp.include_router(user.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
