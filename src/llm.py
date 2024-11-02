from openai import OpenAI
from src.prompt import system_instruction
from llama_index.core import Settings

client = OpenAI()

messages = [
    {"role": "system", "content": system_instruction}
]


def ask_order(message, model="gpt-4o-mini", temperature=0.1 , max_tokens=1024, streaming=True):
    response = client.chat.completions.create(
        model=model,
        messages= messages,
        temperature= temperature
    )

    return response.choices[0].message.content