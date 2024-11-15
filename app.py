import chainlit as cl
from pathlib import Path
from src.llm import ask_order, messages
from typing import Optional, Dict
import json
import os
from llama_index.core import SimpleDirectoryReader
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Settings, load_index_from_storage
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
import socket

storage_context = StorageContext.from_defaults(
        persist_dir="./storage/"
    )

cur_index = load_index_from_storage(
        storage_context,
    )
index = cur_index

chat_file_path = "./chat/chat_store.json"

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

@cl.on_chat_start
async def start():
    if os.path.exists(chat_file_path) and os.path.getsize(chat_file_path) > 0:
        try:
            chat_store = SimpleChatStore.from_persist_path(chat_file_path)
        except:
            chat_store = SimpleChatStore()
    else:
        chat_store = SimpleChatStore()

    chat_memory = ChatMemoryBuffer.from_defaults(
        token_limit=1500,
        chat_store=chat_store,
        chat_store_key="user",
    )  

    individual_query_engine_tools = [
    QueryEngineTool(
        query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name=f"book",
                description=f"1000 Best Bartenders Recipes",
            ),
        )
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        llm=OpenAI(model="gpt-4o-mini", temperature = 0.1, max_tokens = 1024, streaming = True), 
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description="1000 Best Bartenders Recipes",
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]
    app_user = cl.user_session.get("user")

    agent = OpenAIAgent.from_tools(tools, verbose=True, memory = chat_memory)
    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_store", chat_store)


@cl.on_chat_resume
async def on_chat_resume():
    if os.path.exists(chat_file_path) and os.path.getsize(chat_file_path) > 0:
        try:
            chat_store = SimpleChatStore.from_persist_path(chat_file_path)
        except:
            chat_store = SimpleChatStore()
    else:
        chat_store = SimpleChatStore()

    chat_memory = ChatMemoryBuffer.from_defaults(
        token_limit=1500,
        chat_store=chat_store,
        chat_store_key="user",
    )  

    individual_query_engine_tools = [
    QueryEngineTool(
        query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name=f"book",
                description=f"1000 Best Bartenders Recipes",
            ),
        )
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        llm=OpenAI(model="gpt-4o-mini", temperature = 0.1, max_tokens = 1024, streaming = True), 
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description="1000 Best Bartenders Recipes",
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]
    app_user = cl.user_session.get("user")

    agent = OpenAIAgent.from_tools(tools, verbose=True, memory = chat_memory)
    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_store", chat_store)

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

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
    ) -> Optional[cl.User]:
        return default_user

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


