"""Centralized configuration constants for the ChatBotLangGraph application."""
import os

LLM_MODEL = os.getenv("LLM_MODEL", "mistral-small-latest")

MAX_CLARIFICATION_QUESTIONS = 3
STOPPING_PHRASES = ["non", "stop", "ça suffit", "comme tu veux"]

MAX_KEYWORDS = 6

TAVILY_MAX_RESULTS = 15
TAVILY_INPUT_LIMIT = 400

SCRAPE_TIMEOUT = 5
MIN_TEXT_LENGTH = 200
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
SIMILARITY_TOP_K = 5

MAX_INPUT_LENGTH = 2000

MAX_OUTPUT_FILES = 20
