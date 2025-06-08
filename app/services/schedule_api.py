from pathlib import Path
import aiohttp

SCHEDULE_URL = "http://localhost:12543"

async def upload_schedule_to_api(file: Path):
    form = aiohttp.FormData()
    form.add_field(
        "file",
        open(file, "rb"),
        filename=file.name,
        content_type="image/jpeg" if file.suffix.lower() == ".jpg" else "image/png"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SCHEDULE_URL}/upload", data=form) as response:
            return response.status, await response.text()

async def fetch_schedule():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SCHEDULE_URL}/schedule") as resp:
            if resp.status == 200:
                content = await resp.read()
                content_type = resp.headers.get("Content-Type", "application/octet-stream")
                return content, content_type
            else:
                return None, None
