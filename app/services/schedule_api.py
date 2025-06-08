from io import BytesIO
import aiohttp


SCHEDULE_URL = "http://localhost:12543"

async def upload_schedule_to_api(file_bytes: BytesIO, filename: str) -> tuple[int, str]:
    url = f"{SCHEDULE_URL}/upload"

    data = aiohttp.FormData()
    data.add_field(
        name="file",
        value=file_bytes,
        filename=filename,
        content_type="image/jpeg" if filename.endswith("jpg") or filename.endswith("jpeg") else "image/png"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            text = await response.text()
            return response.status, text


async def fetch_schedule():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SCHEDULE_URL}/schedule") as resp:
            if resp.status == 200:
                content = await resp.read()
                content_type = resp.headers.get("Content-Type", "application/octet-stream")
                return content, content_type
            else:
                return None, None
