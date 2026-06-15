import pandas as pd
import sys
import os
from datetime import datetime

def carregar_dados(caminho):
    df = pd.read_csv(caminho)
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
    grupos['ticket_medio'] = grupos['vendas_total'] / grupos['compradores_total']
    return grupos

def decidir_vencedor(metricas):
    vencedor = metricas.sort_values('margem_liquida', ascending=False).iloc[0]
    return vencedor

def gerar_relatorio(df, metricas, vencedor, caminho_csv):
    parceiro = df['Parceiro'].iloc[0]
    data_inicio = df['Data'].min().strftime('%d/%m/%Y')
    data_fim = df['Data'].max().strftime('%d/%m/%Y')
    gerado_em = datetime.now().strftime('%d/%m/%Y %H:%M')

    linhas = []
    linhas.append('# Relatorio de Teste A/B - ' + parceiro)
    linhas.append('')
    linhas.append('**Periodo:** ' + data_inicio + ' a ' + data_fim)
    linhas.append('**Gerado em:** ' + gerado_em)
    linhas.append('')
    linhas.append('---')
    linhas.append('')
    linhas.append('## Metricas por Grupo')
    linhas.append('')
    linhas.append('| Grupo | Compradores | Comissao Total | Cashback Total | Margem Liquida | Margem % | Cashback Rate | Ticket Medio |')
    linhas.append('|-------|-------------|----------------|----------------|----------------|----------|---------------|--------------|')

    for _, row in metricas.iterrows():
        linha = '| ' + str(row['Grupos'])
        linha += ' | ' + str(int(row['compradores_total']))
        linha += ' | R$ ' + str(round(row['comissao_total'], 2))
        linha += ' | R$ ' + str(round(row['cashback_total'], 2))
        linha += ' | R$ ' + str(round(row['margem_liquida'], 2))
        linha += ' | ' + str(round(row['margem_pct'], 1)) + '%'
        linha += ' | ' + str(round(row['cashback_rate'], 1)) + '%'
        linha += ' | R$ ' + str(round(row['ticket_medio'], 2)) + ' |'
        linhas.append(linha)

    linhas.append('')
    linhas.append('---')
    linhas.append('')
    linhas.append('## Decisao')
    linhas.append('')
    linhas.append('**Escalar: ' + str(vencedor['Grupos']) + '**')
    linhas.append('')
    linhas.append('- Margem liquida: R$ ' + str(round(vencedor['margem_liquida'], 2)))
    linhas.append('- Margem %: ' + str(round(vencedor['margem_pct'], 1)) + '%')
    linhas.append('- Cashback rate: ' + str(round(vencedor['cashback_rate'], 1)) + '%')
    linhas.append('')
    linhas.append('**Justificativa:** O grupo vencedor apresenta maior margem liquida, garantindo sustentabilidade financeira para o Meliuz.')

    os.makedirs('reports', exist_ok=True)
    nome = parceiro.lower().replace(' ', '_')
    caminho_relatorio = 'reports/relatorio_' + nome + '.md'

    with open(caminho_relatorio, 'w') as f:
        f.write('\n'.join(linhas))

    print('Relatorio salvo em: ' + caminho_relatorio)

caminho = sys.argv[1]
df = carregar_dados(caminho)
metricas = calcular_metricas(df)
print(metricas.to_string())
vencedor = decidir_vencedor(metricas)
print('')
print('========== DECISAO ==========')
print('Escalar: ' + vencedor['Grupos'])
print('Margem liquida: R$' + str(round(vencedor['margem_liquida'], 0)))
print('Margem %: ' + str(round(vencedor['margem_pct'], 1)) + '%')
print('Cashback rate: ' + str(round(vencedor['cashback_rate'], 1)) + '%')
print('==============================')
gerar_relatorio(df, metricas, vencedor, caminho)
