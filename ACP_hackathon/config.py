import os
import httpx
from openai import OpenAI
http_client = httpx.Client(
    verify = False,
    timeout=60.0,
)

client = OpenAI(
    api_key = os.getenv("DEEPSEEK_API_KEY", "sk-3d784c54aa334377a27821fe1f4d0091"),
    base_url="https://api.deepseek.com/v1",
    http_client = http_client,
)