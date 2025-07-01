import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Garanta que a biblioteca de gráficos esteja instalada: pip install matplotlib seaborn

def analisar_historico_de_metas():
    """Carrega o histórico, analisa e gera visualizações sobre metas batidas."""
    
    print("Iniciando análise do histórico de metas batidas...")
    
    # --- 1. CARREGAR OS DADOS DO HISTÓRICO ---
    try:
        with open('historico_parabens.json', 'r', encoding='utf-8') as f:
            dados_historico = json.load(f)
        
        if not dados_historico:
            print("ℹ️ Histórico de envios está vazio. Nada para analisar.")
            return

        df = pd.DataFrame.from_dict(dados_historico, orient='index')
        print(f"✅ Histórico carregado com {len(df)} registros.")

    except FileNotFoundError:
        print("❌ Arquivo 'historico_parabens.json' não encontrado. Rode o script de envio primeiro.")
        return
    except Exception as e:
        print(f"❌ Erro ao carregar os dados: {e}")
        return

    # --- 2. PREPARAÇÃO DOS DADOS PARA ANÁLISE ---
    print("\n🧹 Preparando dados para análise...")
    df['data_envio'] = pd.to_datetime(df['data_envio'])
    
    dias_semana_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
    df['nome_dia_semana'] = df['dia_da_semana'].map(dias_semana_map)
    print("✅ Dados preparados!")

    # --- 3. ANÁLISE E INSIGHTS ---
    print("\n💡 Extraindo Insights:")

    # Pergunta 1: Qual vendedor mais recebeu parabéns?
    top_performers = df['nome'].value_counts().head(5)
    print("\n🏆 Top 5 Vendedores com Mais Metas Batidas:")
    print(top_performers)

    # Pergunta 2: Em quais dias da semana as metas são mais batidas?
    metas_por_dia = df['nome_dia_semana'].value_counts().reindex(dias_semana_map.values()).fillna(0)
    print("\n📅 Metas Batidas por Dia da Semana:")
    print(metas_por_dia)
    
    # --- 4. VISUALIZAÇÃO DOS DADOS ---
    print("\n🎨 Gerando visualizações...")
    sns.set_style("whitegrid")

    plt.figure(figsize=(10, 6))
    sns.barplot(x=metas_por_dia.index, y=metas_por_dia.values, palette="viridis")
    plt.title('Total de Metas Diárias Batidas por Dia da Semana', fontsize=16, pad=20)
    plt.ylabel('Quantidade de Metas Batidas')
    plt.xlabel('Dia da Semana')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('metas_por_dia_semana.png')
    print("✅ Gráfico 'metas_por_dia_semana.png' salvo.")
    # plt.show() # Descomente para exibir na tela

if __name__ == "__main__":
    analisar_historico_de_metas()