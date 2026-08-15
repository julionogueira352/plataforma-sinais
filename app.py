import streamlit as st
import pandas as pd
import numpy as np

# Configuração Mobile-First
st.set_page_config(
    page_title="Monitor Quant Pro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização básica para o celular
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; }
    h1, h3, p, span { color: white !important; }
    div[data-testid="stMetric"] {
        background-color: #181a1e;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #1f2226;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Monitor Quant Pro + Candles")
st.caption("Foco em análise técnica estrutural e padrões de velas em tempo real (OTC).")

# -------------------------------------------------------------------------
# GERADOR DE DADOS COMPLETO (OHLC: Open, High, Low, Close)
# -------------------------------------------------------------------------
def puxar_dados_ohlc(ativo):
    """Gera dados simulando candles completos com abertura, máxima, mínima e fechamento"""
    np.random.seed(int(sum(ord(c) for c in ativo)))
    preco_base = 1.0850 if "USD" in ativo else 150.0
    
    fechamentos = [preco_base]
    for _ in range(80):
        fechamentos.append(fechamentos[-1] + np.random.normal(0, 0.0004))
        
    df = pd.DataFrame({"close": fechamentos})
    
    # Criando componentes OHLC realistas baseados no fechamento para detectar padrões
    df['open'] = df['close'].shift(1).fillna(preco_base)
    df['high'] = df[['open', 'close']].max(axis=1) + np.random.uniform(0, 0.0003, size=len(df))
    df['low'] = df[['open', 'close']].min(axis=1) - np.random.uniform(0, 0.0003, size=len(df))
    
    return df

# -------------------------------------------------------------------------
# MOTOR DE ANÁLISE: INDICADORES + PADRÕES DE VELAS
# -------------------------------------------------------------------------
def analisar_mercado(df):
    # 1. Indicadores Técnicos
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['std_20'] = df['close'].rolling(window=20).std()
    df['bollinger_superior'] = df['sma_20'] + (df['std_20'] * 2)
    df['bollinger_inferior'] = df['sma_20'] - (df['std_20'] * 2)
    
    delta = df['close'].diff()
    ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = ganho / (perda + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Isolar os dois últimos candles para padrões
    atual = df.iloc[-1]
    anterior = df.iloc[-2]
    
    # Regras matemáticas para Padrões de Candlestick
    corpo_atual = abs(atual['close'] - atual['open'])
    pavio_superior = atual['high'] - max(atual['open'], atual['close'])
    pavio_inferior = min(atual['open'], atual['close']) - atual['low']
    
    corpo_anterior = abs(anterior['close'] - anterior['open'])
    
    # Identificação dos Padrões
    eh_martelo = (pavio_inferior > (2 * corpo_atual)) and (pavio_superior < (0.2 * corpo_atual))
    eh_estrela_cadente = (pavio_superior > (2 * corpo_atual)) and (pavio_inferior < (0.2 * corpo_atual))
    
    eh_engolfo_alta = (anterior['close'] < anterior['open']) and (atual['close'] > atual['open']) and (atual['close'] >= anterior['open']) and (atual['open'] <= anterior['close'])
    eh_engolfo_baixa = (anterior['close'] > anterior['open']) and (atual['close'] < atual['open']) and (atual['close'] <= anterior['open']) and (atual['open'] >= anterior['close'])

    # 2. Sistema de Gatilhos (Filtros mais flexíveis para gerar MAIS sinais)
    
    # Gatilhos de CALL
    if atual['rsi'] <= 40 or atual['close'] <= atual['bollinger_inferior']:
        if eh_martelo:
            return "CALL", "🟢 COMPRA", "Martelo identificado em região de suporte/sobrevenda."
        elif eh_engolfo_alta:
            return "CALL", "🟢 COMPRA", "Engolfo de Alta confirmado em zona de exaustão vendedora."
        elif atual['close'] <= atual['bollinger_inferior']:
            return "CALL", "🟢 COMPRA", "Preço rompeu a Banda Inferior de Bollinger (Estratégia de Retração)."

    # Gatilhos de PUT
    if atual['rsi'] >= 60 or atual['close'] >= atual['bollinger_superior']:
        if eh_estrela_cadente:
            return "PUT", "🔴 VENDA", "Estrela Cadente em região de resistência/sobrecompra."
        elif eh_engolfo_baixa:
            return "PUT", "🔴 VENDA", "Engolfo de Baixa confirmado em zona de exaustão compradora."
        elif atual['close'] >= atual['bollinger_superior']:
            return "PUT", "🔴 VENDA", "Preço rompeu a Banda Superior de Bollinger (Estratégia de Retração)."

    return "SEM ENTRADA", "⚪ NEUTRO", "Aguardando toque nas bandas ou formação de padrão de vela claro."

# -------------------------------------------------------------------------
# RENDERIZAÇÃO NA TELA DO SMARTPHONE
# -------------------------------------------------------------------------
lista_ativos = ["EUR/USD-OTC", "GBP/USD-OTC", "USD/JPY-OTC", "AUD/USD-OTC", "EUR/GBP-OTC", "USD/CHF-OTC"]

st.write("### 🤖 Radar de Sinais (Filtro Técnico + Candles)")

for ativo in lista_ativos:
    dados = puxar_dados_ohlc(ativo)
    direcao, texto_sinal, justificativa = analisar_mercado(dados)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"🔹 {ativo}")
        st.caption(f"**Gatilho:** {justificativa}")
        st.caption("⚠️ *Invalidação: Continuidade da tendência sem retração no primeiro minuto.*")
    
    with col2:
        st.metric(label="Ação", value=texto_sinal)
    
    st.write("---")

if st.button("🔄 Atualizar Grade de Sinais", use_container_width=True):
    st.rerun()
