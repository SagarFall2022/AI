from langchain.prompts import(
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage
from langchain.agents import OpenAIFunctionsAgent, AgentExecutor, AgentType
from langchain.memory import ConversationBufferMemory
from tools.sql import run_query_tool, list_tables, describe_tables_tool, personal_message_tool, describe_tables_sqlite
from tools.report import write_report_tool
from handlers.chat_model_start import ChatModelStartHandler
import os
from dotenv import load_dotenv

load_dotenv()
handler = ChatModelStartHandler()
# chat = ChatOpenAI(
#     callbacks=[handler],
#     temperature=0.0
# )

chat = AzureChatOpenAI(
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    callbacks=[handler],
    temperature=0.0

)


sqlite_tables=describe_tables_sqlite()
tables= list_tables()
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
        #  SystemMessage(content=(
        #     "You are an AI that has access to a SQL Server Database and SQLite database.\n"
        #     f"The database has tables of: {tables}\n"
        #     "Do not make any assumptions about what tables exist or what columns exist. "
        #     "Instead, use the 'describe_tables' function. "
        #     "If you feel the user query is not related to the SQL Server Database, "
        #     "PLEASE USE the 'personal_messages' function with 'User' as the argument.\n"
        #     "You should ONLY run query either in SQL Database or in SQLite Database"
        #     )),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ]
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
# print(memory)
tools=[run_query_tool, describe_tables_tool, write_report_tool,personal_message_tool]
agent = OpenAIFunctionsAgent(
    llm=chat,
    prompt=prompt,
    tools=tools,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)



agent_executor= AgentExecutor(
    agent=agent,
    verbose=True,
    tools=tools,
    memory=memory,
    handle_parsing_errors=True 
)


agent_executor("How many orders are past due date?")


