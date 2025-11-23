"""
Chat interativo com o StylistAgent
Permite comunicação bidirecional no terminal
"""

import os
import time
import json
import base64
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from colorimetria import analisar_imagem
from biotipo import classificar_biotipo
from azure.ai.agents.models import FunctionTool, MessageInputTextBlock, MessageImageUrlParam, MessageInputImageUrlBlock, ListSortOrder

# Load environment variables
load_dotenv()

# Initialize client
project_endpoint = os.environ["PROJECT_ENDPOINT"]
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

# Create FunctionTool with both functions
functions = FunctionTool(functions=[analisar_imagem, classificar_biotipo])


def image_file_to_base64(path: str) -> str:
    """Convert image file to base64 string"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def process_tool_call(tool_call, image_base64=None):
    """Process a tool call and return the output"""
    tool_name = tool_call.function.name
    
    print(f"\n[Tool Call] {tool_name}")
    
    if tool_name == "analisar_imagem":
        try:
            output = analisar_imagem(image_base64)
            return json.dumps(output)
        except Exception as e:
            return json.dumps({"erro": str(e)})
    
    elif tool_name == "classificar_biotipo":
        try:
            args = json.loads(tool_call.function.arguments)
            output = classificar_biotipo(
                args["ombro"],
                args["cintura"],
                args["quadril"]
            )
            return json.dumps(output)
        except Exception as e:
            return json.dumps({"erro": str(e)})
    
    else:
        return json.dumps({"erro": f"Ferramenta desconhecida: {tool_name}"})


def chat_with_agent(agent_id: str = None):
    """Main chat loop with an existing agent"""
    
    with project_client:
        # Use existing agent or get agent_id from environment
        if not agent_id:
            agent_id = os.environ.get("AGENT_ID")
            if not agent_id:
                print("Erro: AGENT_ID não fornecido e não encontrado em variáveis de ambiente")
                print("Use: python agent_chat.py <agent_id>")
                return
        
        # Retrieve the existing agent
        agent = project_client.agents.get_agent(agent_id)
        print(f"\n✓ Agente conectado: {agent.id}")
        print(f"  Nome: {agent.name}")

        # Create thread for conversation
        thread = project_client.agents.threads.create()
        print(f"✓ Thread criada: {thread.id}\n")

        # Welcome message
        print("=" * 60)
        print("BEM-VINDO AO STYLIST AGENT")
        print("=" * 60)
        print("\nDigite 'sair' para encerrar a conversa")
        print("Digite 'imagem:<caminho>' para enviar uma imagem (ex: imagem:foto.png)")
        print("-" * 60 + "\n")

        # Chat loop
        while True:
            # Get user input
            user_input = input("Você: ").strip()

            if user_input.lower() == "sair":
                print("\n✓ Encerrando conversa...")
                break

            if not user_input:
                continue

            # Handle image input
            image_base64 = None
            if user_input.lower().startswith("imagem:"):
                image_path = user_input[7:].strip()
                if os.path.exists(image_path):
                    try:
                        image_base64 = image_file_to_base64(image_path)
                        img_data_url = f"data:image/png;base64,{image_base64}"
                        url_param = MessageImageUrlParam(url=img_data_url, detail="high")
                        content_blocks = [
                            MessageInputTextBlock(text="Analisando a imagem enviada..."),
                            MessageInputImageUrlBlock(image_url=url_param),
                        ]
                        user_input = "Enviei uma foto. Por favor, analise minha coloração pessoal."
                    except Exception as e:
                        print(f"Erro ao carregar imagem: {e}")
                        continue
                else:
                    print(f"Arquivo não encontrado: {image_path}")
                    continue
            else:
                content_blocks = [MessageInputTextBlock(text=user_input)]

            # Send message to agent
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=content_blocks
            )

            # Create run
            run = project_client.agents.runs.create(
                thread_id=thread.id,
                agent_id=agent.id
            )

            # Poll for completion
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(1)
                run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)

                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for tool_call in tool_calls:
                        output = process_tool_call(tool_call, image_base64)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": output
                        })

                    project_client.agents.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

            messages = project_client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
            for msg in messages:
                if msg.text_messages:
                    last_text = msg.text_messages[-1]
                    print(f"{msg.role}: {last_text.text.value}")
                            


if __name__ == "__main__":
    import sys
    
    agent_id = None
    if len(sys.argv) > 1:
        agent_id = sys.argv[1]
    
    chat_with_agent(agent_id)
