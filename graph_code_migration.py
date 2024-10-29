import os
import json
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, MessagesState
from typing import Annotated, List, Literal, Optional, Sequence, TypedDict, Dict, Annotated
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from langchain_databricks import ChatDatabricks, DatabricksEmbeddings
from langchain_databricks.vectorstores import DatabricksVectorSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
import tempfile

def get_llm_model():
    return ChatDatabricks(
    endpoint="ragpoc_openai_chat",
    extra_params={"temperature": 0},
)
    
def get_embedding_model():
    return DatabricksEmbeddings(endpoint="ragpoc_openai_embedding")

llm = get_llm_model()


@tool
def migrate_database_lang_format(source_lang, target_lang, content):
    """For a given source_lang, target_lang and content, Use this tool to convert content from source_lang to target_lang specified."""
    system_message = f"""You are an expert in database systems, skilled in SQL query languages for various database platforms (e.g., MSSQL, PostgreSQL, MySQL, Oracle). Your task is to migrate database queries from a given source format to a target format. Follow these instructions to perform the conversion:

            1. Accurately translate each SQL query, function, and clause from the **source format** to its equivalent in the **target format**.
            2. Ensure that all data types, functions, and keywords are correctly mapped and adjusted according to the target database’s syntax and structure.
            3. For elements in the source format that do not have a direct equivalent in the target format, provide a functionally similar implementation using the target format’s native features.
            4. Preserve query structure, logic, and intent to maintain readability and correct functionality in the **target format**.
            5. Ensure that the resulting target query follows best practices for that format, including proper use of indexes, optimization techniques, and compliance with the target platform’s capabilities.
            6. Validate the target query for correctness, ensuring that the translated query will execute properly in real-world scenarios.
            7. Output the final converted query.

            Source Format: {{source_lang}}
            Target Format: {{target_lang}}
            
            Begin the conversion using the provided source content:
            {{content}}"""
    dbms_lang_migration_prompt = ChatPromptTemplate.from_messages([("system", system_message)])
    dbms_lang_migration_chain = dbms_lang_migration_prompt | llm | StrOutputParser()
    dbms_lang_migrated_content = dbms_lang_migration_chain.invoke({"source_lang": source_lang, "target_lang": target_lang, "content": content})
    return dbms_lang_migrated_content


@tool
def migrate_programming_lang_format(source_lang, target_lang, content):
    """For a given source_lang, target_lang and content, Use this tool to convert content from source_lang to target_lang specified."""
    system_message = f"""You are an expert software engineer proficient in multiple programming languages, including Python, Java, JavaScript, C++, and more. Your task is to migrate code from a source programming language to a target programming language. Follow these instructions to ensure an accurate and efficient conversion:

            1. Accurately translate the syntax, functions, classes, and logic from the source code into the target language while maintaining the code's original functionality.
            2. Identify and use equivalent libraries, functions, and language constructs in the target format to achieve the same results.
            3. Ensure that all key programming concepts (such as loops, conditionals, classes, functions, data structures, etc.) are correctly adapted to the target language's syntax and best practices.
            4. When there is no direct equivalent for a specific feature in the target language, provide a functionally similar implementation using native features of the target language.
            5. Preserve comments and structure from the original code to maintain readability and provide context for the converted code.
            6. Validate the resulting target code to ensure it follows the target language's best practices, style conventions, and coding standards.
            7. Output the final converted code in the target format.

            Source Format: {{source_lang}}
            Target Format: {{target_lang}}
            Begin the conversion using the provided source content:
            {{content}}"""
    lang_migration_prompt = ChatPromptTemplate.from_messages([("system", system_message)])
    lang_migration_chain = lang_migration_prompt | llm | StrOutputParser()
    lang_migrated_content = lang_migration_chain.invoke({"source_lang": source_lang, "target_lang": target_lang, "content": content})
    return lang_migrated_content

@tool
def write_file_content(extension, content, config: RunnableConfig):
    """For a given content, Write the content to a file.
    Determine the filename extension depending on the type of content
    Args:
        extension: The file extension to use for the output file. For example, "txt" for text files, "py" for Python files, etc.
        content: The content to write to the file"""

    filename = f"output.{extension}"
    directory = config.get("configurable", {}).get("directory")

    # Create the full file path
    file_path = os.path.join(directory, filename)

    # Write content to the file
    with open(file_path, 'w') as file:
        file.write(content)
        print(f"Content written to '{file_path}'.")


def load_graph() -> CompiledStateGraph:
    tools = [migrate_programming_lang_format, migrate_database_lang_format,
         write_file_content]

    tool_node = ToolNode(tools)
    model_with_tools = llm.bind_tools(tools)

    workflow = StateGraph(MessagesState)

    def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
        messages = state["messages"]
        last_message = messages[-1]
        # print(last_message)
        if last_message.tool_calls:
            return "tools"
        return "__end__"


    def call_model(state: MessagesState):
        messages = state["messages"]
        # print(messages)
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}


    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.add_edge("__start__", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
    )
    workflow.add_edge("tools", "agent")

    graph = workflow.compile()
    return graph
