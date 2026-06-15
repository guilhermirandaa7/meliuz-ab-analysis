# -*- coding: utf-8 -*-
import pandas as pd
import sys

def carregar_dados(caminho):
    df = pd.read_csv(caminho, encoding='utf-8')
    colunas = ['comissao', 'cashback', 'vendas totais']
    df = df.rename(columns={'comissão': 'comissao', 'Grupos de usuários': 'Grupos'})
    for col in ['comissao', 'cashback', 'vendas totais']:
        df[col] = df[col].str.replace('R$ ', '').str.replace('.', '').astype(float)
    df['Data'] = pd.to_datetime(df['Data'])
    return df

def calcular_metricas(df):
    grupos = df.groupby('Grupos').agg(
        compradores_total=('compradores', 'sum'),
        comissao_total=('comissao', 'sum'),
        cashback_total=('cashback', 'sum'),
        vendas_total=('vendas totais', 'sum'),
        dias=('Data', 'nunique')
    ).reset_index()
    grupos['margem_liquida'] = grupos['comissao_total'] - grupos['cashback_total']
    grupos['margem_pct'] = grupos['margem_liquida'] / grupos['comissao_total'] * 100
    grupos['cashback_rate'] = grupos['cashback_total'] / grupos['vendas_total'] * 100
    return grupos

def decidir_vencedor(metricas):
    vencedor = metricas.sort_values('margem_liquida', ascending=False).iloc[0]
    print('\n========== DECISAO ==========')
    print(f"Escalar: {vencedor['Grupos']}")
    print(f"Margem liquida: R$ {vencedor['margem_liquida']:,.0f}")
    print(f"Margem %: {vencedor['margem_pct']:.1f}%")
    print(f"Cashback rate: {vencedor['cashback_rate']:.1f}%")
    print('==============================\n')
    return vencedor

caminho = sys.argv[1]
df = carregar_dados(caminho)
metricas = calcular_metricas(df)
print(metricas.to_string())
vencedor = decidir_vencedor(metricas)