import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from database import Database

# Загрузка переменных из .env
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
LOW_STOCK_THRESHOLD = 4  # Уведомление, если количество меньше 4
DB_PATH = "inventory.db"

# Логирование
logging.basicConfig(level=logging.INFO)
db = Database(DB_PATH)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Кнопки меню
menu_guest = ReplyKeyboardMarkup(resize_keyboard=True)
menu_guest.add(KeyboardButton("Посмотреть остатки"))

menu_admin = ReplyKeyboardMarkup(resize_keyboard=True)
menu_admin.add(
    KeyboardButton("Посмотреть остатки"),
    KeyboardButton("Добавить позицию"),
    KeyboardButton("Редактировать позицию"),
    KeyboardButton("Удалить позицию"),
)


# Проверка прав администратора
def is_admin(user_id):
    return user_id in ADMIN_IDS


# Формирование таблицы остатков
def format_inventory(inventory):
    response = ""
    for section, items in inventory.items():
        response += f"📦 <b>{section}</b>\n"
        for item, quantity in items:
            color = "🔴" if quantity < LOW_STOCK_THRESHOLD else "🟢"
            response += f" {color} {item} — {quantity} шт.\n"
        response += "\n"
    return response if response else "Нет данных о складе."


# Хэндлер для команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "Добро пожаловать, администратор! Выберите действие:", reply_markup=menu_admin
        )
    else:
        await message.answer(
            "Добро пожаловать! Вы можете только просматривать остатки.",
            reply_markup=menu_guest,
        )


# Хэндлер для просмотра остатков
@dp.message_handler(lambda message: message.text == "Посмотреть остатки")
async def view_inventory(message: types.Message):
    inventory = db.get_inventory()
    response = format_inventory(inventory)
    await message.answer(response, parse_mode="HTML")


# Хэндлер для добавления позиции
@dp.message_handler(lambda message: message.text == "Добавить позицию" and is_admin(message.from_user.id))
async def add_item_prompt(message: types.Message):
    await message.answer("Введите данные в формате: Раздел, Название, Количество")


@dp.message_handler(lambda message: is_admin(message.from_user.id))
async def add_item(message: types.Message):
    if "," in message.text:
        try:
            section, item, quantity = map(str.strip, message.text.split(","))
            quantity = int(quantity)
            db.add_item(section, item, quantity)
            await message.answer(f"Позиция {item} успешно добавлена в раздел {section}.")
        except ValueError:
            await message.answer("Ошибка: Неверный формат данных. Попробуйте снова.")
    else:
        await message.answer("Для добавления используйте формат: Раздел, Название, Количество")


# Хэндлер для редактирования позиции
@dp.message_handler(lambda message: message.text == "Редактировать позицию" and is_admin(message.from_user.id))
async def edit_item_prompt(message: types.Message):
    await message.answer("Введите данные в формате: Название, Новое количество")


@dp.message_handler(lambda message: is_admin(message.from_user.id))
async def edit_item(message: types.Message):
    if "," in message.text:
        try:
            item, quantity = map(str.strip, message.text.split(","))
            quantity = int(quantity)
            db.update_item(item, quantity)
            await message.answer(f"Количество для {item} успешно обновлено до {quantity}.")
        except ValueError:
            await message.answer("Ошибка: Неверный формат данных. Попробуйте снова.")
    else:
        await message.answer("Для редактирования используйте формат: Название, Новое количество")


# Хэндлер для удаления позиции
@dp.message_handler(lambda message: message.text == "Удалить позицию" and is_admin(message.from_user.id))
async def delete_item_prompt(message: types.Message):
    await message.answer("Введите название позиции для удаления.")


@dp.message_handler(lambda message: is_admin(message.from_user.id))
async def delete_item(message: types.Message):
    item = message.text.strip()
    db.delete_item(item)
    await message.answer(f"Позиция {item} успешно удалена.")


# Обработка всех остальных сообщений
@dp.message_handler()
async def handle_unknown(message: types.Message):
    await message.answer("Я не понимаю эту команду. Используйте меню для взаимодействия с ботом.")


# Запуск бота
if __name__ == "__main__":
    from aiogram import executor

    try:
        executor.start_polling(dp, skip_updates=True)
    finally:
        db.close()