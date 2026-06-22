"""
HTML template rendering for the ChatBotLangGraph application.

Loads the external dashboard.html skeleton and injects state data
(brief, history, sources, body content) via string.Template.
"""
import os
from datetime import datetime
from string import Template
from typing import List


def render_dashboard_template(brief_initial: str, history: list, sources: List[str], body_content: str) -> str:
    """
    Load an external HTML template and inject state data via string.Template.

    Builds the clarification history HTML and the sources HTML list, then
    reads the dashboard.html skeleton template and substitutes all
    placeholders with the provided data.

    Args:
        brief_initial: The original user brief.
        history: List of QA dicts with 'q' and 'r' keys.
        sources: List of source URLs used during research.
        body_content: The final markdown body converted to HTML.

    Returns:
        str: The fully rendered HTML page as a string.
    """
    # 1. Generate the clarification history as HTML
    history_html = ""
    if history:
        for item in history:
            history_html += f"""
            <div class="history-item">
                <div class="history-q">Q: {item['q']}</div>
                <div class="history-a">R: {item['r']}</div>
            </div>
            """
    else:
        history_html = '<p style="font-size: 9.5pt; color: #9ca3af;">Aucune clarification requise.</p>'

    # 2. Generate the clickable source list as HTML
    sources_html = ""
    if sources:
        for url in sources:
            display_url = url if len(url) < 45 else url[:42] + "..."
            sources_html += f'<a href="{url}" class="source-link" target="_blank" title="{url}">🔗 {display_url}</a>\n'
    else:
        sources_html = '<p style="font-size: 9.5pt; color: #9ca3af;">Aucune source consultée.</p>'

    # 3. Read the external HTML template
    base_dir = os.path.dirname(__file__)
    template_path = os.path.join(base_dir, "templates", "dashboard.html")

    with open(template_path, "r", encoding="utf-8") as f:
        html_skeleton = f.read()

    # 4. Use Template instead of .format()
    src = Template(html_skeleton)

    # Pass variables into a substitution dictionary
    data = {
        "current_date": datetime.now().strftime('%d/%m/%Y'),
        "current_date_time": datetime.now().strftime('%d/%m/%Y à %H:%M'),
        "history_count": len(history),
        "nb_sources": len(sources),
        "brief_initial": brief_initial,
        "history_html": history_html,
        "sources_html": sources_html,
        "body_content": body_content
    }

    # Safely replace keys starting with $
    return src.substitute(data)