import json
from io import BytesIO
import aiohttp
from config import config

API_LIST_URL = f"{config.API_BASE}/news"
API_UPLOAD_URL = f"{config.API_BASE}/news/add"


async def create_news_in_api(title: str, content: str, files: list[tuple[BytesIO, str]]):
    form = aiohttp.FormData()
    form.add_field("title", title)
    form.add_field("content", content)

    for file_obj, filename in files:
        file_obj.seek(0)
        form.add_field(
            "files",
            file_obj,
            filename=filename,
            content_type="image/jpeg"
        )

    async with aiohttp.ClientSession() as session:
        async with session.put(API_UPLOAD_URL, data=form) as response:
            return response.status, await response.text()

async def upload_news_to_api(news_id: int, title: str, content: str, files: list[tuple[BytesIO, str]]):
    form = aiohttp.FormData()
    form.add_field("title", title)
    form.add_field("content", content)

    for file_obj, filename in files:
        file_obj.seek(0)
        form.add_field(
            "files",
            file_obj,
            filename=filename,
            content_type="image/jpeg"
        )

    async with aiohttp.ClientSession() as session:
        url = f"{config.API_BASE}/news/update/{news_id}"
        async with session.patch(url, data=form) as response:
            return response.status, await response.text()



async def fetch_news_list():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_LIST_URL) as response:
            return await response.json()

# async def fetch_news_by_id(news_id):
#     async with aiohttp.ClientSession() as session:
#         async with session.get(f"http://localhost:41235/news/{news_id}") as resp:
#             resp.raise_for_status()
#             try:
#                 return await resp.json(content_type=None)
#             except aiohttp.ContentTypeError:
#                 text = await resp.text()
#                 import json
#                 try:
#                     return json.loads(text)
#                 except Exception:
#                     return {"text": text}
async def fetch_news_by_id(news_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_LIST_URL}/{news_id}") as resp:
            resp.raise_for_status()
            try:
                news = await resp.json(content_type=None)
            except aiohttp.ContentTypeError:
                text = await resp.text()
                try:
                    news = json.loads(text)
                except Exception:
                    return {"text": text}

        images = []
        for image_info in news.get("images", []):
            image_name = image_info.get("name_image")
            if image_name:
                img_url = f"{API_LIST_URL}/img/{image_name}"
                async with session.get(img_url) as img_resp:
                    img_resp.raise_for_status()
                    img_bytes = await img_resp.read()
                    images.append({
                        "filename": image_name,
                        "bytes": img_bytes
                    })

        news["loaded_images"] = images
        return news
