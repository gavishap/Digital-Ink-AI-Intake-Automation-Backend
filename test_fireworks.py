"""Quick test to verify Fireworks API access with Qwen2.5-VL."""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("FIREWORKS_API_KEY")
if not api_key:
    print("FIREWORKS_API_KEY not found in .env")
    exit(1)

print(f"API key found: {api_key[:8]}...{api_key[-4:]}")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.fireworks.ai/inference/v1",
)

print("Sending test request to Qwen2.5-VL...")
response = client.chat.completions.create(
    model="accounts/fireworks/models/qwen2p5-vl-32b-instruct",
    messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
    max_tokens=10,
)

print(f"Response: {response.choices[0].message.content}")
print("Fireworks API connection successful!")
