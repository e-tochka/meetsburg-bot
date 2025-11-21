from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database import db
from keyboards import get_main_keyboard
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("my_bookings"))
@router.message(lambda message: message.text == "📖 Мои записи")
async def cmd_my_bookings(message: Message):
    try:
        user_id = message.from_user.id
        bookings = await db.get_user_bookings(user_id)
        
        if not bookings:
            await message.answer(
                "📖 <b>Мои записи</b>\n\n"
                "❌ Вы еще не записаны ни на одну встречу.\n\n"
                "Используйте кнопку «📝 Записаться на встречу», чтобы найти интересные мероприятия.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            return
        
        if len(bookings) > 10:
            await message.answer(
                f"📖 <b>Ваши записи (первые 10 из {len(bookings)}):</b>\n\n",
                parse_mode="HTML"
            )
            bookings = bookings[:10]
        else:
            await message.answer("📖 <b>Ваши записи:</b>\n\n", parse_mode="HTML")
        
        for i, booking in enumerate(bookings, 1):
            meet_id, title, date, meet_start_time, room_number, room_start, room_end, joined_at = booking
            
            join_date = datetime.strptime(joined_at, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
            
            booking_text = (
                f"<b>{i}. {title}</b>\n"
                f"📅 {date} ⏰ {meet_start_time}\n"
                f"🏠 Комната {room_number} ({room_start}-{room_end})\n"
                f"📝 Записан: {join_date}\n"
                f"🆔 ID: {meet_id}\n"
            )
            
            await message.answer(booking_text, parse_mode="HTML")
            await asyncio.sleep(0.5)
        
        await message.answer(
            "📖 Это все ваши текущие записи.",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_my_bookings: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке записей. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )