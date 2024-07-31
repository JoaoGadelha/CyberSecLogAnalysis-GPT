import openai
import re
from dotenv import load_dotenv
import os
import time

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Defina sua chave da API aqui
openai.api_key = os.getenv('OPENAI_API_KEY')

# Preço por 1.000.000 tokens em dólares
preco_input_por_milhao = 10.00  # $10.00 por 1M tokens de entrada
preco_output_por_milhao = 30.00 # $30.00 por 1M tokens de saída

# Função para enviar requisição para a API do GPT
def enviar_para_gpt(messages, max_tokens=1500):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=max_tokens
    )
    content = response['choices'][0]['message']['content']
    usage = response['usage']
    return content, usage

# Função para extrair o número de passos da resposta
def extrair_numero_de_passos(resposta):
    match = re.search(r'\[n(?:\\?_)?passos:(\d+)\]', resposta)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Número de passos não encontrado na resposta.")

# Função para salvar o conteúdo em um arquivo
def salvar_em_arquivo(nome_arquivo, conteudo):
    with open(nome_arquivo, 'w', encoding='utf-8') as file:
        file.write(conteudo)

# Função principal para executar o processo
def gerar_relatorio_detalhado(prompt, logs):
    # Início do cronômetro total
    inicio_tempo_total = time.time()

    # Prompt inicial para identificar os passos
    prompt_inicial = [
        {"role": "user", "content": prompt},
        {"role": "user", "content": logs}
    ]
    
    # Envia a primeira requisição para obter o relatório inicial e o número de passos
    resposta_inicial, usage_inicial = enviar_para_gpt(prompt_inicial)
    print("Resposta inicial:", resposta_inicial)
    
    # Cria a pasta para armazenar os arquivos
    pasta_relatorio = 'relatorio_gerado_pelo_GPT'
    os.makedirs(pasta_relatorio, exist_ok=True)
    
    # Salva a resposta inicial
    salvar_em_arquivo(os.path.join(pasta_relatorio, 'relatorio_inicial.txt'), resposta_inicial)
    
    # Extrai o número de passos da resposta inicial
    numero_de_passos = extrair_numero_de_passos(resposta_inicial)
    print(f"Número de passos identificados: {numero_de_passos}")
    
    # Listas para armazenar o tempo de cada passo, tokens usados e custo
    tempos_passos = []
    tokens_usados = []
    custos_passos = []
    custo_total = 0.0
    
    # Para cada passo, envia uma requisição de expansão e salva a resposta
    for i in range(1, numero_de_passos + 1):
        inicio_tempo_passo = time.time()  # Início do cronômetro para o passo i
        
        prompt_expansao = [
            {"role": "assistant", "content": resposta_inicial},
            {"role": "user", "content": f"Por favor, expanda a descrição do Passo {i}. Inclua detalhes sobre as ações realizadas, vulnerabilidades exploradas e sugestões de mitigação."}
        ]
        resposta_expansao, usage_expansao = enviar_para_gpt(prompt_expansao)
        print(f"\nExpansão do Passo {i}:\n{resposta_expansao}\n")
        salvar_em_arquivo(os.path.join(pasta_relatorio, f'expansao_passo_{i}.txt'), resposta_expansao)
        
        fim_tempo_passo = time.time()  # Fim do cronômetro para o passo i
        duracao_passo = fim_tempo_passo - inicio_tempo_passo
        tempos_passos.append(duracao_passo)  # Armazena o tempo do passo
        
        # Calcula o custo para este passo
        prompt_tokens = usage_expansao['prompt_tokens']
        completion_tokens = usage_expansao['completion_tokens']
        total_tokens = usage_expansao['total_tokens']
        tokens_usados.append(total_tokens)

        custo_input = (prompt_tokens / 1000000) * preco_input_por_milhao
        custo_output = (completion_tokens / 1000000) * preco_output_por_milhao
        custo_passo = custo_input + custo_output
        custos_passos.append(custo_passo)
        custo_total += custo_passo
        
        print(f"Tempo para o Passo {i}: {duracao_passo:.2f} segundos")
        print(f"Tokens usados no Passo {i}: {total_tokens}")
        print(f"Custo do Passo {i}: ${custo_passo:.5f}")
    
    # Fim do cronômetro total
    fim_tempo_total = time.time()
    duracao_total = fim_tempo_total - inicio_tempo_total
    print(f"Tempo total para geração do relatório: {duracao_total:.2f} segundos")
    print(f"Custo total estimado: ${custo_total:.5f}")
    
    # Exibir tempos individuais e tokens usados
    for i, (tempo, tokens, custo) in enumerate(zip(tempos_passos, tokens_usados, custos_passos), start=1):
        print(f"Tempo do Passo {i}: {tempo:.2f} segundos")
        print(f"Tokens usados no Passo {i}: {tokens}")
        print(f"Custo estimado do Passo {i}: ${custo:.5f}")
    
    # Salvar relatório de performance
    relatorio_performance = os.path.join(pasta_relatorio, 'api_performance_report.txt')
    with open(relatorio_performance, 'w', encoding='utf-8') as report_file:
        report_file.write(f"Tempo total para geração do relatório: {duracao_total:.2f} segundos\n")
        report_file.write(f"Custo total estimado: ${custo_total:.5f}\n\n")
        for i, (tempo, tokens, custo) in enumerate(zip(tempos_passos, tokens_usados, custos_passos), start=1):
            report_file.write(f"Passo {i}:\n")
            report_file.write(f"  Tempo: {tempo:.2f} segundos\n")
            report_file.write(f"  Tokens usados: {tokens}\n")
            report_file.write(f"  Custo estimado: ${custo:.5f}\n\n")

