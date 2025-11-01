import os
from ollama import Client

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + '118347b4d2404a13ad59ea034ea6c88e.y3rHTTlshlZgTcmr8Riqh5Sb'}
)

try:
    resp = client.chat('qwen3-coder:480b-cloud', messages=[{'role':'user','content':'Hello'}])
    print("✅ Success:", resp)
except Exception as e:
    print("❌ Error:", e)
