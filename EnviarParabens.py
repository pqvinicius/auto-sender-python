# =============================================================================
# IMPORTAÇÕES NECESSÁRIAS
# =============================================================================
import pywhatkit
import time
import datetime
import pandas as pd
import sys
import json
import os
import logging
from tqdm import tqdm
from pathlib import Path

# =============================================================================
# ### OTIMIZAÇÃO APLICADA ###
# FUNÇÃO DE LOGGING MAIS ROBUSTA
# =============================================================================
def configurar_logging():
    """Configura o sistema de logging de forma explícita para mais controle."""
    try:
        # Define o nome e o caminho do arquivo de log
        log_file = 'relatorio_parabens_meta.log'
        
        # Pega o "logger" raiz para configurar
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Remove handlers antigos para evitar duplicação de logs se a função for chamada mais de uma vez
        if logger.hasHandlers():
            logger.handlers.clear()
            
        # Cria um handler para escrever no arquivo
        # O 'delay=True' adia a abertura do arquivo até a primeira escrita, o que pode evitar problemas de lock.
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8', delay=True)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Adiciona o handler de arquivo ao logger
        logger.addHandler(file_handler)
        
        print("✅ Sistema de logging configurado de forma robusta.")
        
    except Exception as e:
        # Se a configuração do log falhar, o programa não pode continuar de forma segura.
        print(f"❌ ERRO CRÍTICO AO CONFIGURAR O LOGGING: {e}")
        sys.exit(1)

# =============================================================================
# FUNÇÕES DE GERENCIAMENTO DE HISTÓRICO
# =============================================================================
def carregar_historico_envios():
    """Carrega o histórico de envios já realizados."""
    arquivo_historico = 'historico_parabens.json'
    if os.path.exists(arquivo_historico):
        try:
            with open(arquivo_historico, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erro ao carregar histórico: {e}")
            return {}
    return {}

def salvar_historico_envios(historico):
    """Salva o histórico de envios realizados."""
    try:
        with open('historico_parabens.json', 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar histórico: {e}")
        return False

def gerar_chave_envio(telefone, data_hoje_str):
    """Gera uma chave única para controlar envios por telefone por dia."""
    return f"{telefone}_{data_hoje_str}"

def ja_foi_enviado_hoje(telefone, historico):
    """Verifica se já foi enviado parabéns para este telefone hoje."""
    data_hoje_str = datetime.date.today().strftime('%Y-%m-%d')
    chave = gerar_chave_envio(telefone, data_hoje_str)
    return chave in historico

def registrar_envio(telefone, nome, historico):
    """Registra um envio realizado no histórico, incluindo o dia da semana."""
    data_hoje = datetime.date.today()
    chave = gerar_chave_envio(telefone, data_hoje.strftime('%Y-%m-%d'))
    historico[chave] = {
        'telefone': telefone, 'nome': nome,
        'data_envio': data_hoje.strftime('%Y-%m-%d'),
        'hora_envio': datetime.datetime.now().strftime('%H:%M:%S'),
        'dia_da_semana': data_hoje.weekday()
    }

def limpar_historico_antigo(historico, dias_manter=30):
    """Remove registros antigos do histórico (padrão: 30 dias)."""
    data_limite = datetime.date.today() - datetime.timedelta(days=dias_manter)
    data_limite_str = data_limite.strftime('%Y-%m-%d')
    chaves_antigas = [chave for chave, dados in historico.items() if dados.get('data_envio', '9999-12-31') < data_limite_str]
    for chave in chaves_antigas:
        del historico[chave]
    if chaves_antigas:
        print(f"🧹 Limpeza: {len(chaves_antigas)} registros antigos removidos.")

# =============================================================================
# FUNÇÕES DE DADOS E MENSAGEM
# =============================================================================
def carregar_dados(caminho_excel, nome_aba):
    """Carrega a planilha e prepara os dados."""
    try:
        df = pd.read_excel(caminho_excel, sheet_name=nome_aba)
        print(f"Planilha '{caminho_excel}' (aba: '{nome_aba}') carregada com {len(df)} registros.")
        df['Telefone_Formatado'] = df['Telefone'].astype(str).apply(lambda tel: f"+55{tel}" if not tel.startswith('+') else tel)
        df['primeiro_nome'] = df['Nome'].str.split().str[0].str.title()
        df_meta_batida = df[df['META_BATIDA'].str.upper() == 'SIM'].copy()
        print(f"Encontrados {len(df_meta_batida)} vendedores que bateram a meta diária.")
        return df_meta_batida
    except Exception as e:
        logging.error(f"Erro ao carregar dados: {e}")
        print(f"ERRO: {e}")
        return None

def montar_mensagem_parabens(nome):
    """Monta a mensagem de parabéns personalizada."""
    return f"Ei {nome}, Parabéns por bater a sua meta diária! 🎉"

def enviar_mensagem_whatsapp(telefone, mensagem):
    """Envia mensagem via PyWhatKit."""
    try:
        pywhatkit.sendwhatmsg_instantly(phone_no=telefone, message=mensagem, wait_time=25, tab_close=True, close_time=15)
        return True
    except Exception as e:
        logging.error(f"Falha no envio da API PyWhatKit para {telefone}: {e}")
        return False

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    configurar_logging()
    
    ARQUIVO_EXCEL = 'contatosvendedores.xlsx'
    NOME_DA_ABA = 'basededados'
    
    logging.info("--- INÍCIO DO PROCESSO DE PARABÉNS POR META BATIDA ---")
    print("🎯 Iniciando processo de parabenização por meta batida...")
    
    historico = carregar_historico_envios()
    limpar_historico_antigo(historico)
    df_parabens = carregar_dados(ARQUIVO_EXCEL, NOME_DA_ABA)
    
    if df_parabens is None or df_parabens.empty:
        if df_parabens is not None and df_parabens.empty:
            print("ℹ️ Nenhum vendedor bateu a meta hoje. Nada para enviar.")
            logging.info("Nenhum vendedor com META_BATIDA = 'SIM' encontrado.")
        sys.exit()
    
    sucessos = 0
    
    for indice, vendedor in tqdm(df_parabens.iterrows(), total=len(df_parabens), desc="Processando Vendedores"):
        nome = vendedor.get('primeiro_nome', 'N/A')
        telefone = vendedor.get('Telefone_Formatado', 'N/A')
        
        if ja_foi_enviado_hoje(telefone, historico):
            logging.info(f"DUPLICATA EVITADA - {nome} ({telefone}) já recebeu parabéns hoje.")
            continue
        
        mensagem = montar_mensagem_parabens(nome)
        print(f"\n🎉 Parabenizando: {nome} ({telefone})")
        
        if enviar_mensagem_whatsapp(telefone, mensagem):
            registrar_envio(telefone, nome, historico)
            logging.info(f"SUCESSO - Parabéns enviado para: {nome} ({telefone})")
            sucessos += 1
        else:
            logging.error(f"FALHA - Não foi possível enviar para: {nome} ({telefone})")
        
        if indice < len(df_parabens) -1:
            print("Aguardando 30 segundos...")
            time.sleep(30)
            
    if salvar_historico_envios(historico):
        print("\n💾 Histórico de envios atualizado com sucesso!")
    else:
        print("\n❌ Erro ao salvar histórico de envios!")
        
    logging.info("--- FIM DO PROCESSO DE PARABÉNS ---")