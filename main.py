import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import json 
import logging
from handlers.start import router as start_router
from handlers.meets import router as meets_router
from keyboards import get_main_keyboard

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

        @dp.message(lambda message: message.text in ["↩️ Назад к меню", "Главное меню"])
        async def back_to_menu(message: Message, state: FSMContext):
            await state.clear()
            await message.answer(
                "🏠 Главное меню:",
                reply_markup=get_main_keyboard()
            )

        logger.info("Бот запущен")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())