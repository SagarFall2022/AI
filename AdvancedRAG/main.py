from dotenv import load_dotenv
load_dotenv()
from graph.graph import app

if __name__ == '__main__':
    print("Welcome to CRAG")
    print(app.invoke(input={"question": "what is the agent memory?"}))