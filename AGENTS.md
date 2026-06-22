# ChatBotLangGraph — Project Context

## What it does
Interactive brief analysis agent: user submits a brief → LLM analyzes → optionally asks clarifying questions (human-in-the-loop) → web search + RAG retrieval → generates a structured pedagogical HTML dashboard.

## Entry points
- `main.py` — CLI version (input loop in terminal)
- `streamlit_app.py` — Web UI version (planned)

## Project structure

| Path | Role |
|---|---|
| `agentbrief/state.py` | `BriefState` & `QA` TypedDicts — the LangGraph state schema |
| `agentbrief/graph.py` | StateGraph construction + compilation (module-level `graph` object) |
| `agentbrief/nodes.py` | One function per graph node (`call_model`, `ask`, `retrieve`, `generate_final_data`, `create_html`) |
| `agentbrief/routing.py` | Conditional edge functions (`route_after_analysis`, `route_after_clarification`) |
| `agentbrief/rag.py` | RAG pipeline: scrape URLs → chunk → embed (HuggingFace) → Chroma → similarity search |
| `agentbrief/templates.py` | Renders `dashboard.html` with state data via `string.Template` |
| `agentbrief/utils/md_to_html.py` | Markdown → HTML conversion (Python-Markdown lib) |
| `agentbrief/config.py` | All magic numbers and env-based configuration |
| `agentbrief/templates/dashboard.html` | HTML/CSS skeleton for the final report |
| `output/` | Generated `.html` files (gitignored) |

## Tech stack
- **Agent framework:** LangGraph (StateGraph, interrupt/resume, MemorySaver checkpointing)
- **LLM:** Groq — `llama-3.3-70b-versatile` (configurable via `LLM_MODEL` env var)
- **Web search:** Tavily (`langchain-tavily`)
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2`
- **Vector store:** Chroma (ephemeral collection per run)
- **Scraping:** `requests` + BeautifulSoup
- **Markdown → HTML:** Python-Markdown with `fenced_code`, `tables`, `codehilite`
- **HTML template:** `string.Template` (`$placeholder` syntax)

## Environment
- `.env` required: `GROQ_API_KEY`, `TAVILY_API_KEY`
- Python 3.10+ — `.venv/` at project root

## Naming conventions
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Private globals: `_UPPERCASE` (prompt templates) or `_lowercase` (helpers)
- Config constants: `UPPER_CASE`
