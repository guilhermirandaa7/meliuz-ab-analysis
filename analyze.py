import pandas as pd
import sys

def carregar_dados(caminho):
    df = pd.read_csv(caminho)
    
    # Converter colunas monetárias de string para float
    colunas_monetarias = ['comissão', 'cashback', 'vendas totais']
    for col in colunas_monetarias:
        df[col] = df[col].str.replace('R$ ', '').str.replace('.', '').astype(float)
    
    # Converter data para datetime
    df['Data'] = pd.to_datetime(df['Data'])
    
    return df

def calcular_metricas(df):
    grupos = df.groupby('Grupos de usuários').agg(
        compradores_total = ('compradores', 'sum'),
        compradores_media = ('compradores', 'mean'),
        comissao_total    = ('comissão', 'sum'),
        cashback_total    = ('cashback', 'sum'),
        vendas_total      = ('vendas totais', 'sum'),
        dias              = ('Data', 'nunique')
    ).reset_index()

    grupos['margem_liquida'] = grupos['comissao_total'] - grupos['cashback_total']
    grupos['margem_pct']     = grupos['margem_liquida'] / grupos['comissao_total'] * 100
    grupos['cashback_rate']  = grupos['cashback_total'] / grupos['vendas_total'] * 100
    grupos['ticket_medio']   = grupos['vendas_total'] / grupos['compradores_total']

    return grupos

# Execução
caminho = sys.argv[1]
df = carregar_dados(caminho)
metricas = calcular_metricas(df)
print(metricas.to_string())