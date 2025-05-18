from datetime import datetime
import random

class ApiClient:
    def __init__(self):
        self.news_storage = []
        self.schedule_storage = {
            'last_updated': None,
            'data': "Расписание не задано"
        }

    def add_news(self, title, content, image_url=None):
        new_news = {
            'id': random.randint(1000, 9999),
            'title': title,
            'content': content,
            'image_url': image_url,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.news_storage.append(new_news)
        return {"status": "success", "id": new_news['id']}

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