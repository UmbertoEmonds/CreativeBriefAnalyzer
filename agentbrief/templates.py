"""
HTML template rendering for the ChatBotLangGraph application.

Loads the external dashboard.html skeleton and injects state data
(brief, history, sources, body content) via string.Template.
"""
import json
import os
from datetime import datetime
from string import Template
from typing import List


def render_dashboard_template(brief_initial: str, history: list, sources: List[str], body_content: str) -> str:
    """
    Load an external HTML template and inject state data via string.Template.

    Builds the clarification history HTML and passes the sources as a
    JSON array for client-side rendering in the dashboard template.

    Args:
        brief_initial: The original user brief.
        history: List of QA dicts with 'q' and 'r' keys.
        sources: List of source URLs used during research.
        body_content: The final markdown body converted to HTML.

    Returns:
        str: The fully rendered HTML page as a string.
    """
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
        history_html = '<p class="sidebar-empty">Aucune clarification requise.</p>'

    base_dir = os.path.dirname(__file__)
    template_path = os.path.join(base_dir, "templates", "dashboard.html")

    with open(template_path, "r", encoding="utf-8") as f:
        html_skeleton = f.read()

    src = Template(html_skeleton)

    data = {
        "current_date": datetime.now().strftime('%d/%m/%Y'),
        "current_date_time": datetime.now().strftime('%d/%m/%Y à %H:%M'),
        "history_count": len(history),
        "nb_sources": len(sources),
        "brief_initial": brief_initial,
        "history_html": history_html,
        "sources_json": json.dumps(sources),
        "body_content": body_content,
    }

    return src.substitute(data)