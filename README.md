# Meliuz A/B Test Analyzer

Solucao automatizada para analise de testes A/B de cashback do Meliuz Growth.

## Planilha de acompanhamento

Acesse o tracking completo dos testes aqui:
[Meliuz AB Tracking - Google Sheets](https://docs.google.com/spreadsheets/d/10DcAUgClidt7Vc1qU5P04CYhsP1eUgEmFJgPg0Noi8k/edit?usp=sharing)

## Como usar

Execute o script indicando o arquivo CSV do teste:

python analyze.py data/dataset_01_parceiroA.csv
python analyze.py data/dataset_02_parceiroB.csv
python analyze.py data/dataset_03_parceiroC.csv

## O que o script faz

1. Le e limpa os dados do CSV
2. Calcula metricas por grupo (margem, cashback rate, ticket medio)
3. Decide qual grupo escalar baseado na maior margem liquida
4. Gera relatorio em reports/
5. Registra o resultado em tracking.csv e no Google Sheets

## Estrutura do projeto

meliuz-ab-analysis/
├── analyze.py         <- script principal
├── tracking.csv       <- historico local dos testes
├── data/              <- datasets dos testes
├── reports/           <- relatorios gerados automaticamente
├── CLAUDE.md          <- instrucoes para agente de IA
└── README.md

## Logica de decisao

O grupo vencedor e escolhido pela maior margem liquida (comissao - cashback).

## Resultados

| Parceiro | Grupo Vencedor | Margem Liquida | Margem % |
|----------|---------------|----------------|----------|
| Parceiro A | Grupo 1 | R$ 404.711 | 63.4% |
| Parceiro B | Grupo 1 | R$ 286.570 | 63.6% |
| Parceiro C | Grupo 1 | R$ 34.769 | 28.6% |

## Requisitos

python -m pip install pandas gspread oauth2client
