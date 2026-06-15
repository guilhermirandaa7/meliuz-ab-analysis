import pandas as pd
import sys
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SHEET_NAME = 'Meliuz AB Tracking'

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

def gerar_alertas(metricas):
    alertas = []
    for _, row in metricas.iterrows():
        if row['margem_liquida'] <= 0:
            alertas.append('ALERTA: ' + str(row['Grupos']) + ' tem margem zero ou negativa — cashback distribuido >= comissao recebida. Grupo inviavel financeiramente.')
    return alertas

def gerar_relatorio(df, metricas, vencedor, caminho_csv):
    parceiro = df['Parceiro'].iloc[0]
    data_inicio = df['Data'].min().strftime('%d/%m/%Y')
    data_fim = df['Data'].max().strftime('%d/%m/%Y')
    gerado_em = datetime.now().strftime('%d/%m/%Y %H:%M')
    alertas = gerar_alertas(metricas)
    linhas = []
    linhas.append('# Relatorio de Teste A/B - ' + parceiro)
    linhas.append('')
    linhas.append('**Periodo:** ' + data_inicio + ' a ' + data_fim)
    linhas.append('**Gerado em:** ' + gerado_em)
    linhas.append('')
    if alertas:
        linhas.append('## Alertas')
        linhas.append('')
        for alerta in alertas:
            linhas.append('> ' + alerta)
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

def registrar_tracking(df, metricas, vencedor, caminho_csv):
    parceiro = df['Parceiro'].iloc[0]
    data_inicio = df['Data'].min().strftime('%d/%m/%Y')
    data_fim = df['Data'].max().strftime('%d/%m/%Y')
    grupos = ' | '.join(metricas['Grupos'].tolist())
    nova_linha = {
        'nome_teste': 'AB_' + parceiro.replace(' ', '_'),
        'descricao': 'Teste A/B de cashback para ' + parceiro,
        'parceiro': parceiro,
        'periodo': data_inicio + ' a ' + data_fim,
        'grupos_testados': grupos,
        'grupo_vencedor': vencedor['Grupos'],
        'margem_vencedor': round(vencedor['margem_liquida'], 2),
        'margem_pct_vencedor': str(round(vencedor['margem_pct'], 1)) + '%',
        'cashback_rate_vencedor': str(round(vencedor['cashback_rate'], 1)) + '%',
        'decisao': 'Escalar ' + str(vencedor['Grupos']),
        'analisado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'arquivo_origem': caminho_csv
    }
    tracking_path = 'tracking.csv'
    if os.path.exists(tracking_path):
        tracker = pd.read_csv(tracking_path)
        tracker = tracker[tracker['arquivo_origem'] != caminho_csv]
        tracker = pd.concat([tracker, pd.DataFrame([nova_linha])], ignore_index=True)
    else:
        tracker = pd.DataFrame([nova_linha])
    tracker.to_csv(tracking_path, index=False)
    print('Tracking atualizado em: ' + tracking_path)
    return nova_linha

def registrar_sheets(nova_linha):
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        if sheet.row_count == 1 and sheet.col_count == 1:
            cabecalho = list(nova_linha.keys())
            sheet.append_row(cabecalho)
        valores = [str(v) for v in nova_linha.values()]
        sheet.append_row(valores)
        print('Registro salvo no Google Sheets!')
    except Exception as e:
        print('Erro ao salvar no Google Sheets: ' + str(e))

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
nova_linha = registrar_tracking(df, metricas, vencedor, caminho)
registrar_sheets(nova_linha)
