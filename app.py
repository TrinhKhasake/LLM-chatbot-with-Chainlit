import chainlit as cl
import os
from pathlib import Path
from src.llm import ask_order, messages
from typing import Optional, Dict
import json
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core import load_index_from_storage
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent

# Path variables
chat_file_path = "./chat/chat_store.json"
MEMORY_FILE = "memory.json"
storage_context = StorageContext.from_defaults(persist_dir="./storage/")

# Load index
cur_index = load_index_from_storage(storage_context)
index = cur_index

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

@cl.on_chat_start
async def start():
    chat_store = (
        SimpleChatStore.from_persist_path(chat_file_path)
        if os.path.exists(chat_file_path) and os.path.getsize(chat_file_path) > 0
        else SimpleChatStore()
    )

    chat_memory = ChatMemoryBuffer.from_defaults(
        token_limit=1500,
        chat_store=chat_store,
        chat_store_key="user",
    )

    individual_query_engine_tools = [
        QueryEngineTool(
            query_engine=index.as_query_engine(),
            metadata=ToolMetadata(
                name="book",
                description="1000 Best Bartenders Recipes",
            ),
        )
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        llm=OpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=1024, streaming=True),
    )

    agent = OpenAIAgent.from_tools(
        tools=individual_query_engine_tools + [
            QueryEngineTool(
                query_engine=query_engine,
                metadata=ToolMetadata(
                    name="sub_question_query_engine",
                    description="1000 Best Bartenders Recipes",
                ),
            )
        ],
        verbose=True,
        memory=chat_memory,
    )

    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_store", chat_store)

@cl.on_message
async def main(message: cl.Message):
    conversation_history = load_memory()

    messages.append({"role": "user", "content": message.content})
    response = ask_order(messages)
    messages.append({"role": "assistant", "content": response})

    conversation_history.append({"role": "user", "content": message.content})
    conversation_history.append({"role": "assistant", "content": response})
    save_memory(conversation_history)

    await cl.Message(content=response).send()

# Entry point with dynamic port binding
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use Render's PORT variable or fallback
    print(f"Starting Chainlit app on port {port}...")
    cl.run("0.0.0.0", port=port)
