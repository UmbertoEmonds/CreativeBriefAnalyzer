# Agent Brief — Module Conventions

## StateGraph topology

```
START → call_model
  call_model → route_after_analysis → "more" | "retrieve"
  more → route_after_clarification → "call_model" | "retrieve"
  retrieve → generate → create_html → END
```

## Node interface
Every node function follows this signature:
```python
def node_name(state: BriefState, llm) -> dict:
    """Docstring with Args/Returns."""
    # mutate or read state, return partial update dict
```
Nodes receive `(state, llm)` — exception: `create_html` only takes `state` (no LLM call).

## Routing return values
- `"more"` → ask another clarification question
- `"retrieve"` → proceed to web search + RAG
- `"call_model"` → re-analyze the brief with updated history
- `"generate"` / `"create_html"` / `END` → linear edges, no conditional needed

## Prompt conventions
- All prompts are in **French** (user-facing project)
- Defined as module-level `_UPPERCASE` `ChatPromptTemplate` in `nodes.py`
- Use `{variable}` placeholders (not f-strings)
- Anti-hallucination rules: never define/guess acronyms from the brief
- Clarification signal: LLM must begin its response with `CLARIFICATION_NEEDED`
- Stopping phrases: `["non", "stop", "ça suffit", "comme tu veux"]`

## Config constants (in `config.py`)
| Constant | Default | Used by |
|---|---|---|
| `LLM_MODEL` | `llama-3.3-70b-versatile` | `graph.py` |
| `MAX_CLARIFICATION_QUESTIONS` | 4 | `routing.py` |
| `MAX_KEYWORDS` | 5 | `nodes.py:retrieve` |
| `TAVILY_MAX_RESULTS` | 10 | `nodes.py:retrieve` |
| `TAVILY_INPUT_LIMIT` | 400 | `nodes.py:retrieve` |
| `SCRAPE_TIMEOUT` | 5 | `rag.py` |
| `MIN_TEXT_LENGTH` | 200 | `rag.py` |
| `CHUNK_SIZE` | 1000 | `rag.py` |
| `CHUNK_OVERLAP` | 100 | `rag.py` |
| `SIMILARITY_TOP_K` | 5 | `rag.py` |
| `STOPPING_PHRASES` | — | `routing.py` |

## RAG pipeline (in `rag.py`)
1. TavilySearch returns URLs → filter out social media domains
2. `requests.get()` each URL → BeautifulSoup extract text
3. `RecursiveCharacterTextSplitter` chunking (1000/100)
4. HuggingFace embeddings → Chroma vectorstore (uuid collection)
5. `similarity_search(query, k=5)` → concatenate results with source attribution

## HTML template system
- `templates.py` reads `templates/dashboard.html` and calls `string.Template.substitute()`
- Template variables use `$placeholder` syntax
- Main content is injected as pre-converted HTML via `$body_content`
- CSS targets: `.source-link`, `.history-item`, `.history-q`, `.history-a`, `.sidebar-empty`
- The template is a single-file HTML (all CSS in `<style>`)

## Markdown conversion
- `md_to_html.py` uses Python-Markdown with `["fenced_code", "tables", "codehilite"]`
- Applied before template rendering (body is already HTML when injected)

## Interrupt / Resume pattern
- `ask()` node calls `interrupt(question)` → graph pauses
- The CLI/Streamlit loop reads `result["__interrupt__"][0].value`
- Resumes via `graph.invoke(Command(resume=user_answer), config=config)`
- Thread identity via `thread_id` in config (uuid per session)
