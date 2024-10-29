import chainlit as cl
from pathlib import Path
from src.llm import ask_order, messages
from typing import Optional
import json
import os

MEMORY_FILE = "memory.json"

# Function to load memory from the JSON file
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

# Function to save conversation history to the JSON file
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# Loads persisted messages when resuming a chat session
@cl.on_chat_resume
async def resume_conversation(messages: Optional[list] = None):
    persisted_messages = load_memory()
    if persisted_messages:
        # Send all previous messages stored in memory to re-establish context
        for msg in persisted_messages:
            await cl.Message(content=msg["content"], role=msg["role"]).send()
    if messages:
        # Respond to the latest message from the persisted conversation
        last_message = messages[-1]
        response = ask_order(messages)
        await cl.Message(content=response).send()

@cl.set_starters
async def set_starters():
    # Pre-set topics the user can select from to start the conversation
    return [
        cl.Starter(
            label="Morning routine ideation",
            message="Can you help me create a personalized morning routine that would help increase my productivity throughout the day? Start by asking me about my current habits and what activities energize me in the morning.",
            icon="/public/idea.svg",
        ),
        cl.Starter(
            label="Explain superconductors",
            message="Explain superconductors like I'm five years old.",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Python script for daily email reports",
            message="Write a script to automate sending daily email reports in Python, and walk me through how I would set it up.",
            icon="/public/terminal.svg",
        ),
        cl.Starter(
            label="Text inviting friend to wedding",
            message="Write a text asking a friend to be my plus-one at a wedding next month. I want to keep it super short and casual, and offer an out.",
            icon="/public/write.svg",
        )
    ]

@cl.on_message
async def main(message: cl.Message):
    # Load the conversation history from JSON
    conversation_history = load_memory()

    # Append the user's message and the assistant's response to memory
    messages.append({"role": "user", "content": message.content})
    response = ask_order(messages)
    messages.append({"role": "assistant", "content": response})

    # Save the updated conversation history to JSON
    conversation_history.append({"role": "user", "content": message.content})
    conversation_history.append({"role": "assistant", "content": response})
    save_memory(conversation_history)

    # Send the assistant's response back to the user
    await cl.Message(content=response).send()

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Dictionary storing usernames and passwords for authentication
    users = {
        "sake": "123",
        "khoa": "123"
    }

    # Verifies credentials and returns user metadata if authenticated
    if username in users and users[username] == password:
        return cl.User(
            identifier=username, metadata={"role": username, "provider": "credentials"}
        )
    else:
        return None

if __name__ == "_main_":
    cl.run(main)