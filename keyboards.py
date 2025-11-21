from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Основная клавиатура с командами
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗓 Новая встреча"), KeyboardButton(text="📋 Мои встречи")],
            [KeyboardButton(text="📝 Записаться на встречу"), KeyboardButton(text="📖 Мои записи")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        persistent=True
    )

# Клавиатура для выбора пароля
def get_password_choice_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 С паролем"), KeyboardButton(text="🔓 Без пароля")],
            [KeyboardButton(text="↩️ Назад к меню")]
        ],
        resize_keyboard=True
    )

# Клавиатура для подтверждения
def get_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, всё верно"), KeyboardButton(text="❌ Нет, исправить")],
            [KeyboardButton(text="↩️ Назад к меню")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_rooms_keyboard(rooms):
    keyboard = []
    for room in rooms:
        room_id, room_number, start_time, end_time, max_participants, current_participants = room
        free_slots = max_participants - current_participants
        
        if free_slots == 1:
            slots_text = "1 место"
        elif free_slots < 5:
            slots_text = f"{free_slots} места"
        else:
            slots_text = f"{free_slots} мест"
            
        button_text = f"🏠 Комната {room_number} ({start_time}-{end_time}) - {slots_text}"
        keyboard.append([KeyboardButton(text=button_text)])
    
    keyboard.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)