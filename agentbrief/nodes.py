from langgraph.types import interrupt
from agentbrief.state import BriefState, QA
from langchain_tavily import TavilySearch
from fpdf import FPDF
from datetime import datetime
import os

from agentbrief.utils.md_to_pdf_parser import MarkdownPDFParser


def call_model(state: BriefState, llm):
    """
        Analyze a creative brief using an LLM.

        Builds a prompt combining the original brief and any previous
        clarification history, then invokes the LLM. If the brief lacks
        essential information (target audience, format, objective), the LLM
        is instructed to begin its response with 'CLARIFICATION_NEEDED'.

        Args:
            state (BriefState): The current graph state, containing the
                original brief ('input') and clarification history
                ('questions_answers').
            llm: A LangChain-compatible LLM instance.

        Returns:
            dict: A partial state update with the key 'analyse' containing
            the LLM's analysis as a string.
    """
    user_input = state["input"]
    history_plain = ""

    for msg in state["questions_answers"]:
        history_plain += f"{msg['q']} {msg['r']} \n"

    response = llm.invoke(
        f"""
        Tu es un assistant qui analyse des briefs créatifs.
        Analyse ce brief : {user_input}
        
        Historique des clarifications : {history_plain}

        Si le brief manque d'informations essentielles (cible, format, objectif), commence ta réponse par CLARIFICATION_NEEDED.
        Sinon, fais directement une analyse complète.
        """
    )
    return {"analyse": response.content}


def ask(state: BriefState, llm):
    """
        Generate a clarification question and interrupt the graph for user input.

        Uses the current analysis to generate a targeted question via the LLM,
        then suspends graph execution using LangGraph's interrupt mechanism.
        Once the user provides an answer, the question/answer pair is stored
        in the state.

        Args:
            state (BriefState): The current graph state, containing the
                LLM's analysis ('analyse').
            llm: A LangChain-compatible LLM instance.

        Returns:
            dict: A partial state update with the key 'questions_answers'
                containing a list with a single QA entry.
    """
    question = llm.invoke(
        f" {state['analyse']} A partir de ces informations, génère une question qui sera renvoyé directement à l'utilisateur.")
    approved = interrupt(question)

    return {"questions_answers": [QA(q=question.content, r=approved)]}

def search_web(state: BriefState):
    """
        Perform a web search based on the original brief.

        Uses the Tavily search API to retrieve relevant web sources.
        The query is truncated to 400 characters to comply with Tavily's
        API limit. Results are formatted as a readable string with
        source URLs and content snippets.

        Args:
            state (BriefState): The current graph state, containing the
                original brief ('input').

        Returns:
            dict: A partial state update with the key 'web_result' containing the formatted search results as a string.
    """
    tavily_tool = TavilySearch(max_results=3)

    # Tavily limit
    query = state["input"][:400]

    results = tavily_tool.invoke(query)

    items = results["results"]
    formatted_results = "\n".join([
        f"Source: {res['url']}\nContenu: {res['content']}\n"
        for res in items
    ])

    return {"web_result": formatted_results}

def generate_final_data(state: BriefState, llm):
    """
        Generate the final structured content for the PDF sheet.

        Combines all available state information (brief, analysis,
        clarifications, web research) into a comprehensive prompt and
        invokes the LLM to produce the final fiche content. The output
        includes key concepts, concrete examples, takeaways, and an
        encouraging message for the target audience.

        Args:
            state (BriefState): The current graph state containing 'input',
                'analyse', 'questions_answers', and 'web_result'.
            llm: A LangChain-compatible LLM instance.

        Returns:
            dict: A partial state update with the key 'final_data' containing the generated content as a string.
    """
    response = llm.invoke(
        f"""
        Brief : {state['input']} 
        Analyse : {state['analyse']} 
        Clarifications : {state['questions_answers']} 
        Recherche web : {state['web_result']}
        
        À partir de ces informations, génère directement le contenu complet de la fiche au format markdown.
        La fiche doit contenir les sections suivantes, avec le contenu réel :
        - Titre
        - Concepts clés avec explications simples
        - Exemples concrets
        - Points à retenir
        - Un mot d'encouragement à destination du profil cible
        """
    )

    return {"final_data": response.content}

def create_pdf(state: BriefState):
    """
        Generate a PDF file from the final structured content.

        Creates a formatted A4 PDF document using fpdf2 with Unicode font
        support. The PDF includes a centered title header followed by the
        full content of the fiche. The output file is timestamped and saved
        to the current working directory.

        Args:
            state (BriefState): The current graph state containing
                'final_data' with the content to render.

        Returns:
            dict: A partial state update with the key 'result_path'
                containing the filename of the generated PDF.
    """
    pdf = FPDF()
    pdf.add_page()

    # Import de la police pour gérer les caractères spéciaux / accents
    pdf.add_font("ArialUnicode", "", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")

    """
    # Titre principal du document
    pdf.set_font('ArialUnicode', size=22)
    pdf.cell(0, 15, "Fiche de Brief Stratégique", ln=True, align='C')
    pdf.ln(5)
    """

    # Récupération du contenu Markdown
    content = state.get("final_data", "Aucun contenu généré.")

    # Utilisation du parseur personnalisé
    parser = MarkdownPDFParser(pdf, font_name="ArialUnicode")
    parser.parse(content)

    # Sauvegarde avec Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/brief_{timestamp}.pdf"

    pdf.output(filename)

    return {"result_path": filename}