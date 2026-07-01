import asyncio
import httpx
from config import get_settings
from services.nim_service import _normalize_api_key

async def test():
    settings = get_settings()
    api_key = _normalize_api_key(
        settings.NVIDIA_NIM_API_KEY or settings.GROQ_API_KEY
    )
    if not api_key or "your_" in api_key:
        print("API key not set correctly.")
        return

    tiny_b64 = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    model = settings.NVIDIA_NIM_DEFAULT_MODEL or settings.GROQ_DEFAULT_MODEL

    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is this?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{tiny_b64}"
                        },
                    },
                ],
            }
        ],
        "temperature": 0.4,
    }

    url = settings.NVIDIA_NIM_API_URL
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(url, headers=headers, json=body)
        print("Status:", res.status_code)
        print("Body:", res.text[:1000])

asyncio.run(test())
