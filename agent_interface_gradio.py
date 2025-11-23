import os 
import time
import json
import base64
import gradio as gr
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from colorimetria import analisar_imagem
from biotipo import classificar_biotipo
from azure.ai.agents.models import (
    FunctionTool,
    MessageInputTextBlock,
    MessageImageUrlParam,
    MessageInputImageUrlBlock,
    ListSortOrder,
)

# Carregar variáveis de ambiente
load_dotenv()
project_endpoint = os.environ["PROJECT_ENDPOINT"]
agent_id = os.environ.get("AGENT_ID")

project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

functions = FunctionTool(functions=[analisar_imagem, classificar_biotipo])


def image_file_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def process_tool_call(tool_call, image_base64=None):
    tool_name = tool_call.function.name
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
                args["quadril"],
            )
            return json.dumps(output)
        except Exception as e:
            return json.dumps({"erro": str(e)})
    else:
        return json.dumps({"erro": f"Ferramenta desconhecida: {tool_name}"})


def gradio_agent_chat(message, history):
    """
    Com multimodal=True, `message` vem como:
    {
        "text": "mensagem do usuário ou None",
        "files": ["caminho_arquivo_1", "caminho_arquivo_2", ...]
    }

    Esta função:
    - Envia a mensagem (texto + imagem) para o agente
    - Espera o run terminar (incluindo tool calls)
    - Busca APENAS a última resposta do agente e retorna um único `yield`
    """

    # Inicializar thread e agente na primeira mensagem
    if not hasattr(gradio_agent_chat, "thread"):
        gradio_agent_chat.thread = project_client.agents.threads.create()
    if not hasattr(gradio_agent_chat, "agent"):
        gradio_agent_chat.agent = project_client.agents.get_agent(agent_id)

    thread = gradio_agent_chat.thread
    agent = gradio_agent_chat.agent

    # Extrair texto e arquivos do message (multimodal)
    if isinstance(message, dict):
        user_text = (message.get("text") or "").strip()
        files = message.get("files") or []
    else:
        # fallback caso multimodal não esteja ativo por algum motivo
        user_text = str(message or "").strip()
        files = []

    content_blocks = []
    image_base64 = None

    # 1) Caso tenha arquivos enviados (imagem)
    if files:
        image_path = files[0]  # pega o primeiro arquivo
        try:
            image_base64 = image_file_to_base64(image_path)
            img_data_url = f"data:image/png;base64,{image_base64}"
            url_param = MessageImageUrlParam(url=img_data_url, detail="high")

            # Se o usuário também mandou texto, incluímos junto
            if user_text:
                content_blocks.append(MessageInputTextBlock(text=user_text))
            else:
                content_blocks.append(
                    MessageInputTextBlock(
                        text="Enviei uma foto. Por favor, analise minha coloração pessoal."
                    )
                )

            content_blocks.append(MessageInputImageUrlBlock(image_url=url_param))
        except Exception as e:
            # Garante pelo menos um yield (evita StopAsyncIteration)
            yield f"Erro ao carregar a imagem enviada: {e}"
            return

    # 2) Caso não tenha arquivos, mas use o comando antigo "imagem:<caminho>"
    elif user_text.lower().startswith("imagem:"):
        image_path = user_text[7:].strip()
        if os.path.exists(image_path):
            try:
                image_base64 = image_file_to_base64(image_path)
                img_data_url = f"data:image/png;base64,{image_base64}"
                url_param = MessageImageUrlParam(url=img_data_url, detail="high")

                content_blocks = [
                    MessageInputTextBlock(
                        text="Enviei uma foto. Por favor, analise minha coloração pessoal."
                    ),
                    MessageInputImageUrlBlock(image_url=url_param),
                ]
            except Exception as e:
                yield f"Erro ao carregar imagem: {e}"
                return
        else:
            yield f"Arquivo não encontrado: {image_path}"
            return

    # 3) Apenas texto normal
    else:
        content_blocks = [MessageInputTextBlock(text=user_text or "")]

    # Enviar mensagem ao agente
    project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=content_blocks,
    )

    # Criar run
    run = project_client.agents.runs.create(
        thread_id=thread.id,
        agent_id=agent.id,
    )

    terminal_statuses = ["succeeded", "completed", "failed", "cancelled", "expired"]

    # Espera o run terminar, tratando tool calls se necessário
    while True:
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for tool_call in tool_calls:
                output = process_tool_call(tool_call, image_base64)
                tool_outputs.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": output,
                    }
                )
            project_client.agents.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs,
            )

        if run.status in terminal_statuses:
            break

        time.sleep(1)
        run = project_client.agents.runs.get(
            thread_id=thread.id,
            run_id=run.id,
        )

    # Buscar APENAS a última mensagem do agente
    last_agent_text = None
    messages = project_client.agents.messages.list(
        thread_id=thread.id,
        order=ListSortOrder.DESCENDING,  # mais recentes primeiro
    )

    for msg in messages:
        # Ignora mensagens do usuário
        if msg.role and msg.role.lower() == "user":
            continue
        if msg.text_messages:
            last_text_block = msg.text_messages[-1]
            last_agent_text = last_text_block.text.value
            break

    if last_agent_text:
        # Sem prefixar com role
        yield last_agent_text
    else:
        # fallback pra evitar StopAsyncIteration
        yield "Não foi possível obter uma resposta do agente. Verifique a configuração ou os logs."


# Interface Gradio estilo chatbot (janela maior + multimodal)
chatbot = gr.ChatInterface(
    fn=gradio_agent_chat,
    title="Stylist Agent Chatbot",
    description=(
        "Converse com o Stylist Agent.\n"
        "Você pode enviar mensagens de texto e anexar imagens para análise de coloração e biotipo."
    ),
    multimodal=True,
    textbox=gr.MultimodalTextbox(
        file_count="multiple",
        file_types=["image"],
        placeholder="Digite sua mensagem e/ou envie uma imagem...",
        show_label=False,
    ),
    chatbot=gr.Chatbot(
        height=600,  # aumenta a 'janela' do chat
    ),
)

if __name__ == "__main__":
    chatbot.launch(debug=True)
