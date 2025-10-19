from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import db
from keyboards import get_main_keyboard

router = Router()

@router.message(Command("my_meets"))
@router.message(lambda message: message.text == "📋 Мои встречи")
async def cmd_my_meets(message: Message):
    meets = await db.get_user_meets(message.from_user.id)
    
    if not meets:
        await message.answer(
            "📋 У вас пока нет созданных встреч.\n\n"
            "Создайте первую встречу с помощью команды /newmeet",
            reply_markup=get_main_keyboard()
        )
        return
    
    meets_text = "📋 <b>Ваши встречи:</b>\n\n"
    
    for meet in meets:
        meet_id, title, date, description, plan, password, created_at = meet
        password_status = "🔓 без пароля" if not password else "🔐 с паролем"
        
        meets_text += (
            f"📝 <b>{title}</b>\n"
            f"📅 Дата: {date}\n"
            f"🔐 Доступ: {password_status}\n"
            f"🆔 ID: <code>{meet_id}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
    
    await message.answer(meets_text, parse_mode="HTML", reply_markup=get_main_keyboard())