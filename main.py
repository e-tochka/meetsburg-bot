import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import json 
import logging

from database import db

from handlers.start import router as start_router
from handlers.newmeet import router as meets_router
from handlers.qr import router as qr_router
from handlers.my_meets import router as my_meets_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        with open('conf.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        token = data.get('token')
        if not token:
            logger.error("Токен не найден")
            return
        
        bot = Bot(token=token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        dp.include_router(start_router)
        dp.include_router(meets_router)
        dp.include_router(my_meets_router)
        dp.include_router(qr_router)

        logger.info("Бот запущен")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())