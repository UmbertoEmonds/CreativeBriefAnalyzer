"""
Streamlit web UI for the ChatBotLangGraph brief analysis application.
"""
import streamlit as st
import uuid
import io
import contextlib
import threading
import queue
import time
import json
import os

st.set_page_config(
    page_title="Analyseur de Brief",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Loading splash (visible during subsequent import / cold start) ──

if "splash_done" not in st.session_state:
    st.markdown(
        """
        <style>
        .splash-outer {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            min-height: 80vh; font-family: system-ui, sans-serif;
        }
        .splash-spinner {
            width: 48px; height: 48px;
            border: 5px solid #e2e8f0;
            border-top-color: #4f46e5;
            border-radius: 50%;
            animation: splash-spin 0.8s linear infinite;
        }
        @keyframes splash-spin { to { transform: rotate(360deg); } }
        .splash-title {
            margin-top: 1.5rem; font-size: 1.5rem;
            font-weight: 700; color: #1e293b;
        }
        .splash-sub {
            margin-top: 0.5rem; color: #64748b; font-size: 0.95rem;
        }
        </style>
        <div class="splash-outer">
            <div class="splash-spinner"></div>
            <div class="splash-title">Analyseur de Brief</div>
            <div class="splash-sub">Chargement en cours...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.splash_done = True
    st.rerun()


# ── Heavy imports (after splash) ─────────────────────────────────────

from langgraph.types import Command
from agentbrief.graph import graph


# ── Custom stdout capture for live streaming ─────────────────────────

class LiveLogCapture(io.StringIO):
    def __init__(self):
        super().__init__()
        self._queue = queue.Queue()

    def write(self, text):
        if text.strip():
            self._queue.put_nowait(text)
        super().write(text)

    def flush(self):
        pass

    def drain(self):
        entries = []
        while not self._queue.empty():
            try:
                entries.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return entries


# ── Session-state defaults ───────────────────────────────────────────

_DEFAULTS = {
    "thread_id": lambda: str(uuid.uuid4()),
    "phase": "input",
    "brief": "",
    "logs": [],
    "question": None,
    "answer": "",
    "html_content": None,
    "result_path": None,
}

for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val() if callable(val) else val

if "config" not in st.session_state:
    st.session_state.config = {
        "configurable": {"thread_id": st.session_state.thread_id}
    }


_FOOTER_HTML = """
<div style="
    text-align: center; font-size: 0.75rem; color: #94a3b8;
    padding: 1rem 0 0.5rem; border-top: 1px solid #e2e8f0;
    margin-top: 2rem;
">
    © 2026 Umberto Emonds — Analyseur de Brief
</div>
"""


def reset_session():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def run_graph_in_thread(graph_input, config, capture, result_holder, error_holder):
    try:
        with contextlib.redirect_stdout(capture):
            result = graph.invoke(graph_input, config=config)
        result_holder.append(result)
    except Exception as exc:
        error_holder.append(exc)


# ── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Journal d'execution")
    log_container = st.container()
    with log_container:
        if st.session_state.logs:
            for entry in st.session_state.logs:
                st.code(entry, language="", line_numbers=False)
        else:
            st.caption("Les logs apparaitront ici en temps reel.")

    st.divider()
    st.caption(f"Session : `{st.session_state.thread_id[:8]}...`")
    st.caption("(c) 2026 Umberto Emonds")

    if st.session_state.phase in ("done",):
        if st.button("Nouvelle analyse", use_container_width=True):
            reset_session()
            st.rerun()


# ── Main content ─────────────────────────────────────────────────────

# INPUT
if st.session_state.phase == "input":
    st.markdown(
        """
        <style>
        .big-title {
            font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
        }
        .big-title span { color: #4f46e5; }
        .sub-title {
            color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem;
        }
        </style>
        <div class="big-title">Analyseur de <span>Brief</span></div>
        <div class="sub-title">
            Decris ton projet, nous l'analysons et generons une fiche
            pedagogique HTML structuree.
        </div>
        """,
        unsafe_allow_html=True,
    )

    brief = st.text_area(
        "Decris ton brief (sujet) :",
        height=140,
        placeholder=(
            "Exemple : Je dois former mon equipe de 5 personnes a la "
            "methode Scrum. Nous sommes une PME de 20 salaries dans "
            "l'edition de logiciels SaaS."
        ),
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Analyser", type="primary", use_container_width=True):
            if brief.strip():
                st.session_state.brief = brief.strip()
                st.session_state.phase = "processing"
                st.rerun()
            else:
                st.error("Veuillez entrer un brief avant de lancer l'analyse.")

# PROCESSING
elif st.session_state.phase == "processing":
    st.subheader("Analyse en cours...")

    status_box = st.status("L'IA travaille...", expanded=True)
    log_area = status_box.empty()

    if st.session_state.question is None:
        graph_input = {
            "input": st.session_state.brief,
            "questions_answers": [],
        }
    else:
        graph_input = Command(resume=st.session_state.answer)
        st.session_state.question = None
        st.session_state.answer = ""

    config = st.session_state.config
    capture = LiveLogCapture()
    result_holder: list = []
    error_holder: list = []

    thread = threading.Thread(
        target=run_graph_in_thread,
        args=(graph_input, config, capture, result_holder, error_holder),
        daemon=True,
    )
    thread.start()

    all_live_lines = []
    while thread.is_alive():
        new_lines = capture.drain()
        for line in new_lines:
            all_live_lines.append(line)
        if all_live_lines:
            display = "\n".join(all_live_lines[-25:])
            log_area.code(display, language="")
        time.sleep(0.15)

    for line in capture.drain():
        all_live_lines.append(line)

    if all_live_lines:
        merged = "\n".join(all_live_lines)
        st.session_state.logs.append(merged)
        log_area.code(merged, language="")

    if error_holder:
        status_box.update(label="Erreur", state="error")
        st.error(f"**Erreur lors de l'analyse** :\n\n{error_holder[0]}")
        if st.button("Reessayer"):
            reset_session()
            st.rerun()
        st.stop()

    result = result_holder[0]
    if "__interrupt__" in result:
        st.session_state.question = result["__interrupt__"][0].value.content
        st.session_state.phase = "clarification"
        status_box.update(label="Question de clarification", state="running")
        log_area.empty()
        st.rerun()

    path = result.get("result_path")
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            st.session_state.html_content = f.read()
        st.session_state.result_path = path

    st.session_state.phase = "done"
    status_box.update(label="Analyse terminee", state="complete", expanded=False)
    st.rerun()

# CLARIFICATION
elif st.session_state.phase == "clarification":
    st.info(f"**Question de clarification :**\n\n{st.session_state.question}")

    qid = str(abs(hash(st.session_state.question)) % 10_000_000)

    st.text_input(
        "Votre reponse :",
        key=f"clarification_{qid}",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Envoyer", type="primary", key=f"send_{qid}", use_container_width=True):
            val = st.session_state.get(f"clarification_{qid}", "").strip()
            if val:
                st.session_state.answer = val
                st.session_state.phase = "processing"
                st.rerun()
            else:
                st.warning("Veuillez entrer une reponse.")

# DONE
elif st.session_state.phase == "done":
    st.success("**Analyse terminee avec succes !**")

    if st.session_state.logs:
        with st.expander("Voir les logs d'execution (URLs, RAG, ...)", expanded=False):
            for entry in st.session_state.logs:
                st.code(entry, language="")

    if st.session_state.html_content:
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.download_button(
                "Telecharger le rapport HTML",
                data=st.session_state.html_content,
                file_name="rapport_analyse.html",
                mime="text/html",
                use_container_width=True,
            )

        st.divider()
        st.subheader("Apercu du rapport")
        st.markdown(
            """
            <style>
            .report-frame iframe {
                border: 2px solid #d1d5db !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
                overflow: hidden;
            }
            </style>
            <div class="report-frame"></div>
            """,
            unsafe_allow_html=True,
        )
        st.components.v1.html(
            st.session_state.html_content, height=800, scrolling=True
        )

    if st.session_state.result_path:
        st.info(
            f"Le fichier est egalement stocke sur le serveur sous "
            f"`{st.session_state.result_path}`."
        )

    st.button("Nouvelle analyse", type="primary", on_click=reset_session)

# ── Footer ───────────────────────────────────────────────────────────

st.markdown(_FOOTER_HTML, unsafe_allow_html=True)
