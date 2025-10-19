from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

router = Router()

@router.message(Command("qr"))
async def cmd_qr(message: Message):
    try:
        photo = FSInputFile("image.png")
        
        await message.answer_photo(
            photo=photo,
            caption="📷 QR-изображение:"
        )
    except FileNotFoundError:
        await message.answer("❌ Файл image.png не найден в корне приложения")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при отправке фото: {str(e)}")