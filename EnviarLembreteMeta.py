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
# FUNÇÃO DE LOGGING
# =============================================================================
def configurar_logging():
    # ### ALTERADO ### - Novo nome para o arquivo de log
    log_file = 'relatorio_lembrete.log'
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8', delay=True)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    print(f"✅ Sistema de logging configurado. Logs salvos em '{log_file}'.")

# =============================================================================
# FUNÇÕES DE GERENCIAMENTO DE HISTÓRICO
# =============================================================================
def carregar_historico_envios():
    # ### ALTERADO ### - Novo nome para o arquivo de histórico
    arquivo_historico = 'historico_lembretes.json'
    if os.path.exists(arquivo_historico):
        try:
            with open(arquivo_historico, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erro ao carregar histórico de lembretes: {e}")
            return {}
    return {}

def salvar_historico_envios(historico):
    # ### ALTERADO ### - Novo nome para o arquivo de histórico
    arquivo_historico = 'historico_lembretes.json'
    try:
        with open(arquivo_historico, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar histórico de lembretes: {e}")
        return False

# Funções 'gerar_chave_envio' e 'ja_foi_enviado_hoje' são as mesmas
def gerar_chave_envio(telefone, data_hoje_str):
    return f"{telefone}_{data_hoje_str}"

def ja_foi_enviado_hoje(telefone, historico):
    data_hoje_str = datetime.date.today().strftime('%Y-%m-%d')
    chave = gerar_chave_envio(telefone, data_hoje_str)
    return chave in historico

def registrar_envio(telefone, nome, historico):
    data_hoje = datetime.date.today()
    chave = gerar_chave_envio(telefone, data_hoje.strftime('%Y-%m-%d'))
    historico[chave] = { 'telefone': telefone, 'nome': nome, 'data_envio': data_hoje.strftime('%Y-%m-%d') }

# =============================================================================
# FUNÇÕES DE DADOS E MENSAGEM
# =============================================================================
def carregar_dados(caminho_excel, nome_aba):
    try:
        df = pd.read_excel(caminho_excel, sheet_name=nome_aba)
        print(f"Planilha '{caminho_excel}' (aba: '{nome_aba}') carregada com {len(df)} registros.")
        df['Telefone_Formatado'] = df['Telefone'].astype(str).apply(lambda tel: f"+55{tel}" if not tel.startswith('+') else tel)
        df['primeiro_nome'] = df['Nome'].str.split().str[0].str.title()
        
        # ### ALTERADO ### - A principal mudança na lógica de negócio!
        # Filtra apenas quem AINDA NÃO bateu a meta.
        df_lembrete = df[df['META_BATIDA'].str.upper() == 'NÃO'].copy()
        
        print(f"Encontrados {len(df_lembrete)} vendedores que ainda não bateram a meta.")
        return df_lembrete
    except Exception as e:
        logging.error(f"Erro ao carregar dados: {e}")
        print(f"ERRO: {e}")
        return None

# ### ALTERADO ### - Nova função para montar a mensagem de lembrete
def montar_mensagem_lembrete(template, nome, falta_meta_dia):
    """Monta a mensagem de lembrete sobre a meta diária."""
    try:
        # Converte o valor para porcentagem e formata
        falta_meta_formatado = f"{(falta_meta_dia * 100):.2f}"
        
        return template.format(
            Nome=nome,
            Falta_Meta_Dia=falta_meta_formatado
        )
    except Exception as e:
        logging.error(f"Erro ao montar mensagem de lembrete para {nome}: {e}")
        return None


def enviar_mensagem_whatsapp(telefone, mensagem):
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
    ARQUIVO_TEMPLATE_LEMBRETE = 'message_lembrete.txt' # Novo template
    
    logging.info("--- INÍCIO DO PROCESSO DE LEMBRETE DE META ---")
    print("🔔 Iniciando processo de lembrete de meta diária...")
    
    # Carregar template
    try:
        with open(ARQUIVO_TEMPLATE_LEMBRETE, 'r', encoding='utf-8') as file:
            template = file.read()
    except FileNotFoundError:
        print(f"❌ ERRO: Arquivo de template '{ARQUIVO_TEMPLATE_LEMBRETE}' não encontrado.")
        sys.exit()

    historico = carregar_historico_envios()
    df_lembretes = carregar_dados(ARQUIVO_EXCEL, NOME_DA_ABA)
    
    if df_lembretes is None or df_lembretes.empty:
        if df_lembretes is not None and df_lembretes.empty:
            print("ℹ️ Todos os vendedores bateram a meta ou não há dados. Nada para enviar.")
            logging.info("Nenhum vendedor com META_BATIDA = 'NÃO' encontrado.")
        sys.exit()
    
    sucessos = 0
    
    for indice, vendedor in tqdm(df_lembretes.iterrows(), total=len(df_lembretes), desc="Enviando Lembretes"):
        nome = vendedor.get('primeiro_nome', 'N/A')
        telefone = vendedor.get('Telefone_Formatado', 'N/A')
        falta_meta_dia_valor = vendedor.get('Falta_Meta_Dia', 0)
        
        if ja_foi_enviado_hoje(telefone, historico):
            logging.info(f"DUPLICATA EVITADA - {nome} ({telefone}) já recebeu um lembrete hoje.")
            continue
        
        # ### ALTERADO ### - Chamando a nova função de montagem
        mensagem = montar_mensagem_lembrete(template, nome, falta_meta_dia_valor)
        
        if not mensagem:
            logging.error(f"Falha ao montar mensagem para {nome}")
            continue

        print(f"\n Lembrete para: {nome} ({telefone})")
        
        if enviar_mensagem_whatsapp(telefone, mensagem):
            registrar_envio(telefone, nome, historico)
            logging.info(f"SUCESSO - Lembrete enviado para: {nome} ({telefone})")
            sucessos += 1
        else:
            logging.error(f"FALHA - Não foi possível enviar lembrete para: {nome} ({telefone})")
        
        if indice < len(df_lembretes.index) - 1:
            print("Aguardando 30 segundos...")
            time.sleep(30)
            
    if salvar_historico_envios(historico):
        print("\n💾 Histórico de lembretes atualizado com sucesso!")
    else:
        print("\n❌ Erro ao salvar histórico de lembretes!")
        
    logging.info("--- FIM DO PROCESSO DE LEMBRETES ---")