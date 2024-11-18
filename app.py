import chainlit as cl
from src.llm import ask_order, messages
from typing import Optional, Dict
import json, os
from llama_index.core import StorageContext, Settings, load_index_from_storage
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Menu",
            message="Can you give me the menu? ",
            icon="/public/public/menu.svg",
        ),
        cl.Starter(
            label="Best drink to start your day",
            message="Can you give me an energizing and stimulating drink to start my day full of energy?",
            icon="/public/public/sun.svg",
        ),
        cl.Starter(
            label="Best drink after workout",
            message="Give me a drink to replenish my energy and minerals after I exercise",
            icon="/public/public/exercise.svg",
        ),
        cl.Starter(
            label="Suitable drink for student",
            message="Can you give some drink that cheap and fresh for student?",
            icon="/public/public/student.svg",
        )
    ]

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