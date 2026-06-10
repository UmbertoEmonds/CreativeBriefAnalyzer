from langgraph.types import interrupt
from agentbrief.rag import build_retriever
from agentbrief.state import BriefState, QA
from langchain_tavily import TavilySearch
from datetime import datetime
import os

from agentbrief.templates import render_dashboard_template
from agentbrief.utils.md_to_html import markdown_to_html


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
        Tu es un assistant expert dans l'analyse de briefs de projets. Ton unique rôle est de vérifier si le brief contient les informations fondamentales nécessaires pour concevoir le livrable (qui est le public cible, quel est l'objectif principal, quel est le format ou le type de document attendu).
        
        ## DONNÉES
        Brief à analyser : {user_input}
        Historique des clarifications : {history_plain}

        ## DIRECTIVES STRICTES DE SÉCURITÉ :
        - NE TENTE JAMAIS de définir, de développer, d'interpréter ou de deviner le sens des acronymes, des sigles, du jargon ou des termes spécifiques au domaine du brief. Traite-les comme des concepts opaques sans chercher à les expliciter à ce stade.
        - Concentre-toi exclusivement sur la structure du besoin : Sait-on à QUI s'adresse ce projet ? Sait-on QUEL est le but précis recherché ?

        Si le brief manque d'informations fondamentales pour commencer la rédaction, commence ta réponse EXACTEMENT par le mot-clé : CLARIFICATION_NEEDED
        Sinon, fais directement une analyse complète de la demande.
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
        f"""Tu es un analyste rigoureux. Ton rôle est de poser une unique question à l'utilisateur pour combler les manques essentiels du brief identifiés dans l'analyse ci-dessous.

        Analyse du brief : {state['analyse']}

        ## RÈGLE DE SÉCURITÉ ABSOLUE :
        - INTERDICTION TOTALE de définir, de deviner, d'étendre ou d'expliciter le sens des acronymes, abréviations ou expressions spécifiques utilisés dans le brief.
        - Ne fais aucune supposition sur le sens des mots. Si tu dois mentionner un terme ou un acronyme issu du brief, utilise-le strictement BRUT, tel quel, sans jamais essayer de l'expliquer.
        - Formule une question courte, neutre, polie et directe.

        Génère UNIQUEMENT la question à renvoyer à l'utilisateur :"""
    )
    approved = interrupt(question)

    return {"questions_answers": [QA(q=question.content, r=approved)]}

