# Analyseur de Brief — AI-Powered Brief Analyzer

> A LangGraph-based AI agent that analyzes a brief, asks clarifying questions, runs a dynamic RAG pipeline, and generates a structured HTML dashboard.

Built by **Umberto Emonds**

---

## What it does

1. **Analyzes** the user's brief using an LLM
2. **Clarifies** missing information via human-in-the-loop interrupts
3. **Retrieves** relevant sources via Tavily + dynamic RAG (HuggingFace + Chroma)
4. **Generates** a complete pedagogical fiche in Markdown
5. **Exports** the result as a styled HTML dashboard

---

## Tech stack

| Component | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | Mistral (`mistral-small-latest`, configurable via `LLM_MODEL`) |
| Web search | Tavily |
| Embeddings | HuggingFace — `all-MiniLM-L6-v2` |
| Vector store | Chroma (ephemeral, per run) |
| Scraping | requests + BeautifulSoup |
| Markdown > HTML | mistune |
| Web UI | Streamlit |
| Output | HTML + CSS dashboard |

---

## Setup

```bash
git clone https://github.com/your-username/agent-brief.git
cd agent-brief
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file at the root:

```env
MISTRAL_API_KEY=your_mistral_api_key
TAVILY_API_KEY=your_tavily_api_key
```

---

## Usage

### CLI
```bash
python main.py
```

### Web UI (Streamlit)
```bash
streamlit run streamlit_app.py
```

---

## Project structure

```
agent-brief/
├── agentbrief/
│   ├── state.py         # BriefState and QA TypedDicts
│   ├── nodes.py         # Graph node functions + LLM prompts
│   ├── graph.py         # Graph construction and compilation
│   ├── routing.py       # Conditional edge routing
│   ├── rag.py           # Dynamic RAG pipeline
│   ├── config.py        # Configuration constants
│   ├── templates.py     # HTML template rendering
│   ├── templates/
│   │   └── dashboard.html
│   └── utils/
│       └── md_to_html.py
├── streamlit_app.py     # Streamlit web UI
├── main.py              # CLI entry point
├── assets/
│   └── demo.png
├── output/              # Generated dashboards (gitignored, max 20 kept)
├── .env                 # API keys (gitignored)
├── .streamlit/
│   └── config.toml
├── AGENTS.md            # AI assistant conventions (opencode)
└── requirements.txt
```

---

## Graph architecture

```
START → call_model → more (optional loop) → retrieve → generate → create_html → END
```

| Node | Role |
|---|---|
| `call_model` | Analyzes the brief, detects if clarification is needed |
| `more` | Asks a clarification question (human-in-the-loop) |
| `retrieve` | Web search + dynamic RAG pipeline |
| `generate` | Generates the fiche in Markdown |
| `create_html` | Exports as a styled HTML dashboard |

---

## Configuration

Key constants in `agentbrief/config.py`:

| Constant | Default | Description |
|---|---|---|
| `LLM_MODEL` | `mistral-small-latest` | LLM model (set via `LLM_MODEL` env var) |
| `MAX_CLARIFICATION_QUESTIONS` | 3 | Max clarification rounds |
| `MAX_KEYWORDS` | 6 | Max keywords for Tavily search |
| `TAVILY_MAX_RESULTS` | 15 | URLs returned by Tavily |
| `SCRAPE_TIMEOUT` | 5s | HTTP timeout per scraped URL |
| `CHUNK_SIZE` | 1000 | RAG chunk size (characters) |
| `CHUNK_OVERLAP` | 100 | RAG chunk overlap |
| `SIMILARITY_TOP_K` | 5 | Top-k results from Chroma |
| `MAX_OUTPUT_FILES` | 20 | Max dashboard files kept in `output/` |
