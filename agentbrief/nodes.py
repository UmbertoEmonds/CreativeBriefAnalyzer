"""
Graph node implementations for the ChatBotLangGraph brief analysis workflow.

Each function corresponds to a node in the LangGraph state graph:
call_model, ask, retrieve, generate_final_data, and create_html.
"""
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate
from agentbrief.rag import build_retriever
from agentbrief.state import BriefState, QA
from langchain_tavily import TavilySearch
from datetime import datetime
import os

from agentbrief.templates import render_dashboard_template
from agentbrief.utils.md_to_html import markdown_to_html
from agentbrief.config import MAX_KEYWORDS, TAVILY_MAX_RESULTS, TAVILY_INPUT_LIMIT


_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Tu es un assistant expert dans l'analyse de briefs de projets. Ton role est de verifier si le brief contient les informations fondamentales necessaires pour commencer la redaction.

Le livrable final est toujours un dashboard HTML pedagogique. Ne pose donc jamais de question sur le format attendu.

## DONNEES
Brief a analyser : {user_input}
Historique des clarifications : {history_plain}

## DIRECTIVES STRICTES DE SECURITE :
- NE TENTE JAMAIS de definir, de developper, d'interpreter ou de deviner le sens des acronymes, des sigles, du jargon ou des termes specifiques au domaine du brief. Traite-les comme des concepts opaques sans chercher a les expliciter a ce stade.
- Concentre-toi exclusivement sur la structure du besoin : Sait-on a QUI s'adresse ce projet ? Sait-on QUEL est le but precis recherche ?

## GESTION DE L'HISTORIQUE DES CLARIFICATIONS :
- Chaque question deja posee et respondue dans l'historique doit etre consideree comme une information desormais acquise, meme si la reponse est partielle.
- Si une information fondamentale (public cible, objectif) a deja fait l'objet d'une question dans l'historique, ne la signale plus comme manquante.
- Identifie UNIQUEMENT les informations fondamentales qui n'ont PAS encore ete abordees dans l'historique.

Si le brief manque d'informations fondamentales pour commencer la redaction et que ces informations n'ont PAS encore ete demandees dans l'historique, commence ta reponse EXACTEMENT par le mot-cle : CLARIFICATION_NEEDED, suivi d'une breve justification de ce qui manque.
Sinon, fais directement une analyse complete de la demande.""")
])

_QUESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Tu es un analyste rigoureux. Pose UNE SEULE question a l'utilisateur pour combler le manque identifie dans l'analyse ci-dessous.

Analyse du brief : {analyse}

## REGLES STRICTES :
- INTERDICTION TOTALE de definir, de deviner, d'etendre ou d'expliciter le sens des acronymes, abreviations ou expressions specifiques utilises dans le brief.
- Ne repose pas une question sur une information deja fournie dans le brief utilisateur ({user_input}) ou deja abordee dans l'historique des clarifications.
- Ne demande pas le format de livrable (le systeme ne genere que du HTML).
- Formule une question unique courte et directe.
- Si tu mentionnes un terme issu du brief, utilise-le BRUT, sans l'expliquer.

Genere UNIQUEMENT la question, sans preambule.""")
])

_KEYWORD_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Extrais UNIQUEMENT les mots-cles techniques du sujet principal de ce brief.
Maximum {max_keywords} mots-cles. Exemple de format : 'LangGraph Python agents StateGraph'

