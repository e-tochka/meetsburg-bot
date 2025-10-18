from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import get_main_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать!\n☝️ Настоятельно рекомендуем ознакомиться с /help",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
@router.message(lambda message: message.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    help_text = """
🤖 <b>ПОМОЩЬ ПО БОТУ</b>

━━━━━━━━━━━━━━━━━━━━

🎯 <b>ОСНОВНЫЕ КОМАНДЫ</b>

├─ 🗓 <b>Создание встречи</b>
│   • /newmeet - новая встреча
│   • Пошаговый мастер создания
│
├─ 📋 <b>Мои встречи</b>  
│   • /my_meets - список встреч
│   • Просмотр и управление
│
├─ 👤 <b>Профиль</b>
│   • /profile - настройки
│   • Статистика и данные
│
└─ ℹ️ <b>Помощь</b>
    • /help - эта справка
    • /start - главное меню

━━━━━━━━━━━━━━━━━━━━

📋 <b>ПРАВИЛА СОЗДАНИЯ КОМНАТ</b>

⏰ <b>Временные ограничения:</b>
   ├─ • Минимально: 10 минут
   ├─ • Максимально: 10 часов
   └─ • Суммарно: ≤ 10 часов

━━━━━━━━━━━━━━━━━━━━

💡 <b>ПОДСКАЗКИ</b>
• Используйте кнопки для удобства
• Проверяйте данные перед сохранением
• Пароль можно изменить позже

❓ <b>ПОДДЕРЖКА</b>
Если есть вопросы: @E_t0chka
    """.strip()

    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())