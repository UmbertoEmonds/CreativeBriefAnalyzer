from agentbrief.graph import graph
from langgraph.types import Command

config = {"configurable": {"thread_id": "1"}}

result = graph.invoke(
    {"input": input(
        """
        ╔══════════════════════════════════════════════════════╗
        ║         Analyseur de Brief - © Umberto Emonds        ║
        ╚══════════════════════════════════════════════════════╝

        Décris ton sujet. Nous l'analyserons pour toi et te 
        poserons des questions de clarification si nécessaire.
        Un document PDF pédagogique et structuré te sera 
        proposé après cet échange. 
        
        ➔ """
    ), "questions_answers": []},
    config=config
)

while "__interrupt__" in result:
    interrupt_value = result["__interrupt__"][0].value

    print(f"\nQuestion : {interrupt_value.content}")
    user_response = input("Votre réponse : ")

    result = graph.invoke(
        Command(resume=user_response),
        config=config
    )

print(f"\nPDF généré : {result['result_path']}")