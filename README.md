# BriefAnalyzer 🤖📊

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-LangGraph-orange)](https://github.com/langchain-ai/langgraph)
[![LLM Provider](https://img.shields.io/badge/LLM-Groq%20%7C%20Llama%203.3-green)](https://groq.com/)

**BriefAnalyzer** is an intelligent, conversational AI agent designed to automate, enrich, and evaluate creative and strategic briefs. Built on top of **LangGraph**, it transforms raw, incomplete ideas into comprehensive, production-ready PDF strategic sheets.

Rather than just processing text statically, the agent acts as a dynamic collaborator: it analyzes inputs, interacts with humans to fill in missing gaps, performs autonomous web research, and outputs a beautifully formatted document.

---

## 🛠️ Core Features

- **Smart Analysis Loop**: Evaluates briefs using advanced LLMs (`Llama 3.3` via Groq) to instantly detect missing essential information (target audience, format, core objectives).
- **Human-in-the-Loop Interaction**: Seamlessly pauses graph execution using LangGraph's native `interrupt` mechanism to request targeted user feedback, resuming exactly where it left off.
- **Autonomous Web Research**: Integrates the `Tavily Search API` to automatically fetch live web context, trends, and references based on the brief's topic.
- **Robust Markdown-to-PDF Parser**: Features a custom-built, error-resistant `FPDF2` engine that converts structured Markdown text, bold/italic inline styling, bullet points, and code snippets into a professional PDF without encoding or text-overflow issues.

---

## 🏗️ Architecture & Workflow

The agent operates as a state machine managing a non-linear flow. Below is the workflow layout of the compiled graph:

```text
       [ START ]
           │
           ▼
     ┌───────────┐
     │ call_model│ ◄──────────────────────────┐
     └─────┬─────┘                            │
           │                                  │
           ▼ (Conditional Edge)               │
     Is clarification needed?                 │
      /                  \                    │
    (Yes)                (No)                 │
    /                      \                  │
   ▼                        ▼                 │
┌──────┐              ┌────────────┐          │
│ more │              │ search_web │          │ (Loop back if
└──┬───┘              └─────┬──────┘          │  under limit)
   │                        │                 │
   ▼ (Conditional Edge)     ▼                 │
 Max 2 Qs or User Stop? ──(No)────────────────┘
   │
 (Yes)
   │
   ▼
┌──────────┐
│ generate │
└────┬─────┘
     │
     ▼
┌────────────┐
│ create_pdf │
└────┬───────┘
     │
     ▼
  [ END ]
