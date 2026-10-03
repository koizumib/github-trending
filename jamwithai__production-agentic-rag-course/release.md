tag: week7.0
name: Week 7: Agentic RAG with LangGraph and Telegram Bot
published_at: 2025-11-26T09:24:07Z
prerelease: False

**What's included:**
• LangGraph-powered agentic RAG with intelligent decision-making
• Guardrail node for query validation and domain boundary detection
• Document grading with semantic relevance evaluation
• Query rewriting for automatic query refinement
• Adaptive multi-attempt retrieval with intelligent fallback
• Telegram bot integration with async operations
• Reasoning transparency with exposed decision steps
• Interactive Jupyter notebook tutorial (notebooks/week7/week7_agentic_rag.ipynb)

**Key learning outcomes:**
• Build state-based agent workflows with LangGraph
• Implement guardrails for query validation
• Design document grading systems
• Create adaptive retrieval strategies
• Integrate Telegram bots with RAG systems
• Expose reasoning steps for transparency and debugging

**Prerequisites:**
• Completed Week 1-6 setup
• Docker Desktop with Docker Compose running
• Python 3.12+ with UV Package Manager
• All services healthy (FastAPI, PostgreSQL, OpenSearch, Airflow, Ollama, Redis, Langfuse)

**Getting started:**
```
git clone --branch week7.0 https://github.com/jamwithai/arxiv-paper-curator
cd arxiv-paper-curator
uv sync
docker compose down -v
docker compose up --build -d
```