Brief : {user_input}""")
])

_FINAL_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Tu es un expert en ingenierie pedagogique et un redacteur senior de premier ordre. Ta mission est de rediger une fiche de reference claire, didactique et immediatement actionnable sur le sujet demande. Tonalite : inspire toi de celle utilisée par l'utilisateur dans {user_input}, et les réponses dans {questions_answers}.

## CONTEXTE ET DONNEES SOURCES (Tes seules verites factuelles)
- Brief original de l'utilisateur : {user_input}
- Analyse initiale du besoin : {analyse}
- CLARIFICATIONS DE L'UTILISATEUR (A integrer imperativement pour calibrer le niveau et les attentes) :
{questions_answers}
- INFORMATIONS ISSUES DU RECHERCHE WEB / RAG (Ta seule source autorisee pour les faits, chiffres ou specificites) :
{rag_result}

## DIRECTIVES CRITIQUES ANTI-HALLUCINATION
1. ANCRAGE STRICT AUX FAITS : Toutes les definitions, donnees, caracteristiques ou methodologies propres au sujet DOIVENT etre extraites ou validees par les "Informations issues du RAG". Si une information cruciale n'est pas presente, ne l'invente pas. Prefere rester factuel. Cite chaque source RAG entre parentheses (Source: url) a chaque fois que tu utilises un fait issu du RAG.
2. PAS D'IMPROVISATION DE CONTENU : Ne cree jamais de faux exemples magiques, de fausses statistiques ou des elements imaginaires pour simplifier ton explication. Tout exemple doit refleter la realite concrete du domaine aborde.
3. ADAPTATION AU PROFIL : Utilise les "Clarifications obtenues" pour aligner precisement la complexite, le vocabulaire et les exemples de la fiche avec le profil et les besoins reels formules par l'utilisateur.

## MISSION
Redige une fiche complete, structuree et immediatement utilisable au format Markdown.
Ne genere PAS de preambule ni de meta-commentaires (commence directement au titre #).

## STRUCTURE OBLIGATOIRE

# [Titre accrocheur et descriptif du sujet]

## Introduction
Contexte et enjeux en 3-4 phrases. Explique pourquoi ce sujet est crucial pour le profil cible.

## Concepts cles / Piliers majeurs
Pour chaque concept ou pilier essentiel identifie : definition rigoureuse (appuyee sur le RAG), analogie concrete pour vulgariser, puis un exemple court. NE donne pas ici d'exemples detailles deployee.

## Exemples pratiques et Applications concretes
Fournis au moins 2 exemples detailles, realistes, entierement differents de ceux esquisses dans la section Concepts cles. Si pertinent, inclus templates, scripts, ou cas d'ecole commentes.

## Exploration approfondie / Analyse detaillee
Description complete des mecanismes sous-jacents, des nuances, des pieges a eviter, des limites et des cas d'usage avances du sujet.

## Guide de mise en oeuvre / Plan d'action pas a pas
Etapes numerotees, precises et chronologiques pour mettre en pratique le sujet.

## Points a retenir
5 a 7 points essentiels sous forme de liste a puces.

## Pour aller plus loin
2-3 pistes d'approfondissement reelles, lectures, outils ou concepts connexes.

## Mot de fin
Message d'encouragement personnalise et cible pour l'utilisateur.

## CONTRAINTES DE REDACTION SEVERES
- Utilise toute la richesse du Markdown (titres, gras, italique, listes, extrait de code, tableaux comparatifs si pertinent).
- Interdiction absolue de meubler avec du texte generique : chaque paragraphe doit apporter une valeur concrete et tangible.""")
])


def call_model(state: BriefState, llm):
    user_input = state["input"]
    history_plain = ""

    for msg in state["questions_answers"]:
        history_plain += f"{msg['q']} {msg['r']} \n"

    messages = _ANALYSIS_PROMPT.format_messages(
        user_input=user_input, history_plain=history_plain
    )
    print("Analyse du brief par l'IA...")
    response = llm.invoke(messages)
    return {"analyse": response.content}


def ask(state: BriefState, llm):
    print("Generation d'une question de clarification...")
    messages = _QUESTION_PROMPT.format_messages(analyse=state["analyse"], user_input=state["input"])
    question = llm.invoke(messages)
    approved = interrupt(question)

    return {"questions_answers": [QA(q=question.content, r=approved)]}


def retrieve(state: BriefState, llm):
    messages = _KEYWORD_PROMPT.format_messages(
        user_input=state["input"], max_keywords=MAX_KEYWORDS
    )
    print("Extraction des mots-cles...")
    query_response = llm.invoke(messages)
    print(f"   Mots-cles : {query_response.content}")

    print("Recherche web via Tavily...")
    tavily_tool = TavilySearch(max_results=TAVILY_MAX_RESULTS)

    results = tavily_tool.invoke(query_response.content[:TAVILY_INPUT_LIMIT])
    urls = [r["url"] for r in results["results"]]
    print(f"   {len(urls)} URL(s) trouvee(s)")

    rag_result = build_retriever(urls, state["input"])

    return {
        "rag_result": rag_result,
        "sources": urls,
    }


def generate_final_data(state: BriefState, llm):
    print("Redaction de la fiche pedagogique par l'IA...")
    messages = _FINAL_PROMPT.format_messages(
        user_input=state["input"],
        analyse=state["analyse"],
        questions_answers=state["questions_answers"],
        rag_result=state["rag_result"],
    )
    response = llm.invoke(messages)

    return {"final_data": response.content}


def create_html(state: BriefState):
    print("Generation du fichier HTML...")
    brief_initial = state.get("input", "N/A")
    history = state.get("questions_answers", [])
    raw_markdown = state.get("final_data", "")

    sources = state.get("sources", [])

    body_content_html = markdown_to_html(raw_markdown)

    final_html_output = render_dashboard_template(
        brief_initial=brief_initial,
        history=history,
        sources=sources,
        body_content=body_content_html
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/dashboard_{timestamp}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_html_output)

    return {"result_path": filename}
