# lmstudio_api.py
import requests
import base64
import os

def describe_image(image_path, model_key="qwen2-vl-2b-instruct", user_prompt="Describe this image in detail.", system_prompt=None):
    if system_prompt is None:
        system_prompt = (
            "This is a chat between a user and an assistant. "
            "The assistant is an expert in describing images, with detail and accuracy."
        )

    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{image_base64}"

    payload = {
        "model": model_key,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": user_prompt}
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": False
    }

    response = requests.post("http://localhost:1234/v1/chat/completions", json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise RuntimeError(f"LM Studio Error: {response.status_code} - {response.text}")
