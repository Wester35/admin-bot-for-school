import requests
from config import Config

class ApiClient:
    def __init__(self):
        self.base_url = Config.API_URL
        self.headers = {'Authorization': f'Bearer {Config.API_KEY}'}

    def add_news(self, title, content, image_url=None):
        data = {'title': title, 'content': content}
        if image_url:
            data['image_url'] = image_url
        response = requests.post(f'{self.base_url}/news', json=data, headers=self.headers)
        return response.json()

    def update_schedule(self, schedule_data):
        response = requests.put(f'{self.base_url}/schedule', json=schedule_data, headers=self.headers)
        return response.json()

    def get_news(self):
        response = requests.get(f'{self.base_url}/news', headers=self.headers)
        return response.json()

    def get_schedule(self):
        response = requests.get(f'{self.base_url}/schedule', headers=self.headers)
        return response.json()