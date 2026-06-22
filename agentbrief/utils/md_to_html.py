"""
Markdown to HTML converter for the ChatBotLangGraph fiche generation.

Uses the Python-Markdown library with fenced_code and tables extensions.
"""
import markdown as md


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

    return md.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "codehilite"],
    )
