# =============================================================================
# IMPORTAÇÕES NECESSÁRIAS
# =============================================================================
import pywhatkit
import time
import datetime
import pandas as pd
import sys
import logging
import re
import json
import os
from tqdm import tqdm
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# =============================================================================
# CONFIGURAÇÕES CENTRALIZADAS
# =============================================================================
class Config:
    ARQUIVO_EXCEL = 'contatosvendedores.xlsx'
    NOME_DA_ABA = 'basededados'
    ARQUIVO_TEMPLATE = 'message.txt'
    ARQUIVO_HISTORICO = 'historico_relatorios.json'
    TEMPO_ESPERA_BASE = 15
    TEMPO_ESPERA_ENTRE_ENVIOS = 30
    TEMPO_FECHAR_ABA = 15
    MAX_TENTATIVAS = 3
    COLUNAS_OBRIGATORIAS = [
        'Nome', 'Telefone', 'Faturado_mes', 'Meta', 'Alcance', 
        'falta_meta_mes', 'Fat_Projetado', 'Pct_Projetado', 'Meta_diaria'
    ]

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def configurar_logging():
    """Configura o sistema de logging com rotação de arquivos."""
    log_file = Path('logs') / f'relatorio_envio_diario_{datetime.date.today().strftime("%Y%m%d")}.log'
    log_file.parent.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)])
    print(f"Sistema de logging configurado. Logs em: {log_file}")

def validar_arquivo_existe(caminho: str) -> bool:
    """Verifica se um arquivo existe antes de tentar abri-lo."""
    if not Path(caminho).exists():
        logging.error(f"Arquivo não encontrado: {caminho}")
        return False
    return True

def formatar_moeda_brasileira(valor: Any) -> str:
    """Formata valores monetários no padrão brasileiro de forma segura."""
    try:
        if pd.isna(valor) or valor == '': return "R$ 0,00"
        if isinstance(valor, str): valor = float(valor.replace(',', '.'))
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

def validar_dados_obrigatorios(df: pd.DataFrame) -> bool:
    """Valida se todas as colunas necessárias existem na planilha."""
    for coluna in Config.COLUNAS_OBRIGATORIAS:
        if coluna not in df.columns:
            raise ValueError(f"Coluna obrigatória '{coluna}' não encontrada na planilha")
    return True

def carregar_e_preparar_dados(caminho_excel: str, nome_aba: str) -> Optional[pd.DataFrame]:
    """Carrega, valida e prepara os dados da planilha."""
    try:
        if not validar_arquivo_existe(caminho_excel): return None
        
        df = pd.read_excel(caminho_excel, sheet_name=nome_aba)
        logging.info(f"Planilha carregada: {len(df)} registros da aba '{nome_aba}'")
        
        validar_dados_obrigatorios(df)
        
        df = df.dropna(subset=['Nome', 'Telefone']).copy()
        df['Telefone_Formatado'] = df['Telefone'].astype(str).apply(lambda tel: f"+55{tel}" if not tel.startswith('+') else tel)
        df['primeiro_nome'] = df['Nome'].str.split().str[0].str.title()
        
        logging.info(f"Dados preparados: {len(df)} registros válidos para processamento")
        return df
    except Exception as e:
        logging.error(f"Erro ao carregar e preparar dados: {e}")
        return None

def montar_mensagem(template: str, dados_loja: pd.Series) -> Optional[str]:
    """Monta a mensagem personalizada para uma loja."""
    try:
        return template.format(
            Nome=dados_loja.get('primeiro_nome', 'Cliente'),
            data_atual=datetime.date.today().strftime('%d/%m/%Y'),
            Faturado_mes=formatar_moeda_brasileira(dados_loja.get('Faturado_mes', 0)),
            Meta=formatar_moeda_brasileira(dados_loja.get('Meta', 0)),
            Alcance=f"{(dados_loja.get('Alcance', 0)*100):.2f}",
            falta_meta_mes=formatar_moeda_brasileira(dados_loja.get('falta_meta_mes', 0)),
            Fat_Projetado=formatar_moeda_brasileira(dados_loja.get('Fat_Projetado', 0)),
            Pct_Projetado=f"{(dados_loja.get('Pct_Projetado', 0)*100):.2f}",
            Meta_diaria=formatar_moeda_brasileira(dados_loja.get('Meta_diaria', 0))
        )
    except Exception as e:
        logging.error(f"Erro ao montar mensagem para {dados_loja.get('Nome', 'N/A')}: {e}")
        return None

def enviar_com_retry(telefone: str, mensagem: str) -> bool:
    """Envia mensagem com sistema de retry."""
    for tentativa in range(Config.MAX_TENTATIVAS):
        try:
            pywhatkit.sendwhatmsg_instantly(phone_no=telefone, message=mensagem, wait_time=Config.TEMPO_ESPERA_BASE,
                                          tab_close=True, close_time=Config.TEMPO_FECHAR_ABA)
            if tentativa > 0: logging.info(f"Sucesso na tentativa {tentativa + 1} para {telefone}")
            return True
        except Exception as e:
            logging.warning(f"Tentativa {tentativa + 1} falhou para {telefone}: {e}")
            if tentativa < Config.MAX_TENTATIVAS - 1: time.sleep(5)
    return False

