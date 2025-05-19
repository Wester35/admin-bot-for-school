import os
import shutil
import uuid
from datetime import datetime
import random

class ApiClient:
    def __init__(self):
        self.news_storage = []
        self.schedule_storage = {
            'last_updated': None,
            'data': "Расписание не задано"
        }

        self.upload_dir = "uploaded_news"

        os.makedirs(self.upload_dir, exist_ok=True)

    def add_news(self, title: str, content: str, photos: list = None):
        # Переносим фото в постоянное хранилище
        saved_photos = []
        for photo_path in photos or []:
            if os.path.exists(photo_path):
                filename = f"{uuid.uuid4()}.jpg"
                new_path = os.path.join(self.upload_dir, filename)
                shutil.move(photo_path, new_path)  # Перемещаем, а не копируем
                saved_photos.append(new_path)

        new_news = {
            'id': len(self.news_storage) + 1,  # Простая нумерация
            'title': title,
            'content': content,
            'photos': saved_photos,
            'created_at': datetime.now().strftime("%d.%m.%Y %H:%M")  # Более читаемый формат
        }
        self.news_storage.append(new_news)
        return new_news  # Возвращаем всю новость

    def get_news(self):
        return {'news': self.news_storage.copy()}

    def update_schedule(self, schedule_data):
        self.schedule_storage = {
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'data': schedule_data
        }
        return {"status": "success"}

    def get_news(self):
        return {"news": self.news_storage}

    def get_schedule(self):
        return self.schedule_storage

    def clear_all(self):  # Для тестирования
        self.news_storage = []
        self.schedule_storage = {
            'last_updated': None,
            'data': "Расписание не задано"
        }