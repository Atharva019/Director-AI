import asyncio
import httpx
from config import get_settings

async def test():
    settings = get_settings()
    api_key = settings.GROQ_API_KEY
    if not api_key or "your_" in api_key:
        print("API key not set correctly.")
        return

    # Tiny 1x1 transparent GIF in base64, but we'll say jpeg to match our code
    tiny_b64 = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    
    body = {
        "model": settings.GROQ_DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is this?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{tiny_b64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.4
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=body)
        print("Status:", res.status_code)
        print("Body:", res.text)

asyncio.run(test())
