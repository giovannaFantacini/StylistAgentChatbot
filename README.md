# StylistAgentChatbot

## Descrição do Projeto
O StylistAgentChatbot é um agente inteligente desenvolvido para auxiliar usuários na análise de coloração pessoal, recomendando tons e cores que valorizam características individuais. Utiliza algoritmos de colorimetria e biotipo para sugerir paletas personalizadas, tornando o processo de consultoria de imagem mais acessível e interativo.

## LLM Utilizada
Este projeto utiliza o modelo de linguagem gpt-4.1 para processamento e geração das respostas do agente.

## Objetivo do Agente
O objetivo principal é automatizar a análise de coloração pessoal, oferecendo recomendações baseadas em dados e características do usuário. O agente busca democratizar o acesso à consultoria de imagem, tornando-a disponível de forma rápida e personalizada.

## Funcionamento

O agente possui as seguintes funções principais:

### 1. Análise de Coloração Pessoal
- Recebe uma imagem do rosto do usuário e utiliza o algoritmo KMeans para identificar as cores dominantes.
- Classifica as cores extraídas em estações (Primavera, Verão, Outono, Inverno) usando regras de colorimetria.
- Retorna uma paleta personalizada e estatísticas de temperatura, saturação e luminosidade das cores.
- **Atenção:** O algoritmo de colorimetria utiliza KMeans para extração das cores dominantes e tem acurácia média de 70%.

### 2. Classificação de Biotipo Corporal
- Solicita as medidas de ombro, cintura e quadril do usuário.
- Classifica o biotipo corporal (Triângulo, Triângulo Invertido, Ampulheta, Oval, Retângulo) com base nas proporções das medidas.

### 3. Recomendações Personalizadas
- Após obter a coloração pessoal e o biotipo, o agente sugere paletas de cores, modelagens, cortes e peças de roupa ideais.
- Gera links automáticos para lojas (C&A e Renner) com sugestões de peças adequadas ao perfil identificado.

O fluxo de atendimento segue rigorosamente as etapas:
#### 1. Solicitação de foto do rosto
<img width="1722" height="784" alt="SolicitacaoFoto" src="https://github.com/user-attachments/assets/bddeb0ae-111f-4d90-a5f0-c446fb022c8b" />

#### 2. Análise de coloração pessoal e Solicitação das medidas corporais
<img width="1732" height="783" alt="AnaliseColoracao" src="https://github.com/user-attachments/assets/ab48e1cf-845e-4bc3-829d-8fa432c573d4" />


#### 3. Classificação do biotipo

<img width="1720" height="771" alt="ClassificacaoBiotipo" src="https://github.com/user-attachments/assets/931ccbfc-1848-42bb-8007-71529e147542" />

#### 4. Recomendações completas de roupas e links
<img width="1723" height="777" alt="Recomendacoes" src="https://github.com/user-attachments/assets/9ede0f2e-03e5-40ef-ae1b-973752087cb1" />


## Demonstração em Vídeo

[Clique aqui para abrir o vídeo em nova aba](https://github.com/user-attachments/assets/45fefcfc-470e-41eb-a029-44b3e5f90a29)


## Referências
- [Guia rápido Gradio](https://www.gradio.app/guides/quickstart)
- [Documentação Azure AI Agents](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-agents-readme?view=azure-python)

## Como Executar

1. Instale as dependências listadas em `requirements.txt`.
2. Crie o agente executando o arquivo `stylish_agent.py`:
	```powershell
	python stylish_agent.py
	```
	O ID do agente será exibido no terminal. Copie esse ID e salve no arquivo `.env` na variável `AGENT_ID`.
3. Após salvar o `AGENT_ID` no `.env`, escolha a forma de execução:
	- Para rodar no terminal (chat):
	  ```powershell
	  python agent_chat.py
	  ```
	- Para rodar com interface gráfica (Gradio):
	  ```powershell
	  gradio agent_interface_gradio.py
	  ```
4. Siga as instruções na interface para interagir com o agente.

## Observações
- O vídeo de funcionamento está disponível em `assets/VideoFuncionamento`.
- O agente utiliza técnicas de colorimetria para análise, mas recomenda-se validação profissional para resultados mais precisos.
