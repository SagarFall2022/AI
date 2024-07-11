import sqlite3
from typing import List
import pypyodbc
from pydantic.v1 import BaseModel
from langchain.tools import Tool
from tools.credential import username,password
conn1 = sqlite3.connect("db.sqlite")
# Connect to the SQL Server database
server='infotraax-dev.database.windows.net'
database='SRM'
# Connect to the SQL Server database
def connect_to_sql_server():
    try: 

        conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
        conn = pypyodbc.connect(conn_str)
        return conn
    except pypyodbc.Error as e:
         return f"The following error occurred: {str(e)}"



def list_tables():
    conn = connect_to_sql_server()
    c= conn.cursor()
    c.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = 'dbo';")
    rows= c.fetchall()
    conn.close()
    return "\n".join(row[0] for row in rows if row[0] is not None)


# Define the Pydantic schema for passing arguments to the run_query_tool
class RunQueryArgsSchema(BaseModel):
    query: str

# Function to run a SQL Server query
def run_sql_server_query(query):
    conn = connect_to_sql_server()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except pypyodbc.Error as e:
        return f"The following error occurred: {str(e)}"


# Define the tool for running queries
run_query_tool = Tool.from_function(
    name="sql_server_query",
    description="Run a SQL Server query.",
    func=run_sql_server_query,
    args_schema=RunQueryArgsSchema
)

# Function to describe tables in the SQL Server database
def describe_tables(table_names):
    conn = connect_to_sql_server()
    cursor = conn.cursor()
    tables = ', '.join("'" + table + "'" for table in table_names)
    cursor.execute(f"SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IN ({tables})")
    return cursor.fetchall()

class DescribeTablesArgsSchema(BaseModel):
    table_names: List[str]

# Define the tool for describing tables
describe_tables_tool = Tool.from_function(
    name="describe_tables",
    description="Given a list of table names, returns the schema of those tables",
    func=describe_tables,
    args_schema=DescribeTablesArgsSchema
)


# Function to retrieve personal messages from the SQL Server database
def personal_messages(topic):
    cursor1 = conn1.cursor()
    cursor1.execute(f"SELECT message FROM personal_messages WHERE topic = '{topic}';")
    return cursor1.fetchone()

# Define the tool for retrieving personal messages
personal_message_tool = Tool.from_function(
    name="personal_messages",
    description="To display the personal message",
    func=personal_messages
)

def describe_tables_sqlite():
    c= conn1.cursor()
    rows= c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' and name IN('personal_messages');")
    return '\n'.join(row[0] for row in rows if row[0] is not None)

