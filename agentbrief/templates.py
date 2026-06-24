"""HTML template rendering: injects state data into dashboard.html via string.Template."""
import html
import os
from datetime import datetime
from string import Template
from typing import List


def render_dashboard_template(brief_initial: str, history: list, sources: List[str], body_content: str) -> str:
    """Build the final HTML page by substituting state data into the template."""
    history_html = ""
    if history:
        for item in history:
            history_html += f"""
            <div class="history-item">
                <div class="history-q">Q: {html.escape(item['q'])}</div>
                <div class="history-a">R: {html.escape(item['r'])}</div>
            </div>
            <br>
            """
    else:
        history_html = '<p style="font-size: 9.5pt; color: #9ca3af;">Aucune clarification requise.</p>'

    sources_html = ""
    if sources:
        for url in sources:
            safe_url = html.escape(url)
            display_url = safe_url if len(safe_url) < 45 else safe_url[:42] + "..."
            sources_html += f'<div><a href="{safe_url}" class="source-link" target="_blank" title="{safe_url}">{display_url}</a></div>\n'
    else:
        sources_html = '<p style="font-size: 9.5pt; color: #9ca3af;">Aucune source consultée.</p>'

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
        "brief_initial": html.escape(brief_initial),
        "history_html": history_html,
        "sources_html": sources_html,
        "body_content": body_content
    }

    return src.substitute(data)
