import logging
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, ADMIN_IDS
from api_client import ApiClient
from keyboards import get_main_menu, get_news_menu, get_schedule_menu
from config import Config

# Использование конфига в коде
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher(bot)

def is_admin(user_id):
    return user_id in Config.ADMIN_IDS

logging.basicConfig(level=logging.INFO)


api = ApiClient()


# Проверка прав администратора
def is_admin(user_id):
    return user_id in ADMIN_IDS


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("Доступ запрещен")
        return

    await message.reply("Добро пожаловать в админ-панель!", reply_markup=get_main_menu())


@dp.message_handler(lambda message: message.text == 'Новости')
async def news_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Управление новостями:", reply_markup=get_news_menu())


@dp.message_handler(lambda message: message.text == 'Расписание')
async def schedule_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("Управление расписанием:", reply_markup=get_schedule_menu())


@dp.callback_query_handler(lambda c: c.data == 'add_news')
async def add_news_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите заголовок новости:")


@dp.message_handler(
    lambda message: message.reply_to_message and message.reply_to_message.text == "Введите заголовок новости:")
async def process_news_title(message: types.Message):
    title = message.text
    await message.reply("Теперь введите содержание новости:")
    # Здесь можно сохранить title в состоянии (например, в словаре)


@dp.message_handler(
    lambda message: message.reply_to_message and message.reply_to_message.text == "Теперь введите содержание новости:")
async def process_news_content(message: types.Message):
    content = message.text
    # Получаем сохраненный title из состояния
    # result = api.add_news(title, content)
    await message.reply("Новость успешно добавлена!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)