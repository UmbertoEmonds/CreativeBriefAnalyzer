# AgentBrief Analyst 🚀

An intelligent, interactive Creative Brief Analyzer built with **LangGraph** and **LangChain**. It processes user inputs, requests necessary human-in-the-loop clarifications via an interrupt mechanism, conducts RAG-powered web research using Tavily, and compiles everything into a stunning, responsive HTML dashboard.

## 🛠️ Project Architecture

The project is decoupled into single-responsibility modules to ensure clean code and easy maintenance:

```text
agentbrief/
│
├── templates/
│   └── dashboard.html       # Pure HTML/CSS responsive layout template
│
├── converters.py            # Sequential line-by-line Markdown-to-HTML parser
├── templates.py             # Template engine using python's string.Template
├── nodes.py                 # LangGraph workflow nodes (StateGraph actions)
├── graph.py                 # Core StateGraph and routing workflow definition
├── state.py                 # TypedDict definitions for global BriefState and QA
└── routing.py               # Conditional edge routers
