"""
Centralized configuration constants for the ChatBotLangGraph application.
"""
import os

# LLM
LLM_MODEL = os.getenv("LLM_MODEL", "mistral-small-latest")

# Routing
MAX_CLARIFICATION_QUESTIONS = 3
STOPPING_PHRASES = ["non", "stop", "ça suffit", "comme tu veux"]

# Keyword extraction
MAX_KEYWORDS = 6

# Tavily search
TAVILY_MAX_RESULTS = 15
TAVILY_INPUT_LIMIT = 400

# RAG / Scraping
SCRAPE_TIMEOUT = 5
MIN_TEXT_LENGTH = 200
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
SIMILARITY_TOP_K = 5
