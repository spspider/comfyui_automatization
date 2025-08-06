import os
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define client configuration
client_config = {
    "Azure": {
        "client": AzureOpenAI(
            azure_endpoint=os.environ.get("azure_endpoint"),
            api_key=os.environ.get("azure_api_key"),
            api_version="2024-02-01"
        ),
        "model": "gpt-4o",
        "client_type": "azure"
    },
    "GPT": {
        "client": OpenAI(api_key=os.environ.get("OPENAI_API_KEY")),
        "model": "gpt-3.5-turbo",
        "client_type": "openai"
    },
    "DeepSeek-distill-qwen": {
        "client": OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("deepseek_api_key"),
        ),
        "model": "moonshotai/kimi-k2:free",
        "client_type": "openai"
    },
    "DeepSeek-r1": {
        "client": OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("deepseek_api_key"),
        ),
        "model": "deepseek/deepseek-r1:free",
        "client_type": "openai"
    },
    "gemini": {
        "client": OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("deepseek_api_key"),
        ),
        "model": "google/gemini-2.0-flash-exp:free",
        "client_type": "openai"
    },
    "DeepSeek-exp-1206": {
        "client": OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("deepseek_api_key"),
        ),
        "model": "google/gemini-exp-1206:free",
        "client_type": "openai"
    },
    "qwen": {
        "client": OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("deepseek_api_key"),
        ),
        "model": "qwen/qwen3-235b-a22b:free",
        "client_type": "openai"
    }
}

async def generate_response_allmy(provider, all_text):
    """
    Universal function to generate responses from different providers.

    :param provider: The provider name (either 'Azure' or 'GPT').
    :param all_text: The input text for the model.
    :return: The generated response.
    """
    try:
        if provider not in client_config:
            raise ValueError(f"Invalid provider: {provider}")

        client_info = client_config[provider]
        client = client_info["client"]
        model = client_info["model"]

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": all_text}],
            model=model
        )

        all_response = f"######## {provider} #######\n{chat_completion.choices[0].message.content}"
        # print(f"{all_response}")
        return all_response
    except Exception as e:
        print(f"Error ({provider}): {e}")
        return None

# Example usage
import asyncio

async def main():

    deepseek_response = await generate_response_allmy("DeepSeek-r1", "You a creator of popular content, you have to write scenario for short 1 minute video. use the most popular viewing videos, and trends.")
    print(deepseek_response)

if __name__ == "__main__":
    asyncio.run(main())