from dotenv import load_dotenv
import os

# Загружаем переменные из .env файла
load_dotenv()


class Config:
    # Основные настройки бота
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

    # Настройки API
    API_URL = os.getenv('API_URL')
    API_KEY = os.getenv('API_KEY')

    # Настройки приложения
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

    # Проверка обязательных переменных
    @classmethod
    def validate(cls):
        required_vars = ['BOT_TOKEN', 'API_URL', 'API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}")


# Валидируем конфиг при импорте
Config.validate()