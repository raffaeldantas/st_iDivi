import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

# Lista completa de tickers no formato para Yahoo Finanças
tickers_com_extensao = [
    'ABCB4.SA', 'BRSR6.SA', 'BBSE3.SA', 'BBDC3.SA', 'BBDC4.SA', 'BRAP4.SA', 'BBAS3.SA', 'AGRO3.SA',
    'CXSE3.SA', 'CMIG3.SA', 'CMIG4.SA', 'CSMG3.SA', 'CPLE3.SA', 'CPLE6.SA', 'CPFE3.SA',
    'CMIN3.SA', 'CURY3.SA', 'DIRR3.SA', 'EGIE3.SA', 'FESA4.SA', 'FLRY3.SA', 'GGBR4.SA', 'GOAU4.SA',
    'RANI3.SA', 'ITSA4.SA', 'JBSS3.SA', 'JHSF3.SA', 'KEPL3.SA', 'KLBN11.SA', 'LAVV3.SA', 'POMO4.SA',
    'LEVE3.SA', 'BEEF3.SA', 'MTRE3.SA', 'PETR3.SA', 'PETR4.SA', 'PLPL3.SA', 'POSI3.SA', 'SAPR4.SA',
    'SANB11.SA', 'STBP3.SA', 'CSNA3.SA', 'TAEE11.SA', 'TASA4.SA', 'TGMA3.SA', 'VIVT3.SA', 'TIMS3.SA',
    'TRPL4.SA', 'UNIP6.SA', 'USIM5.SA', 'VALE3.SA', 'WIZC3.SA'
]

# Função para obter o Dividend Yield de uma empresa usando o yfinance
def get_dividend_yield(ticker):
    stock = yf.Ticker(ticker)
    dividend_yield = stock.info.get('dividendYield')
    return round(dividend_yield * 100, 2) if dividend_yield is not None else 0.0

# Função para obter o Valor Atual da ação
def get_valor_atual(ticker):
    stock = yf.Ticker(ticker)
    try:
        preco_atual = stock.history(period="1d")['Close'].iloc[-1]
        return round(preco_atual, 2)
    except IndexError:
        return None

# Função para obter o Lucro por Ação (LPA) e Valor Patrimonial por Ação (VPA)
def get_lpa_vpa(ticker):
    stock = yf.Ticker(ticker)
    lpa = stock.info.get('trailingEps')
    vpa = stock.info.get('bookValue')
    return lpa, vpa

# Obter os Dividend Yields, Valores Atuais, LPA e VPA para cada ação
dividend_yields = [get_dividend_yield(ticker) for ticker in tickers_com_extensao]
valores_atuais = [get_valor_atual(ticker) for ticker in tickers_com_extensao]
lpa_vpa = [get_lpa_vpa(ticker) for ticker in tickers_com_extensao]
lpas = [lpa for lpa, vpa in lpa_vpa]
vpas = [vpa for lpa, vpa in lpa_vpa]

# Calcular o Valor Intrínseco usando a Fórmula de Graham
valores_intrinsecos = []
for lpa, vpa in zip(lpas, vpas):
    if lpa is not None and vpa is not None:
        valor_intrinseco = round(np.sqrt(22.5 * lpa * vpa), 2)
        valores_intrinsecos.append(valor_intrinseco)
    else:
        valores_intrinsecos.append(None)

# Calcular a diferença entre o Valor Intrínseco e o Valor Atual
diferencas = []
for valor_intrinseco, valor_atual in zip(valores_intrinsecos, valores_atuais):
    if valor_intrinseco is not None and valor_atual is not None:
        diferenca = round(valor_intrinseco - valor_atual, 2)
        diferencas.append(diferenca)
    else:
        diferencas.append(None)

# Criar um DataFrame com os tickers, Dividend Yields, Valores Atuais, Valor Intrínseco e Diferença
df_dividend_yield = pd.DataFrame({
    'Ticker': [ticker.replace('.SA', '') for ticker in tickers_com_extensao],
    'DY (%)': dividend_yields,
    'Valor Atual (BRL)': valores_atuais,
    'Valor Intrínseco (BRL)': valores_intrinsecos,
    'Diferença (BRL)': diferencas
})

# Criar o indicador composto (Div-Value Pro - DVP) e adicionar ao DataFrame, arredondando para duas casas decimais
df_dividend_yield['Div-Value Pro (DVP)'] = df_dividend_yield['DY (%)'] + df_dividend_yield['Diferença (BRL)'].fillna(0)
df_dividend_yield['Div-Value Pro (DVP)'] = df_dividend_yield['Div-Value Pro (DVP)'].round(2)

# Ordenar o DataFrame pelo indicador composto
df_dividend_yield = df_dividend_yield.sort_values(by='Div-Value Pro (DVP)', ascending=False)

# Layout do aplicativo com Streamlit
st.set_page_config(page_title="Tabela de Indicadores Financeiros - Div-Value Pro (DVP)", layout="wide")

st.title("Tabela de Indicadores Financeiros - Div-Value Pro (DVP)")
st.dataframe(df_dividend_yield)

st.markdown("<div style='text-align: center; color: #777777; margin-top: 30px;'>Fonte: Yahoo Finance</div>", unsafe_allow_html=True)
