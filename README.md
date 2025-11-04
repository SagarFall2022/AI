

---

## Projects
1. **ServiceNow + Slack AI Copilot (Personal Project)**

   AI-powered incident lifecycle: create, dedupe, triage, and sync.
   - **Slack Bot**: `/incident` command + interactive replies.
   - **Duplicate Detection**: OpenAI embeddings + Qdrant vector search (≥0.80).
   - **AI Triage**: LLM summaries of similar incidents inside Slack.
   - **Realtime Sync**: ServiceNow Business Rule → REST → n8n → Qdrant upsert/delete.
   - **Stack**: n8n · ServiceNow · Slack · OpenAI (GPT-4o-mini, text-embedding-3-small) · Qdrant.

2. **SQL AI Agent with Azure OpenAI Integration**

   This project showcases the development of an SQL AI Agent using Azure's OpenAI services. It enables interaction with both SQL Server and SQLite databases, providing intelligent SQL query capabilities and detailed responses to user inquiries. Key features include:

   - **Azure OpenAI Integration**: Generates intelligent responses and executes SQL queries.
   - **Dual Database Support**: Interacts with SQL Server and SQLite databases.
   - **Memory Management**: Maintains conversation history using `ConversationBufferMemory`.
   - **Tool Integration**: Runs SQL queries, describes table structures, writes reports, and handles personal messages.
   - **Text Embedding**: Utilizes a `TextEmbedder` class to generate text embeddings via Cohere's API.

   This project offers a robust foundation for integrating advanced SQL querying and data analysis capabilities into AI-driven applications.

3. **InfoRefine(AdvancedRAG)**

   **InfoRefine** is a Retrieval-Augmented Generation (RAG) system designed to produce accurate and contextually relevant information. It combines Chroma DB for efficient retrieval, TAVILY for web searches, LangSmith for monitoring, and Pytest for robust testing. The          system refines information through a multi-step process, ensuring high-quality output.


4. **Daily AI News Research Agent**

   The Daily AI News Research Agent automates AI news discovery and summarization using n8n, GPT-4o, and Perplexity API. It fetches the latest AI developments, removes duplicates through Google Sheets memory, and emails a clean daily digest at 9 AM.

    - **Perplexity + GPT-4o**: Fetches and summarizes daily AI updates.
    - **Google Sheets Memory**: Tracks and filters past news items.
    - **Automated Delivery**: Sends formatted digests via Gmail.
    - **Fully Autonomous Flow**: Runs daily without manual input.

   Tech Stack: n8n | GPT-4o | Perplexity API | Google Sheets | Gmail

---


