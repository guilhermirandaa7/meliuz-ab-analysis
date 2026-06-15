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

# Recebe o arquivo como argumento
caminho = sys.argv[1]
df = carregar_dados(caminho)

print(df.head())
print()
print(df.dtypes)