def gerar_relatorio_final(sucessos: int, falhas: int, pulados: int, total: int) -> str:
    """Gera relatório final detalhado."""
    taxa_sucesso = (sucessos / (sucessos + falhas) * 100) if (sucessos + falhas) > 0 else 0
    relatorio = f"""
    ========== RELATÓRIO FINAL DE ENVIO ==========
    📊 Total de Lojas na Planilha: {total}
    ✅ Envios Bem-sucedidos: {sucessos}
    ❌ Falhas no Envio: {falhas}
    ⏭️  Envios Pulados (Já Realizados Hoje): {pulados}
    📈 Taxa de Sucesso (dos envios tentados): {taxa_sucesso:.1f}%
    📅 Data/Hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    ============================================
    """
    return relatorio

# Funções de histórico
def carregar_historico_envios() -> Dict:
    if os.path.exists(Config.ARQUIVO_HISTORICO):
        try:
            with open(Config.ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f: return json.load(f)
        except json.JSONDecodeError: return {}
    return {}

def salvar_historico_envios(historico: Dict):
    try:
        with open(Config.ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f: json.dump(historico, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Falha crítica ao salvar o histórico de envios: {e}")

def gerar_chave_diaria(telefone: str) -> str:
    return f"{telefone}_{datetime.date.today().strftime('%Y-%m-%d')}"

def ja_enviado_hoje(telefone: str, historico: Dict) -> bool:
    return gerar_chave_diaria(telefone) in historico

def registrar_envio_no_historico(telefone: str, nome: str, historico: Dict):
    chave = gerar_chave_diaria(telefone)
    historico[chave] = {
        'nome': nome, 'data_envio': datetime.date.today().strftime('%Y-%m-%d'),
        'hora_envio': datetime.datetime.now().strftime('%H:%M:%S'), 'status': 'SUCESSO'
    }

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================
def main():
    configurar_logging()
    logging.info("=== INÍCIO DO PROCESSO DE ENVIO DE RELATÓRIO ===")
    
    historico_de_envios = carregar_historico_envios()
    
    try:
        with open(Config.ARQUIVO_TEMPLATE, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        logging.critical(f"Arquivo de template '{Config.ARQUIVO_TEMPLATE}' não encontrado. Abortando.")
        return

    df_lojas = carregar_e_preparar_dados(Config.ARQUIVO_EXCEL, Config.NOME_DA_ABA)
    
    if df_lojas is None or df_lojas.empty:
        logging.warning("Nenhum dado válido para processar. Finalizando.")
        return
    
    sucessos, falhas, pulados = 0, 0, 0
    
    for indice, loja in tqdm(df_lojas.iterrows(), total=len(df_lojas), desc="Enviando Relatórios", unit="msg"):
        nome_loja = loja.get('primeiro_nome', 'N/A')
        telefone_loja = loja.get('Telefone_Formatado', 'N/A')
        
        if ja_enviado_hoje(telefone_loja, historico_de_envios):
            logging.info(f"PULADO: Relatório para {nome_loja} ({telefone_loja}) já foi enviado hoje.")
            pulados += 1
            continue
        
        mensagem = montar_mensagem(template, loja)
        if not mensagem:
            logging.error(f"FALHA AO MONTAR MENSAGEM para {nome_loja} (linha {indice})")
            falhas += 1
            continue
        
        print(f"\n📱 Processando: {nome_loja} ({telefone_loja})")
        
        if enviar_com_retry(telefone_loja, mensagem):
            logging.info(f"SUCESSO: Relatório para {nome_loja} ({telefone_loja}) enviado.")
            sucessos += 1
            registrar_envio_no_historico(telefone_loja, nome_loja, historico_de_envios)
        else:
            logging.error(f"FALHA TOTAL no envio para: {nome_loja} ({telefone_loja})")
            falhas += 1
        
        if indice < len(df_lojas) - 1:
            print(f"⏱️  Aguardando {Config.TEMPO_ESPERA_ENTRE_ENVIOS}s...")
            time.sleep(Config.TEMPO_ESPERA_ENTRE_ENVIOS)
            
    salvar_historico_envios(historico_de_envios)
    logging.info("Histórico de envios foi salvo.")
    
    relatorio = gerar_relatorio_final(sucessos, falhas, pulados, len(df_lojas))
    print(relatorio)
    logging.info(relatorio.replace('\n', ' '))
    logging.info("=== FIM DO PROCESSO ===")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Processo interrompido pelo usuário.")
        print("\nProcesso cancelado.")
    except Exception as e:
        logging.critical(f"Erro fatal não tratado na execução: {e}", exc_info=True)