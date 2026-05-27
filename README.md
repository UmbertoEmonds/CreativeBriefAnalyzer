# Agent Brief — AI-Powered Brief Analyzer

> A LangGraph-based agentic pipeline that analyzes creative briefs, asks clarifying questions, performs web research, and generates a structured PDF document.

Built by **Umberto Emonds**

---

## Overview

Agent Brief is an AI agent built with LangGraph that orchestrates a full brief analysis workflow:

1. **Analyzes** the user's brief using an LLM
2. **Asks clarifying questions** if essential information is missing (target audience, format, objective)
3. **Searches the web** for relevant resources via Tavily
4. **Generates** a structured, pedagogical fiche
5. **Exports** the result as a formatted PDF

---

## Architecture

```
__start__
    │
    ▼
call_model ──(CLARIFICATION_NEEDED)──► more ──► call_model (loop)
    │                                               │
    └──────────────(sufficient brief)───────────────┘
                         │
                         ▼
                     search_web
                         │
                         ▼
                      generate
                         │
                         ▼
                     create_pdf
                         │
                         ▼
                      __end__
```

### Graph nodes

| Node | Role |
|---|---|
| `call_model` | Analyzes the brief and detects if clarification is needed |
| `more` | Asks the user a targeted clarification question (human-in-the-loop) |
| `search_web` | Performs a web search via Tavily based on the brief |
| `generate` | Generates the full structured fiche content |
| `create_pdf` | Renders the content as a formatted PDF |

### State schema

```python
class BriefState(TypedDict):
    input: str                                        # Original user brief
    analyse: str                                      # LLM analysis
    questions_answers: Annotated[list[QA], operator.add]  # Clarification history
    web_result: str                                   # Tavily search results
    final_data: str                                   # Generated fiche content
    result_path: str                                  # Output PDF path
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| LLM | [Groq](https://groq.com/) — `llama-3.3-70b-versatile` |
| Web search | [Tavily](https://tavily.com/) |
| PDF generation | [fpdf2](https://py-pdf.github.io/fpdf2/) |
| Environment | Python 3.13, dotenv |

---

## Project Structure

```
agent-brief/
├── agentbrief/
│   ├── state.py          # BriefState and QA TypedDict definitions
│   ├── nodes.py          # All graph node functions
│   ├── graph.py          # Graph construction and compilation
│   ├── routing.py        # Conditional edge routing functions
│   └── utils/
│       └── md_to_pdf_parser.py  # Markdown to PDF renderer
├── main.py               # CLI entry point
├── generate_graph.py     # Graph schema export (PNG)
├── output/               # Generated PDFs (gitignored)
├── .env                  # API keys (gitignored)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/agent-brief.git
cd agent-brief
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file at the root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

---

## Usage

```bash
python main.py
```

Example interaction:

```
╔══════════════════════════════════════════════════════════╗
║           Analyseur de Brief - © Umberto Emonds          ║
╚══════════════════════════════════════════════════════════╝

  Décris ton brief (sujet). Nous l'analyserons pour toi et te
  poserons des questions de clarification si nécessaire.
  Un document PDF pédagogique et structuré sera généré à l'issue de cette séance.

  À toi de jouer : Je veux une fiche sur LangGraph pour des développeurs débutants

  ⏳ Analyse en cours...

  ❓ Question 1 :
  Quel format de document souhaitez-vous (A4 imprimable, numérique) ?

  Votre réponse : A4 imprimable, ton didactique

  ⏳ Traitement en cours...

────────────────────────────────────────────────────────────
PDF généré avec succès 📄 (output/brief_20260518_1042.pdf)
────────────────────────────────────────────────────────────
```

### Example briefs

| Type | Brief |
|---|---|
| Short (triggers questions) | `"Génère une fiche pour apprendre Python à un enfant."` |
| Medium | `"Je veux une fiche pédagogique sur LangGraph pour des développeurs débutants, format A4."` |
| Detailed (no questions) | `"Crée une fiche PDF pour un enfant de 12 ans, débutant en Python, couvrant variables, boucles et fonctions, ton ludique, format A4."` |

---

## Generate graph schema

```bash
python generate_graph.py
```

Outputs `graph.png` at the project root.

---

## Key design decisions

- **Closure pattern** — LLM instance is injected into nodes via closures, keeping node signatures compatible with LangGraph's single-argument requirement
- **Human-in-the-loop** — Uses LangGraph's `interrupt` mechanism to pause execution and resume after user input
- **Retrieval** — Web search via Tavily enriches the LLM context before fiche generation; extensible to a vector database for full RAG
- **Routing logic** — Clarification limit is enforced in `route_after_analysis` to prevent infinite loops; early exit keywords handled in `route_after_clarification`

---

## Possible extensions

- Swap PDF output for image generation (DALL-E, Stable Diffusion) for infographic-style fiches
- Add a vector database (e.g. Chroma, Pinecone) for true RAG over internal documents
- Build a Streamlit UI for a more polished demo experience
- Add Agent-to-Agent (A2A) communication for multi-agent workflows
- Integrate MCP servers for external tool connectivity

---

## License

MIT
