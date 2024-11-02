# Load indices from disk
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Settings
from llama_index.core import load_index_from_storage
from llama_index.llms.openai import OpenAI
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.memory import ChatMemoryBuffer
import os
import openai
from llama_index.readers.file import UnstructuredReader
from pathlib import Path
from dotenv import load_dotenv


#initiate api key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

storage_context = StorageContext.from_defaults(
        persist_dir=f"./storage/"
    )
cur_index = load_index_from_storage(
        storage_context,
    )
index = cur_index


individual_query_engine_tools = [
    QueryEngineTool(
        query_engine=index.as_query_engine(),
        metadata=ToolMetadata(
            name=f"vector_index",
            description=f"useful for when you want to answer queries about the Campell books",
        ),
    )
]

query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=individual_query_engine_tools,
    llm=OpenAI(model="gpt-3.5-turbo"),
)

query_engine_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="sub_question_query_engine",
        description="useful for when you want to answer queries about the Campell books",
    ),
)

tools = individual_query_engine_tools + [query_engine_tool]


chat_store = SimpleChatStore()

chat_memory = ChatMemoryBuffer.from_defaults(
    token_limit=3000,
    chat_store=chat_store,
    chat_store_key="user1",
)

agent = OpenAIAgent.from_tools(tools, verbose=True, memory =chat_memory)

while True:
    text_input = input("User: ")
    if text_input == "exit":
        break
    response = agent.chat(text_input)
    print(f"Agent: {response}")
    chat_store.persist(persist_path="chat_store.json")