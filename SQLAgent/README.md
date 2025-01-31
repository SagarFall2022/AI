---

# SQL AI Agent with Azure OpenAI Integration

## Overview

This project demonstrates the implementation of an SQL AI Agent using Azure's OpenAI services. The agent is designed to interact with both SQL Server and SQLite databases, providing intelligent SQL query capabilities and detailed responses to user inquiries. Additionally, it includes a `TextEmbedder` class to generate text embeddings using Cohere's API.

## Features

- **Azure OpenAI Integration**: Utilizes Azure's OpenAI to generate responses and perform SQL queries.
- **Dual Database Support**: Supports both SQL Server and SQLite databases.
- **Memory Management**: Uses `ConversationBufferMemory` to manage conversation history.
- **Tool Integration**: Includes tools for running SQL queries, describing tables, writing reports, and handling personal messages.
- **Text Embedding**: Uses Cohere's API to generate text embeddings.

## Requirements

- Python 3.7+
- `langchain`
- `langchain_openai`
- `python-dotenv`
- `os`
- `re`
- `requests`
- `logging`
- `tenacity`
- `cohere`

## Setup

1. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Create a `.env` file in the project root and add your Azure OpenAI and Cohere credentials:
    ```env
    AZURE_OPENAI_API_VERSION=<your_azure_openai_api_version>
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=<your_azure_openai_chat_deployment_name>
    AZURE_COHERE_DEPLOYMENT_NAME=<your_azure_cohere_deployment_name>
    AZURE_COHERE_API_KEY=<your_azure_cohere_api_key>
    AZURE_COHERE_SERVICE_NAME=<your_azure_cohere_service_name>
    ```

5. **Run the script**:
    ```bash
    python main.py
    ```

## Usage

### Initializing the Chat Model

```python
from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

chat = AzureChatOpenAI(
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    temperature=0.0
)
```

### Setting Up the Agent

1. **Define the Prompt**:
    ```python
    from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
    from langchain.schema import SystemMessage

    sqlite_tables = describe_tables_sqlite()
    tables = list_tables()

    prompt = ChatPromptTemplate(
        messages=[
            SystemMessage(content=(
                "You are an EXPERT SQL AI AGENT with access to both a SQL Server Database and a SQLite database.\n"
                f"The SQL Server database contains tables: {tables}\n"
                f"The SQLite database table structure: {sqlite_tables}\n\n"
                "Do not assume anything about the existence of tables or columns in either database. "
                "Always use the 'describe_tables' function to obtain information about specific tables.\n\n"
                "If you have a user query related to the SQL Server database, please ensure that you use columns from 'describe_tables' in your request. "
                "Retry querying up to five times, making any necessary adjustments based on error messages if you are querying the SQL Database.\n\n"
                "When the user query is NOT related to the SQL Server Database, ALWAYS use the 'personal_messages' function with 'User' as the argument. "
                "If the response from 'personal_messages' is null, retry with 'User' as the argument.\n\n"
                "Remember to provide clear and specific details about your query to receive accurate results."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )
    ```

2. **Initialize Memory and Tools**:
    ```python
    from langchain.memory import ConversationBufferMemory
    from tools.sql import run_query_tool, describe_tables_tool, personal_message_tool, describe_tables_sqlite
    from tools.report import write_report_tool

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    tools = [run_query_tool, describe_tables_tool, write_report_tool, personal_message_tool]
    ```

3. **Create the Agent**:
    ```python
    from langchain.agents import OpenAIFunctionsAgent, AgentExecutor, AgentType

    agent = OpenAIFunctionsAgent(
        llm=chat,
        prompt=prompt,
        tools=tools,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
    )
    ```

4. **Set Up the Agent Executor**:
    ```python
    agent_executor = AgentExecutor(
        agent=agent,
        verbose=True,
        tools=tools,
        memory=memory,
        handle_parsing_errors=True 
    )
    ```

### Running a Query

```python
response = agent_executor("How many orders are past due date?")
print(response)
```

### Text Embedding

The `TextEmbedder` class provides functionality to generate text embeddings using Cohere's API.

1. **Define the `TextEmbedder` Class**:
    ```python
    import os
    import re
    import cohere
    from tenacity import retry, wait_random_exponential, stop_after_attempt  

    class TextEmbedder():

        AZURE_COHERE_EMBEDDING_DEPLOYMENT=os.getenv["AZURE_COHERE_DEPLOYMENT_NAME"]

        def clean_text(self, text):
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'[\n\r]+', ' ', text).strip()
            return text

        @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(2))
        def embed_content(self, text, clean_text=True, use_single_precision=True):
            if clean_text:
                text = self.clean_text(text)

            cohere_api_key = os.getenv["AZURE_COHERE_API_KEY"]
            cohere_base_url = os.getenv["AZURE_COHERE_SERVICE_NAME"]
            co = cohere.Client(base_url=cohere_base_url, api_key=cohere_api_key) 

            model = self.AZURE_COHERE_EMBEDDING_DEPLOYMENT
            response = co.embed( 
                texts=[text], 
                model=model, 
                input_type="search_document", 
                embedding_types=["int8"], 
            ) 
            embedding = [embedding for embedding in response.embeddings.int8] 

            return embedding[0]
    ```

2. **Using the `TextEmbedder`**:
    ```python
    embedder = TextEmbedder()
    text = "Sample text to embed"
    embedding = embedder.embed_content(text)
    print(embedding)
    ```



---

## Additional Notes

- Ensure you have the required database connections and credentials configured in your environment.
- Adjust the prompt and agent settings as needed to fit your specific use case.

---

