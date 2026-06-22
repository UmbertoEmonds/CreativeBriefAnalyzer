"""
Markdown to HTML converter for the ChatBotLangGraph fiche generation.

Uses the Python-Markdown library with fenced_code and tables extensions.
"""
import re

import markdown as md


def _normalize_fenced_blocks(text: str) -> str:
    """
    Ensure fenced code block markers (```) are always on their own line.

    The Python-Markdown fenced_code extension requires opening and closing
    ``` to be isolated on their own line. This pre-processing step fixes
    LLM output that sometimes places ``` inline with surrounding text.
    """
    text = re.sub(r"([^\n])```", r"\1\n```", text)
    text = re.sub(r"```([^\n])", r"```\n\1", text)
    return text


def markdown_to_html(markdown_text: str) -> str:
    """
    Convert Markdown to HTML using the Python-Markdown library.

    Supports fenced code blocks, tables, bold, italic, inline code,
    headings, lists, and nested structures.

    Args:
        markdown_text: The raw Markdown content to convert.

    Returns:
        str: The generated HTML string.
    """
    if not markdown_text:
        return "<p>Aucun contenu généré.</p>"

    normalized = _normalize_fenced_blocks(markdown_text)

    return md.markdown(
        normalized,
        extensions=["fenced_code", "tables", "codehilite"],
    )
