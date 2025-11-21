from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from database import db
from keyboards import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

router = Router()

class MeetDetails(StatesGroup):
    waiting_for_meet_choice = State()

def get_meets_keyboard(meets):
    """Клавиатура для выбора встречи"""
    keyboard = []
    for meet in meets:
        meet_id, title, date, description, start_time, password, created_at = meet
        button_text = f"📋 {title} ({date})"
        keyboard.append([KeyboardButton(text=button_text)])
    
    keyboard.append([KeyboardButton(text="↩️ Назад к меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(Command("my_meets"))
@router.message(lambda message: message.text == "📋 Мои встречи")
async def cmd_my_meets(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        meets = await db.get_user_meets(user_id)
        
        if not meets:
            await message.answer(
                "📋 У вас пока нет созданных встреч.\n\n"
                "Создайте первую встречу с помощью команды /newmeet",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Сохраняем встречи в состоянии
        await state.update_data(meets=meets)
        
        meets_text = "📋 <b>Ваши встречи:</b>\n\n"
        
        for i, meet in enumerate(meets, 1):
            meet_id, title, date, description, start_time, password, created_at = meet
            password_status = "🔓" if not password else "🔐"
            
            meets_text += (
                f"<b>{i}. {title}</b>\n"
                f"   📅 {date} ⏰ {start_time} {password_status}\n"
                f"   🆔 ID: <code>{meet_id}</code>\n\n"
            )
        
        await message.answer(
            meets_text + "Выберите встречу для просмотра деталей:",
            parse_mode="HTML",
            reply_markup=get_meets_keyboard(meets)
        )
        
        await state.set_state(MeetDetails.waiting_for_meet_choice)
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_my_meets: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке встреч. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

@router.message(MeetDetails.waiting_for_meet_choice)
async def process_meet_choice(message: Message, state: FSMContext):
    try:
        if message.text == "↩️ Назад к меню":
            await state.clear()
            await message.answer("🏠 Главное меню:", reply_markup=get_main_keyboard())
            return
        
        data = await state.get_data()
        meets = data.get('meets', [])
        
        selected_meet = None
        for meet in meets:
            meet_id, title, date, description, start_time, password, created_at = meet
            if message.text.startswith(f"📋 {title} ({date})"):
                selected_meet = meet
                break
        
        if not selected_meet:
            await message.answer(
                "❌ Пожалуйста, выберите встречу из списка:",
                reply_markup=get_meets_keyboard(meets)
            )
            return
        
        meet_id, title, date, description, start_time, password, created_at = selected_meet
        
        # Получаем детальную информацию о встрече
        rooms = await db.get_meet_rooms(meet_id)
        
        if not rooms:
            meet_detail = (
                f"📊 <b>Детали встречи:</b> {title}\n"
                f"📅 {date} ⏰ {start_time}\n"
                f"📝 {description}\n\n"
                f"❌ Нет созданных комнат\n"
                f"🆔 ID для записи: <code>{meet_id}</code>"
            )
        else:
            meet_detail = f"📊 <b>Детали встречи:</b> {title}\n"
            meet_detail += f"📅 {date} ⏰ {start_time}\n"
            meet_detail += f"📝 {description}\n\n"
            meet_detail += f"🏠 <b>Комнаты:</b>\n"
            
            total_participants = 0
            total_capacity = 0
            
            for room in rooms:
                room_id, room_number, room_start, room_end, max_participants, current_participants = room
                
                total_participants += current_participants
                total_capacity += max_participants
                
                participants = await db.get_room_participants(room_id)
                
                meet_detail += f"\n<b>Комната {room_number}</b> ({room_start}-{room_end})\n"
                meet_detail += f"   👥 {current_participants}/{max_participants} участников\n"
                
                if participants:
                    meet_detail += "   📝 Записались:\n"
                    for j, participant in enumerate(participants, 1):
                        username, joined_at = participant
                        join_time = joined_at.split(' ')[1][:5] if ' ' in joined_at else joined_at[:5]
                        meet_detail += f"      {j}. {username} ({join_time})\n"
                else:
                    meet_detail += "   📝 Пока никто не записался\n"
            
            meet_detail += f"\n📈 <b>Итого по встрече:</b>\n"
            meet_detail += f"   👥 Участников: {total_participants}/{total_capacity}\n"
            meet_detail += f"   🏠 Комнат: {len(rooms)}\n"
            meet_detail += f"   🆔 ID для записи: <code>{meet_id}</code>"
        
        await message.answer(meet_detail, parse_mode="HTML")
        
        # Предлагаем посмотреть другую встречу
        await message.answer(
            "Выберите другую встречу или вернитесь в меню:",
            reply_markup=get_meets_keyboard(meets)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в process_meet_choice: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )