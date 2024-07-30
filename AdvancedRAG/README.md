---

# InfoRefine(AdvancedRAG)
InfoRefine is an advanced Retrieval-Augmented Generation (RAG) system designed to enhance the generation of accurate and contextually relevant information. Leveraging a LangGraph, InfoRefine integrates multiple components and tools to ensure high-quality output        through a structured and efficient process.

## Project Flow

1. **Start**: The process initiates at the `start` node.

2. **Retrieve**: Relevant documents or information are retrieved from a knowledge base or external sources.

3. **Grade Documents**: Retrieved documents are assessed for relevance and accuracy to ensure the use of only the most pertinent information.

4. **Web Search (Conditional)**: If the initial retrieval and grading do not yield satisfactory results, InfoRefine performs a web search using TAVILY to gather additional information. This step is conditional, indicated by a dashed line, based on the quality of the graded documents.

5. **Generate**: Utilizing the refined information from the retrieval, grading, and optional web search, InfoRefine generates final output that is accurate and contextually relevant.

6. **End**: The process concludes at the `end` node, delivering the final generated content ready for use.

## Technologies and Tools

- **Chroma DB**: Acts as the vector store for efficient information retrieval.
- **LangSmith**: Provides tracing and monitoring of the RAG process to ensure transparency and traceability.
- **TAVILY**: Conducts web searches to supplement information when the initial retrieval is insufficient.
- **Pytest**: Implements test cases to ensure system robustness and correctness.

## Features

- **High-Quality Output**: Ensures that generated content is accurate and contextually relevant through a multi-step process.
- **Efficient Retrieval**: Utilizes Chroma DB for fast and reliable information retrieval.
- **Enhanced Search Capability**: Incorporates TAVILY for additional information retrieval when needed.
- **Transparent Process**: Monitors and traces the entire RAG process with LangSmith.
- **Robust Testing**: Ensures system reliability with Pytest.

## Getting Started

To get started with InfoRefine, follow these steps:

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/InfoRefine.git
    ```

2. **Install Dependencies**:
    ```bash
    cd AdvancedRAG
    pip install -r requirements.txt
    ```

3. **Configure the System**:
    Follow the configuration instructions in `config.yaml` to set up your knowledge base, TAVILY credentials, and other necessary settings.

4. **Run the System**:
    ```bash
    python main.py
    ```

5. **Run Tests**:
    ```bash
    pytest
    ```


---