# Ler os logs do arquivo 'logs_experimento1'
def ler_logs_do_arquivo(nome_arquivo):
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        raise RuntimeError(f"Erro ao ler o arquivo {nome_arquivo}: {e}")

# Caminho para o arquivo de logs
nome_arquivo_logs = 'logs_experimento2'

# Lê os logs do arquivo
logs = ler_logs_do_arquivo(nome_arquivo_logs)

# Definição do prompt com instruções detalhadas
prompt = (
    "Você receberá uma série de logs de segurança da informação, originários de diversas fontes como firewalls, sistemas de monitoramento de banco de dados, registros de servidores web e ferramentas de detecção de intrusão. "
    "Sua tarefa será analisar esses logs em ordem cronológica para identificar e descrever as atividades de um possível atacante através de um relatório em LaTeX. Por favor, concentre-se em:\n\n"
    "- Descrever as ações do ataque como o exemplo:\n\"[timestamp] O atacante acessou o sistema tal, abriu o arquivo tal, subiu uma webshell, se autenticou no serviço tal, ...\"\n"
    "- Determinar a sequência cronológica dos eventos registrados nos logs.\n"
    "- Identificar padrões anômalos ou atividades suspeitas em cada conjunto de logs.\n"
    "- Explicar a relevância de cada atividade suspeita em relação ao cenário geral do ataque.\n"
    "- Sugerir quais técnicas e táticas o atacante pode estar usando, com base nos padrões observados.\n"
    "- Avaliar potenciais vulnerabilidades ou falhas de segurança que o atacante explorou.\n"
    "- Propor medidas de resposta ou mitigação para os incidentes identificados.\n\n"
    "- Escape underlines no código LaTeX.\n"
    "- Não diga nada além do código latex do relatório.\n"
    "- Não precisa gerar um preâmbulo, já comece a partir de \\begin{document}.\n"
    "- Diga o número de passos do ataque no seguinte formato: [n_passos:X], onde X é o número de passos. Por exemplo, se no ataque teve uma varredura de portas, uma injeção SQL e uma escalada de privilégios, então X = 3, resultando em [n_passos:3]. Após dizer o número de passos, escreva uma array com os nomes dos passos, para justificar sua resposta. Por exemplo, [n_passos:3] [varredura_de_portas, injecao_SQL, escalada_de_privilegios]"
)

# Gera o relatório detalhado
gerar_relatorio_detalhado(prompt, logs)
