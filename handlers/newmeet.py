from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from keyboards import get_main_keyboard, get_password_choice_keyboard, get_confirmation_keyboard
from database import db
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

router = Router()

class CreateMeet(StatesGroup):
    waiting_for_title = State()           
    waiting_for_date = State()            
    waiting_for_start_time = State()      
    waiting_for_description = State()     
    waiting_for_rooms_count = State()    
    waiting_for_room_duration = State()   
    waiting_for_max_participants = State() 
    waiting_for_password_choice = State() 
    waiting_for_password_input = State()
    waiting_for_confirmation = State()

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def is_valid_date(date_string):
    try:
        date = datetime.strptime(date_string, '%d-%m-%Y')
        if date.date() < datetime.now().date():
            return False, "❌ Дата не может быть в прошлом"
        return True, date
    except ValueError:
        return False, "❌ Неверный формат даты. Используйте DD-MM-YYYY (например: 15-11-2024)"

def is_valid_time(time_string):
    try:
        time = datetime.strptime(time_string, '%H:%M')
        return True, time
    except ValueError:
        return False, "❌ Неверный формат времени. Используйте HH:MM (например: 17:00)"

def calculate_schedule(rooms_count, room_duration, start_time_str, date_str):
    try:
        start_datetime = datetime.strptime(f"{date_str} {start_time_str}", '%d-%m-%Y %H:%M')
        schedule = []
        
        current_time = start_datetime
        for i in range(rooms_count):
            end_time = current_time + timedelta(minutes=room_duration)
            schedule.append({
                'room_number': i + 1,
                'start_time': current_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M')
            })
            current_time = end_time
        
        return schedule
    except Exception as e:
        logger.error(f"Ошибка расчета расписания: {e}")
        return []

