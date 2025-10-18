from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Основная клавиатура с командами
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗓 Новая встреча"), KeyboardButton(text="📋 Мои встречи")],
            [KeyboardButton(text="ℹ️ Помощь"), KeyboardButton(text="👤 Профиль")]
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

# Клавиатура для отмены
def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )