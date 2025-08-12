import requests
import base64
import os

# Настройки
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
model_key = "qwen2-v1-2b-instruct"

user_prompt = (
    "translate this text to Romanian:\n"
    "input: hello world\n"
    "output: translated text. NOTHING MORE"
)
system_prompt = (
    "You are a translation engine. Translate the user's input into Romanian. "
    "Respond with ONLY the translated text. Do not add any explanations, greetings, or formatting."
)


# Формируем запрос
payload = {
    "model": model_key,
    "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ],
    "temperature": 0.8,
    "max_tokens": 512,
    "stream": False
}


# Отправка запроса
response = requests.post(LMSTUDIO_API, json=payload)

# Вывод результата
if response.status_code == 200:
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print("📸 Translated text:\n")
    print(reply)
else:
    print(f"❌ Ошибка от LM Studio: {response.status_code}\n{response.text}")
