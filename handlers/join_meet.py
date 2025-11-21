from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from keyboards import get_main_keyboard, get_rooms_keyboard, get_cancel_keyboard
from database import db
import logging

logger = logging.getLogger(__name__)

router = Router()

class JoinMeet(StatesGroup):
    waiting_for_meet_id = State()        
    waiting_for_password = State()       
    waiting_for_room_choice = State()    

@router.message(Command("join"))
@router.message(lambda message: message.text == "📝 Записаться на встречу")
async def cmd_join_meet(message: Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer(
            "📝 Запись на встречу\n\n"
            "🆔 Введите ID встречи:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(JoinMeet.waiting_for_meet_id)
    except Exception as e:
        logger.error(f"Ошибка в cmd_join_meet: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=get_main_keyboard())

@router.message(JoinMeet.waiting_for_meet_id)
async def process_meet_id(message: Message, state: FSMContext):
    try:
        if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
            await cancel_join(message, state)
            return
        
        meet_id = int(message.text.strip())
        
        meet = await db.get_meet_by_id(meet_id)
        
        if not meet:
            await message.answer(
                "❌ Встреча с таким ID не найдена.\n\n"
                "Проверьте ID и попробуйте снова:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        is_active = await db.is_meet_active(meet_id)
        if not is_active:
            await message.answer(
                "❌ Эта встреча уже завершена или отменена.\n\n"
                "Выберите другую встречу:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        meet_data = {
            'meet_id': meet_id,
            'title': meet[1],
            'date': meet[2],
            'description': meet[3],
            'start_time': meet[4],
            'password': meet[5],
            'user_id': meet[6]
        }
        
        await state.update_data(meet_data=meet_data)
        
        if meet_data['password']:
            await message.answer(
                f"🔐 Эта встреча защищена паролем.\n\n"
                f"📝 <b>Название:</b> {meet_data['title']}\n"
                f"📅 <b>Дата:</b> {meet_data['date']}\n\n"
                "Введите пароль для доступа:",
                parse_mode="HTML",
                reply_markup=get_cancel_keyboard()
            )
            await state.set_state(JoinMeet.waiting_for_password)
        else:
            await show_available_rooms(message, state, meet_id)
            
    except ValueError:
        await message.answer(
            "❌ ID встречи должен быть числом.\n\n"
            "Введите ID снова:",
            reply_markup=get_cancel_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в process_meet_id: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=get_main_keyboard())

@router.message(JoinMeet.waiting_for_password)
async def process_meet_password(message: Message, state: FSMContext):
    try:
        if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
            await cancel_join(message, state)
            return
        
        data = await state.get_data()
        meet_data = data['meet_data']
        
        if message.text.strip() != meet_data['password']:
            await message.answer(
                "❌ Неверный пароль.\n\n"
                "Введите пароль снова:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await message.answer("✅ Пароль верный!")
        await show_available_rooms(message, state, meet_data['meet_id'])
    except Exception as e:
        logger.error(f"Ошибка в process_meet_password: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=get_main_keyboard())

async def show_available_rooms(message: Message, state: FSMContext, meet_id: int):
    try:
        rooms = await db.get_meet_rooms(meet_id)
        
        if not rooms:
            await message.answer(
                "❌ Для этой встречи нет доступных комнат.\n\n"
                "Возможно, все комнаты уже заполнены или встреча отменена.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        available_rooms = []
        for room in rooms:
            room_id, room_number, start_time, end_time, max_participants, current_participants = room
            if current_participants < max_participants:
                available_rooms.append(room)
        
        if not available_rooms:
            await message.answer(
                "❌ Во всех комнатах этой встречи нет свободных мест.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        data = await state.get_data()
        meet_data = data['meet_data']
        
        rooms_info = "\n".join([
            f"🏠 Комната {room[1]}: {room[2]}-{room[3]}"
            for room in available_rooms[:5]  
        ])
        
        if len(available_rooms) > 5:
            rooms_info += f"\n... и еще {len(available_rooms) - 5} комнат"
        
        await message.answer(
            f"📋 <b>Доступные комнаты:</b>\n\n"
            f"📝 {meet_data['title']}\n"
            f"📅 {meet_data['date']} {meet_data['start_time']}\n\n"
            f"{rooms_info}\n\n"
            "Выберите комнату:",
            parse_mode="HTML",
            reply_markup=get_rooms_keyboard(available_rooms)
        )
        
        await state.update_data(available_rooms=available_rooms)
        await state.set_state(JoinMeet.waiting_for_room_choice)
    except Exception as e:
        logger.error(f"Ошибка в show_available_rooms: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=get_main_keyboard())

@router.message(JoinMeet.waiting_for_room_choice)
async def process_room_choice(message: Message, state: FSMContext):
    try:
        if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
            await cancel_join(message, state)
            return
        
        data = await state.get_data()
        available_rooms = data.get('available_rooms', [])
        
        selected_room = None
        for room in available_rooms:
            room_id, room_number, start_time, end_time, max_participants, current_participants = room

            if message.text.startswith(f"🏠 Комната {room_number}"):
                selected_room = room
                break
        
        if not selected_room:
            await message.answer(
                "❌ Пожалуйста, выберите комнату из предложенных вариантов:",
                reply_markup=get_rooms_keyboard(available_rooms)
            )
            return
        
        room_id, room_number, start_time, end_time, max_participants, current_participants = selected_room
        
        user_name = message.from_user.full_name or f"User_{message.from_user.id}"
        success, result_message = await db.join_room(room_id, message.from_user.id, user_name)
        
        if success:
            await message.answer(
                f"🎉 Вы успешно записались!\n\n"
                f"📝 {data['meet_data']['title']}\n"
                f"🏠 Комната {room_number}\n"
                f"⏰ {start_time}-{end_time}\n"
                f"👥 {current_participants + 1}/{max_participants}",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ {result_message}",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в process_room_choice: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=get_main_keyboard())

async def cancel_join(message: Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer(
            "❌ Запись отменена.\n\n"
            "🏠 Главное меню:",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в cancel_join: {e}")

@router.message(lambda message: message.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    try:
        await cancel_join(message, state)
    except Exception as e:
        logger.error(f"Ошибка в cancel_handler: {e}")