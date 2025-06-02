import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    @property
    def BOT_TOKEN(self):
        return os.getenv('BOT_TOKEN', 'fake_bot_token_123')

    @property
    def ADMIN_IDS(self):
        ids = os.getenv('ADMIN_IDS', '').split(',')
        return [int(id.strip()) for id in ids if id.strip().isdigit()]

    def validate(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан")
        if not self.ADMIN_IDS:
            raise ValueError("ADMIN_IDS не заданы")

    @property
    def API_BASE(self):
        return "http://localhost:41235"


config = Config()
config.validate()