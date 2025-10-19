from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from keyboards import get_main_keyboard, get_password_choice_keyboard, get_confirmation_keyboard
from database import db

router = Router()

# Определяем состояния для создания встречи
class CreateMeet(StatesGroup):
    waiting_for_title = State()       # Ожидаем название встречи
    waiting_for_date = State()        # Ожидаем дату
    waiting_for_description = State() # Ожидаем описание
    waiting_for_plan = State()        # Ожидаем расписание 
    waiting_for_password_choice = State() # Выбор режима пароля
    waiting_for_password_input = State() # Ввод пароля
    waiting_for_confirmation = State() # Ожидаем подтверждение

@router.message(Command("newmeet"))
@router.message(lambda message: message.text == "🗓 Новая встреча")
async def cmd_newmeet(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🗓️ Создание новой встречи...\n\n"
        "📝 Введите название встречи:",
        reply_markup=None
    )
    await state.set_state(CreateMeet.waiting_for_title)

@router.message(CreateMeet.waiting_for_title)
async def process_meet_title(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
        
    await state.update_data(title=message.text)
    
    await message.answer(
        f"✅ Название сохранено: <b>{message.text}</b>\n\n"
        "📅 Теперь введите дату встречи (например: 25.12.2024):",
        parse_mode="HTML"
    )
    await state.set_state(CreateMeet.waiting_for_date)

@router.message(CreateMeet.waiting_for_date)
async def process_meet_date(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
        
    await state.update_data(date=message.text)
    
    await message.answer(
        f"✅ Дата сохранена: <b>{message.text}</b>\n\n"
        "📋 Теперь введите описание встречи:",
        parse_mode="HTML"
    )
    await state.set_state(CreateMeet.waiting_for_description)

@router.message(CreateMeet.waiting_for_description)
async def process_meet_description(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
        
    await state.update_data(description=message.text)
    
    await message.answer(
        f"✅ Описание сохранено\n\n"
        "📋 Введите план встречи:\n",
        parse_mode="HTML"
    )
    await state.set_state(CreateMeet.waiting_for_plan)

@router.message(CreateMeet.waiting_for_plan)
async def process_meet_plan(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
    
    # Обрабатываем ввод плана
    if message.text.strip() == '-':
        plan = "Не указан"
        plan_text = "❌ не указан"
    else:
        plan = message.text.strip()
        plan_text = f"✅ {plan}"
    
    await state.update_data(plan=plan, plan_text=plan_text)
    
    await message.answer(
        f"✅ План сохранен\n\n"
        "🔐 Выберите тип доступа к встрече:",
        reply_markup=get_password_choice_keyboard()
    )
    await state.set_state(CreateMeet.waiting_for_password_choice)

@router.message(CreateMeet.waiting_for_password_choice)
async def process_password_choice(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
        
    if message.text == "🔓 Без пароля":
        # Если без пароля - сразу переходим к подтверждению
        await state.update_data(password=None, password_text="🔓 без пароля")
        await show_confirmation(message, state)
        
    elif message.text == "🔐 С паролем":
        # Если с паролем - запрашиваем ввод пароля
        await message.answer(
            "🔐 Введите пароль для встречи:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="↩️ Назад к меню")]],
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
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
        
    password = message.text.strip()
    if not password:
        await message.answer(
            "❌ Пароль не может быть пустым. Введите пароль:"
        )
        return
    
    await state.update_data(password=password, password_text=f"🔐 {password}")
    await show_confirmation(message, state)

async def show_confirmation(message: Message, state: FSMContext):
    # Получаем все сохраненные данные
    data = await state.get_data()
    
    # Формируем итоговое сообщение для подтверждения
    meet_info = (
        "📋 <b>Проверьте данные встречи:</b>\n\n"
        f"📝 <b>Название:</b> {data['title']}\n"
        f"📅 <b>Дата:</b> {data['date']}\n"
        f"📋 <b>Описание:</b> {data['description']}\n"
        f"📋 <b>План:</b> {data['plan_text']}\n"
        f"🔐 <b>Пароль:</b> {data['password_text']}\n\n"
        "<b>Всё верно?</b>"
    )
    
    await message.answer(meet_info, parse_mode="HTML", reply_markup=get_confirmation_keyboard())
    await state.set_state(CreateMeet.waiting_for_confirmation)

@router.message(CreateMeet.waiting_for_confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    if message.text in ["↩️ Назад к меню", "🏠 Главное меню"]:
        await back_to_menu(message, state)
        return
        
    if message.text == "✅ Да, всё верно":
        # Получаем данные из состояния
        data = await state.get_data()
        
        # Сохраняем встречу в базу данных
        meet_id = await db.add_meet(
            user_id=message.from_user.id,
            title=data['title'],
            date=data['date'],
            description=data['description'],
            plan=data['plan'],
            password=data.get('password')
        )
        
        if meet_id:
            await message.answer(
                f"🎉 Встреча <b>«{data['title']}»</b> создана успешно!\n\n"
                "✅ Все данные сохранены в базе!",
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
            reply_markup=None
        )
        await state.set_state(CreateMeet.waiting_for_title)
    else:
        await message.answer(
            "Пожалуйста, выберите вариант с клавиатуры:",
            reply_markup=get_confirmation_keyboard()
        )

# Функция возврата в главное меню
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_keyboard()
    )

# Обработчик для кнопки "Назад к меню"
@router.message(lambda message: message.text == "↩️ Назад к меню")
async def back_to_menu_handler(message: Message, state: FSMContext):
    await back_to_menu(message, state)