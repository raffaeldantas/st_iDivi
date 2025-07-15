# v.002 - dy
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

# Lista de tickers
tickers_com_extensao = [
    'ABCB4.SA', 'BRSR6.SA', 'BBSE3.SA', 'BBDC3.SA', 'BBDC4.SA', 'BRAP4.SA', 'BBAS3.SA', 'AGRO3.SA',
    'CXSE3.SA', 'CMIG3.SA', 'CMIG4.SA', 'CSMG3.SA', 'CPLE3.SA', 'CPLE6.SA', 'CPFE3.SA',
    'CMIN3.SA', 'CURY3.SA', 'DIRR3.SA', 'EGIE3.SA', 'FESA4.SA', 'FLRY3.SA', 'GGBR4.SA', 'GOAU4.SA',
    'RANI3.SA', 'ITSA4.SA', 'JBSS3.SA', 'JHSF3.SA', 'KEPL3.SA', 'KLBN11.SA', 'LAVV3.SA', 'POMO4.SA',
    'LEVE3.SA', 'BEEF3.SA', 'MTRE3.SA', 'PETR3.SA', 'PETR4.SA', 'PLPL3.SA', 'POSI3.SA', 'SAPR4.SA',
    'SANB11.SA', 'STBP3.SA', 'CSNA3.SA', 'TAEE11.SA', 'TASA4.SA', 'TGMA3.SA', 'VIVT3.SA', 'TIMS3.SA',
    'TRPL4.SA', 'UNIP6.SA', 'USIM5.SA', 'VALE3.SA', 'WIZC3.SA' # Nota: ISAE4.SA foi trocado por TRPL4.SA para exemplo, pois às vezes ISAE4 não retorna dados.
]

@st.cache_data
def carregar_dados_acoes(tickers):
    """
    Busca e processa todos os dados necessários para uma lista de tickers.
    Faz apenas uma chamada principal por ticker para otimizar a performance.
    """
    dados_acoes = []
    
    progress_bar = st.progress(0, text="Iniciando busca de dados...")
    total_tickers = len(tickers)

    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # --- Obtenção dos dados ---
            valor_atual = info.get('regularMarketPrice')
            if valor_atual is None:
                 hist = stock.history(period="1d")
                 if not hist.empty:
                    valor_atual = hist['Close'].iloc[-1]

            dividend_rate = info.get('dividendRate')
            dy_percent = 0.0
            if dividend_rate is not None and valor_atual is not None and valor_atual > 0:
                dy_ratio = dividend_rate / valor_atual
                dy_percent = round(dy_ratio * 100, 2)
            
            lpa = info.get('trailingEps')
            vpa = info.get('bookValue')

            # --- NOVO: VERIFICAÇÃO DE SANIDADE PARA O LPA ---
            # Ocasionalmente, a API retorna valores absurdos para o LPA.
            # Se o módulo do LPA for maior que o dobro do preço, consideramos um erro
            # e o anulamos para não poluir o cálculo de Graham.
            if valor_atual is not None and lpa is not None and valor_atual > 0:
                if abs(lpa) > (valor_atual * 2):
                    lpa = None # Anula o LPA por ser irrealista

            # --- Cálculos ---
            valor_intrinseco = None
            diferenca = None
            margem_seguranca = None

            # A lógica a seguir já lida com lpa=None, então não precisamos mudar mais nada.
            if lpa is not None and vpa is not None and lpa > 0:
                valor_intrinseco = round(np.sqrt(22.5 * lpa * vpa), 2)
                
                if valor_atual is not None:
                    diferenca = round(valor_intrinseco - valor_atual, 2)
                    margem_seguranca = round((diferenca / valor_atual) * 100, 2) if valor_atual > 0 else 0

            # Adiciona todos os dados processados à lista
            dados_acoes.append({
                'Ticker': ticker.replace('.SA', ''),
                'DY (%)': dy_percent,
                'Valor Atual (R$)': round(valor_atual, 2) if valor_atual else None,
                'LPA': lpa,
                'VPA': vpa,
                'Valor Intrínseco (R$)': valor_intrinseco,
                'Diferença (R$)': diferenca,
                'Margem Segurança (%)': margem_seguranca
            })

        except Exception as e:
            print(f"Não foi possível obter dados para {ticker}: {e}")
            dados_acoes.append({'Ticker': ticker.replace('.SA', ''), 'DY (%)': 'Erro', 'Valor Atual (R$)': 'Erro'})
        
        progress_bar.progress((i + 1) / total_tickers, text=f"Buscando dados para {ticker}...")
    
    progress_bar.empty()
    return pd.DataFrame(dados_acoes)

# --- Layout do aplicativo com Streamlit ---
st.set_page_config(page_title="Análise de Ações - Graham & Dividendos", layout="wide")
st.title("Análise de Ações - Graham & Dividendos")

df_acoes = carregar_dados_acoes(tickers_com_extensao)

# Criar ranks para uma pontuação mais robusta (Alternativa ao DVP)
df_acoes['Rank_DY'] = df_acoes['DY (%)'].rank(ascending=False, na_option='bottom')
df_acoes['Rank_Margem'] = df_acoes['Margem Segurança (%)'].rank(ascending=False, na_option='bottom')
df_acoes['Score (Rank)'] = df_acoes['Rank_DY'] + df_acoes['Rank_Margem']

# Ordenar pelo Score (menor é melhor, pois é soma de posições no rank)
df_acoes_ordenado = df_acoes.sort_values(by='Score (Rank)', ascending=True)

# --- ADIÇÃO CRÍTICA AQUI: Resetar o índice e adcionar +1 ---
# Isso cria um novo índice sequencial de 0 a N-1, que será exibido como a primeira coluna
df_acoes_ordenado = df_acoes_ordenado.reset_index(drop=True)
df_acoes_ordenado.index = df_acoes_ordenado.index + 1

st.info("""
**Como usar a tabela:**
- **DY (%)**: Dividend Yield dos últimos 12 meses.
- **Valor Intrínseco (R$)**: Calculado pela Fórmula de Graham `√(22.5 * LPA * VPA)`. Só é válido para empresas com lucro (LPA > 0).
- **Margem Segurança (%)**: Mostra o quanto o preço atual está abaixo do valor intrínseco. Valores positivos indicam um possível desconto.
- **Score (Rank)**: Uma pontuação combinada. Quanto **menor** o Score, melhor a posição da ação no ranking combinado de Dividend Yield e Margem de Segurança.
""", icon="ℹ️")

# Exibindo o DataFrame formatado
st.dataframe(df_acoes_ordenado.style.format({
    'DY (%)': '{:.2f}%',
    'Valor Atual (R$)': 'R$ {:.2f}',
    'LPA': '{:.2f}',
    'VPA': '{:.2f}',
    'Valor Intrínseco (R$)': 'R$ {:.2f}',
    'Diferença (R$)': 'R$ {:.2f}',
    'Margem Segurança (%)': '{:.2f}%',
    'Rank_DY': '{:.0f}',       # Adicionado para formatar como inteiro
    'Rank_Margem': '{:.0f}',   # Adicionado para formatar como inteiro
    'Score (Rank)': '{:.0f}'   # Adicionado para formatar como inteiro
}, na_rep='-'))


st.markdown("<div style='text-align: center; color: #777777; margin-top: 30px;'>Fonte: Yahoo Finance | Apenas para fins de estudo, não é recomendação de investimento.</div>", unsafe_allow_html=True)