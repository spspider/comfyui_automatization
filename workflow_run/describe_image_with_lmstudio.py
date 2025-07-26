import requests
import base64
import os

# Настройки
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"
model_key = "qwen2-vl-2b-instruct"
image_path = os.path.abspath("gen/input.jpeg")

user_prompt = "Describe this image in detail."
system_prompt = (
    "This is a chat between a user and an assistant. "
    "The assistant is an expert in describing images, with detail and accuracy."
)

# Кодируем изображение в base64
with open(image_path, "rb") as img_file:
    image_bytes = img_file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:image/jpeg;base64,{image_base64}"

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
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }
    ],
    "temperature": 0.7,
    "max_tokens": 512,
    "stream": False
}

# Отправка запроса
response = requests.post(LMSTUDIO_API, json=payload)

# Вывод результата
if response.status_code == 200:
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print("📸 Описание изображения:\n")
    print(reply)
else:
    print(f"❌ Ошибка от LM Studio: {response.status_code}\n{response.text}")
