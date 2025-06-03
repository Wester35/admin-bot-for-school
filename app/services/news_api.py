from pathlib import Path

import aiohttp
from config import config

API_LIST_URL = f"{config.API_BASE}/news"
API_UPLOAD_URL = f"{config.API_BASE}/news/add"

async def fetch_news_list():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_LIST_URL) as response:
            return await response.json()

async def fetch_news_by_id(news_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:41235/news/{news_id}") as resp:
            resp.raise_for_status()
            try:
                return await resp.json(content_type=None)
            except aiohttp.ContentTypeError:
                text = await resp.text()
                import json
                try:
                    return json.loads(text)
                except Exception:
                    return {"text": text}


async def upload_news_to_api(title, content, files: list[Path]):
    form = aiohttp.FormData()
    form.add_field("title", title)
    form.add_field("content", content)

    for photo_path in files:
        form.add_field(
            "files",
            open(photo_path, "rb"),
            filename=photo_path.name,
            content_type="image/jpeg"
        )

    async with aiohttp.ClientSession() as session:
        async with session.put(API_UPLOAD_URL, data=form) as response:
            return response.status, await response.text()