def retrieve(state: BriefState, llm):
    query_response = llm.invoke(
        f"""Extrais UNIQUEMENT les mots-clés techniques du sujet principal de ce brief.
        Ignore le format de livrable (carte mentale, PDF, slides...).
        Maximum 5 mots-clés. Exemple de format : 'LangGraph Python agents StateGraph'

        Brief : {state['input']}"""
    )

    # Tavily input limit : 400
    tavily_tool = TavilySearch(max_results=10)

    results = tavily_tool.invoke(query_response.content[:400])
    urls = [r["url"] for r in results["results"]]

    rag_result = build_retriever(urls, state["input"])

    return {
        "rag_result": rag_result,
        "sources": urls,
    }

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
        f"""Tu es un expert en ingénierie pédagogique et un rédacteur senior de premier ordre. Ta mission est de rédiger une fiche de référence d'une rigueur absolue, claire, didactique et immédiatement actionnable sur le sujet demandé.
        
        ## CONTEXTE ET DONNÉES SOURCES (Tes seules vérités factuelles)
        - Brief original de l'utilisateur : {state['input']}
        - Analyse initiale du besoin : {state['analyse']}
        
        - CLARIFICATIONS DE L'UTILISATEUR (À intégrer impérativement pour calibrer le niveau et les attentes) : 
        {state['questions_answers']}
        
        - INFORMATIONS ISSUES DU RECHERCHE WEB / RAG (Ta seule source autorisée pour les faits, chiffres ou spécificités) : 
        {state['rag_result']}
        
        ## DIRECTIVES CRITIQUES ANTI-HALLUCINATION
        1. ANCRAGE STRICT AUX FAITS : Toutes les définitions, données, caractéristiques ou méthodologies propres au sujet DOIVENT être extraites ou validées par les "Informations issues du RAG". Si une information cruciale n'est pas présente, ne l'invente pas. Préfère rester factuel plutôt que d'inventer des fonctionnalités, des concepts ou des données fictives.
        2. PAS D'IMPROVISATION DE CONTENU : Ne crée jamais de faux exemples magiques, de fausses statistiques ou des éléments imaginaires pour simplifier ton explication. Tout exemple doit refléter la réalité concrète du domaine abordé (qu'il soit technique, marketing, managérial, etc.).
        3. ADAPTATION AU PROFIL : Utilise les "Clarifications obtenues" pour aligner précisément la complexité, le vocabulaire et les exemples de la fiche avec le profil et les besoins réels formulés par l'utilisateur.
        
        ## MISSION
        Rédige une fiche complète, structurée et immédiatement utilisable au format Markdown.
        Ne génère PAS de préambule ni de méta-commentaires (commence directement au titre #).
        
        ## STRUCTURE OBLIGATOIRE
        
        # [Titre accrocheur et descriptif du sujet]
        
        ## Introduction
        Contexte et enjeux en 3-4 phrases. Explique pourquoi ce sujet est crucial pour le profil cible en t'appuyant directement sur le brief et les clarifications.
        
        ## Concepts clés / Piliers majeurs
        Pour chaque concept ou pilier essentiel identifié : 
        - Définition ou explication rigoureuse (appuyée sur le RAG)
        - Analogie concrète pour vulgariser
        - Exemple d'application réelle adapté au contexte de l'utilisateur.
        
        ## Exemples pratiques et Applications concrètes
        Fournis au moins 2 exemples détaillés, réalistes et applicables immédiatement.
        Selon la nature du sujet, inclus des livrables concrets (ex: templates, scripts, structures de messages, cas d'école vécus, simulations) avec des explications claires et commentées.
        
        ## Exploration approfondie / Analyse détaillée
        Description complète des mécanismes sous-jacents, des nuances, des pièges à éviter, des limites et des cas d'usage avancés du sujet.
        
        ## Guide de mise en œuvre / Plan d'action pas à pas
        Étapes numérotées, précises et chronologiques pour mettre en pratique le sujet. Chaque étape doit être suffisamment détaillée pour être suivie sans ambiguïté par le lecteur.
        
        ## Points à retenir
        5 à 7 points essentiels sous forme de liste à puces.
        
        ## Pour aller plus loin
        2-3 pistes d'approfondissement réelles, lectures, outils ou concepts connexes pour prolonger l'apprentissage.
        
        ## Mot de fin
        Message d'encouragement personnalisé et ciblé pour l'utilisateur et la réussite de son projet.
        
        ## CONTRAINTES DE RÉDACTION SÉVÈRES
        - Utilise toute la richesse du Markdown (titres, gras, italique, listes, tableaux comparatifs si pertinent).
        - Interdiction absolue de meubler avec du texte générique : chaque paragraphe doit apporter une valeur concrète et tangible.
        """
    )

    return {"final_data": response.content}


def create_html(state: BriefState):
    # 1. Extraction des données de l'état global du graphe
    brief_initial = state.get("input", "N/A")
    history = state.get("questions_answers", [])
    raw_markdown = state.get("final_data", "")

    # Récupération de la liste de chaînes (URLs) depuis le State
    sources = state.get("sources", [])

    # 2. Conversion du Markdown brut en éléments HTML via le parseur ligne par ligne
    body_content_html = markdown_to_html(raw_markdown)

    # 3. Injection dans le template HTML externe via string.Template
    final_html_output = render_dashboard_template(
        brief_initial=brief_initial,
        history=history,
        sources=sources,
        body_content=body_content_html
    )

    # 4. Enregistrement sécurisé du fichier sur le disque (.html)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/dashboard_{timestamp}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_html_output)

    # On retourne le chemin du fichier pour que le graph ou main.py puisse le lire à la fin
    return {"result_path": filename}