@router.message(Command("newmeet"))
@router.message(lambda message: message.text == "🗓 Новая встреча")
async def cmd_newmeet(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🗓️ Создание новой встречи...\n\n"
        "📝 Введите название встречи:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreateMeet.waiting_for_title)

@router.message(CreateMeet.waiting_for_title)
async def process_meet_title(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
        
    await state.update_data(title=message.text)
    
    await message.answer(
        f"✅ Название сохранено: <b>{message.text}</b>\n\n"
        "📅 Теперь введите дату встречи в формате DD-MM-YYYY:\n"
        "<i>Например: 25-12-2024</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreateMeet.waiting_for_date)

@router.message(CreateMeet.waiting_for_date)
async def process_meet_date(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
    
    is_valid, result = is_valid_date(message.text)
    if not is_valid:
        await message.answer(result + "\n\nВведите дату снова:", reply_markup=get_cancel_keyboard())
        return
        
    await state.update_data(date=message.text)
    
    await message.answer(
        f"✅ Дата сохранена: <b>{message.text}</b>\n\n"
        "⏰ Теперь введите время старта первой комнаты в формате HH:MM:\n"
        "<i>Например: 14:30</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreateMeet.waiting_for_start_time)

@router.message(CreateMeet.waiting_for_start_time)
async def process_start_time(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
    
    is_valid, result = is_valid_time(message.text)
    if not is_valid:
        await message.answer(result + "\n\nВведите время снова:", reply_markup=get_cancel_keyboard())
        return
        
    await state.update_data(start_time=message.text)
    
    await message.answer(
        f"✅ Время старта сохранено: <b>{message.text}</b>\n\n"
        "📋 Теперь введите описание встречи:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(CreateMeet.waiting_for_description)

@router.message(CreateMeet.waiting_for_description)
async def process_meet_description(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
        
    await state.update_data(description=message.text)
    
    rules_text = (
        "📋 <b>ПРАВИЛА СОЗДАНИЯ КОМНАТ</b>\n\n"
        "⏰ <b>Временные ограничения:</b>\n"
        "   ├─ • Минимально: 10 минут\n"
        "   ├─ • Максимально: 10 часов\n"
        "   └─ • Суммарно: ≤ 10 часов\n\n"
        "🏠 Введите количество комнат:"
    )
    
    await message.answer(rules_text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await state.set_state(CreateMeet.waiting_for_rooms_count)

@router.message(CreateMeet.waiting_for_rooms_count)
async def process_rooms_count(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
    
    try:
        rooms_count = int(message.text.strip())
        
        if rooms_count <= 0:
            await message.answer("❌ Количество комнат должно быть положительным числом. Введите снова:", reply_markup=get_cancel_keyboard())
            return
        
        max_rooms = 60  
        if rooms_count > max_rooms:
            await message.answer(f"❌ Слишком много комнат. Максимум {max_rooms} комнат. Введите снова:", reply_markup=get_cancel_keyboard())
            return
        
        await state.update_data(rooms_count=rooms_count)
        
        await message.answer(
            f"✅ Количество комнат: <b>{rooms_count}</b>\n\n"
            "⏱️ Теперь введите продолжительность одной комнаты в минутах:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(CreateMeet.waiting_for_room_duration)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 3):", reply_markup=get_cancel_keyboard())

@router.message(CreateMeet.waiting_for_room_duration)
async def process_room_duration(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
    
    try:
        room_duration = int(message.text.strip())
        
        if room_duration < 10:
            await message.answer("❌ Продолжительность комнаты должна быть не менее 10 минут. Введите снова:", reply_markup=get_cancel_keyboard())
            return
        
        if room_duration > 600: 
            await message.answer("❌ Продолжительность комнаты не может превышать 10 часов (600 минут). Введите снова:", reply_markup=get_cancel_keyboard())
            return
        
        data = await state.get_data()
        rooms_count = data['rooms_count']
        total_duration = rooms_count * room_duration
        
        if total_duration > 600: 
            max_rooms_for_duration = 600 // room_duration
            await message.answer(
                f"❌ Суммарное время встречи превышает 10 часов.\n"
                f"При продолжительности {room_duration} минут одной комнаты "
                f"максимум можно создать {max_rooms_for_duration} комнат.\n\n"
                "Введите меньшую продолжительность или уменьшите количество комнат:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await state.update_data(room_duration=room_duration)
        
        hours_total = total_duration // 60
        minutes_total = total_duration % 60
        time_display = f"{hours_total} ч {minutes_total} мин" if hours_total > 0 else f"{minutes_total} мин"
        
        await message.answer(
            f"✅ Продолжительность сохранена: <b>{room_duration} минут</b>\n"
            f"📊 Всего: {rooms_count} комнат × {room_duration} мин = {time_display}\n\n"
            "👥 Теперь введите максимальное количество участников в одной комнате:\n"
            "<i>Например: 1 (для индивидуальных встреч)</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(CreateMeet.waiting_for_max_participants)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число минут (например: 15):", reply_markup=get_cancel_keyboard())

@router.message(CreateMeet.waiting_for_max_participants)
async def process_max_participants(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
    
    try:
        max_participants = int(message.text.strip())
        
        if max_participants < 1:
            await message.answer("❌ Количество участников должно быть не менее 1. Введите снова:", reply_markup=get_cancel_keyboard())
            return
        
        if max_participants > 50:
            await message.answer("❌ Слишком много участников. Максимум 50 на комнату. Введите снова:", reply_markup=get_cancel_keyboard())
            return
        
        await state.update_data(max_participants=max_participants)
        
        await message.answer(
            f"✅ Максимальное количество участников: <b>{max_participants}</b>\n\n"
            "🔐 Выберите тип доступа к встрече:",
            parse_mode="HTML",
            reply_markup=get_password_choice_keyboard()
        )
        await state.set_state(CreateMeet.waiting_for_password_choice)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 1):", reply_markup=get_cancel_keyboard())

@router.message(CreateMeet.waiting_for_password_choice)
async def process_password_choice(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
        
    if message.text == "🔓 Без пароля":
        await state.update_data(password=None, password_text="🔓 без пароля")
        await show_confirmation(message, state)
        
    elif message.text == "🔐 С паролем":
        await message.answer(
            "🔐 Введите пароль для встречи:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="❌ Отмена")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(CreateMeet.waiting_for_password_input)
    else:
        await message.answer(
            "Пожалуйста, выберите вариант с клавиатуры:",
            reply_markup=get_password_choice_keyboard()
        )

@router.message(CreateMeet.waiting_for_password_input)
async def process_password_input(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
        
    password = message.text.strip()
    if not password:
        await message.answer(
            "❌ Пароль не может быть пустым. Введите пароль:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(password=password, password_text=f"🔐 {password}")
    await show_confirmation(message, state)

async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    
    schedule = calculate_schedule(
        data['rooms_count'], 
        data['room_duration'], 
        data['start_time'], 
        data['date']
    )
    
    rooms_info = f"{data['rooms_count']} комнат по {data['room_duration']} минут"
    total_minutes = data['rooms_count'] * data['room_duration']
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0:
        duration_text = f" ({hours} ч {minutes} мин)"
    else:
        duration_text = f" ({minutes} мин)"
    
    schedule_text = "\n".join([
        f"• Комната {room['room_number']}: {room['start_time']} - {room['end_time']}"
        for room in schedule
    ])
    
    meet_info = (
        "📋 <b>Проверьте данные встречи:</b>\n\n"
        f"📝 <b>Название:</b> {data['title']}\n"
        f"📅 <b>Дата:</b> {data['date']}\n"
        f"⏰ <b>Начало:</b> {data['start_time']}\n"
        f"📋 <b>Описание:</b> {data['description']}\n"
        f"🏠 <b>Комнаты:</b> {rooms_info}{duration_text}\n"
        f"👥 <b>Участников в комнате:</b> до {data['max_participants']} чел.\n\n"
        f"<b>📅 Расписание:</b>\n{schedule_text}\n\n"
        f"🔐 <b>Пароль:</b> {data['password_text']}\n\n"
        "<b>Всё верно?</b>"
    )
    
    await message.answer(meet_info, parse_mode="HTML", reply_markup=get_confirmation_keyboard())
    await state.set_state(CreateMeet.waiting_for_confirmation)

@router.message(CreateMeet.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню", "❌ Отмена"]:
        await cancel_creation(message, state)
        return
        
    if message.text == "✅ Да, всё верно":
        data = await state.get_data()
        
        schedule = calculate_schedule(
            data['rooms_count'], 
            data['room_duration'], 
            data['start_time'], 
            data['date']
        )
        
        if not schedule:
            await message.answer(
                "❌ Ошибка при расчете расписания. Проверьте введенные данные.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        meet_id, success = await db.add_meet_with_rooms(
            user_id=message.from_user.id,
            title=data['title'],
            date=data['date'],
            description=data['description'],
            start_time=data['start_time'],
            rooms_data=schedule,
            max_participants=data['max_participants'],
            password=data.get('password')
        )
        
        if meet_id and success:
            total_minutes = data['rooms_count'] * data['room_duration']
            hours = total_minutes // 60
            minutes = total_minutes % 60
            time_display = f"{hours} ч {minutes} мин" if hours > 0 else f"{minutes} мин"
            
            access_info = ""
            if data.get('password'):
                access_info = f"\n🔐 <b>Пароль для доступа:</b> {data['password']}"
            
            await message.answer(
                f"🎉 Встреча <b>«{data['title']}»</b> создана успешно!\n\n"
                f"🆔 <b>ID встречи:</b> {meet_id}\n"
                f"📅 <b>Дата:</b> {data['date']}\n"
                f"⏰ <b>Начало:</b> {data['start_time']}\n"
                f"🏠 <b>Комнаты:</b> {data['rooms_count']} × {data['room_duration']} мин\n"
                f"👥 <b>Участников в комнате:</b> до {data['max_participants']} чел.\n"
                f"⏱️ <b>Общее время:</b> {time_display}\n"
                f"{access_info}\n\n"
                "✅ Все данные сохранены в базе!\n\n"
                "📋 Участники могут записаться в комнаты с помощью ID встречи.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при сохранении встречи. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        
    elif message.text == "❌ Нет, исправить":
        await message.answer(
            "❌ Давайте начнем создание встречи заново.\n\n"
            "📝 Введите название встречи:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(CreateMeet.waiting_for_title)
    else:
        await message.answer(
            "Пожалуйста, выберите вариант с клавиатуры:",
            reply_markup=get_confirmation_keyboard()
        )

async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Создание встречи отменено.\n\n"
        "🏠 Возврат в главное меню:",
        reply_markup=get_main_keyboard()
    )

async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_keyboard()
    )

@router.message(lambda message: message.text == "↩️ Назад к меню")
async def back_to_menu_handler(message: Message, state: FSMContext):
    await back_to_menu(message, state)

@router.message(lambda message: message.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await cancel_creation(message, state)