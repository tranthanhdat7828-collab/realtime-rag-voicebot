import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list()
    print("Danh sách model tài khoản bạn có quyền dùng:")
    for model in models.data:
        print(f" - {model.id}")
except Exception as e:
    print(f"Lỗi API Key hoặc mạng: {e}")
