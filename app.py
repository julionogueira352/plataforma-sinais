import streamlit as st
import pandas as pd
import numpy as np
import random

# Configuração Mobile-First da Interface
st.set_page_config(
    page_title="Painel Quant - Sinais Avançados",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para o painel no Android (Tema Escuro de Trading)
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; }
    .stCard {
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #1f2226;
    }
    .call-bg { background-color: #162a1c; border-left: 6px solid #00c853; }
    .put-bg { background-color: #2d1919; border-left: 6px solid #ff3d00; }
    .neutral-bg { background-color: #181a1e; border-left: 6px solid #546e7a; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# SIMULADOR DE CONEXÃO WEBSOCKET (Substituir pelos pacotes do GitHub)
# -------------------------------------------------------------------------
def puxar_dados_websocket(ativo):
    """
    Simula uma requisição via WebSocket retornando dados históricos de candles (OHLCV).
    Para produção, utilize bibliotecas como 'iqoptionapi' ou conectores WebSocket customizados.
    """
    np.random.seed(int(sum(ord(c) for c in ativo)))  # Mantém consistência visual por ativo
    preco_base = 1.0850 if "USD" in ativo else 150.0
    fechamentos = [preco_base]
    for _ in range(100):  # Carrega 100 candles para cálculo preciso de indicadores de longo prazo
        fechamentos.append(fechamentos[-1] + np.random.normal(0, 0.0004))
    
    df = pd.DataFrame({"close": fechamentos})
    return df

# -------------------------------------------------------------------------
# MOTOR QUANTITATIVO AVANÇADO (Cálculos de Indicadores)
# -------------------------------------------------------------------------
def calcular_analise_quantitativa(df):
    """
    Executa cálculos puramente matemáticos sobre os dados atuais e históricos.
    Não tenta prever o futuro; gera probabilidade com base em confluências.
    """
    # 1. Médias Móveis (SMA e EMA)
    df['sma_20'] = df['close'].rolling(window=20).mean()
    
    # 2. Bandas de Bollinger (Desvio Padrão de 2 sobre a média de 20)
    df['std_20'] = df['close'].rolling(window=20).std()
    df['bollinger_superior'] = df['sma_20'] + (df['std_20'] * 2)
    df['bollinger_inferior'] = df['sma_20'] - (df['std_20'] * 2)
    
    # 3. RSI (Índice de Força Relativa)
    delta = df['close'].diff()
    ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = ganho / (perda + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 4. MACD (Média Móvel Convergência Divergência)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['sinal_macd'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Isolar o último candle fechado para análise estatística
    ultimo = df.iloc[-1]
    penultimo = df.iloc[-2]
    
    # 5. Sistema Estrito de Confluência para Sinais
    # Critério de CALL: Preço tocando/abaixo da banda inferior + RSI sobrevendido + MACD cruzando para cima
    condicao_call_rsi = ultimo['rsi'] <= 35
    condicao_call_bb = ultimo['close'] <= ultimo['bollinger_inferior']
    condicao_call_macd = ultimo['macd'] > ultimo['sinal_macd'] and penultimo['macd'] <= penultimo['sinal_macd']
    
    # Critério de PUT: Preço tocando/acima da banda superior + RSI sobrecomprado + MACD cruzando para baixo
    condicao_put_rsi = ultimo['rsi'] >= 65
    condicao_put_bb = ultimo['close'] >= ultimo['bollinger_superior']
    condicao_put_macd = ultimo['macd'] < ultimo['sinal_macd'] and penultimo['macd'] >= penultimo['sinal_macd']

    # Classificação de direção e nível de confiança por confluência
    if condicao_call_rsi and condicao_call_bb:
        confianca = "Alta" if condicao_call_macd else "Média"
        return "CALL", confianca, "Preço em exaustão na Banda Inferior de Bollinger aliado a RSI em região de sobrevenda.", "Rompimento agressivo da Banda Inferior sem retração imediata."
        
    elif condicao_put_rsi and condicao_put_bb:
        confianca = "Alta" if condicao_put_macd else "Média"
        return "PUT", confianca, "Preço em exaustão na Banda Superior de Bollinger aliado a RSI em região de sobrecompra.", "Rompimento agressivo da Banda Superior sem retração imediata."
        
    else:
        return "SEM ENTRADA", "Nenhuma", "Sinais técnicos conflitantes, sem confluência matemática clara entre volatilidade e momentum.", "N/A"

# -------------------------------------------------------------------------
# INTERFACE GRÁFICA DO USUÁRIO (UI MOBILE)
# -------------------------------------------------------------------------
st.title("📊 Monitor Quant Pro")
st.caption("Focado em análise estatística pura para mercado aberto e OTC. Sem previsões futuras.")

# Seletor de mercado otimizado para toque no Android
filtro_mercado = st.radio("Filtro de Mercado:", ["Todos", "Aberto", "OTC"], horizontal=True)

# Definição dos ativos solicitados
ativos_aberto = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "EUR/GBP"]
ativos_otc = ["EUR/USD-OTC", "GBP/USD-OTC", "USD/JPY-OTC", "USD/CHF-OTC", "EUR/GBP-OTC"]

if filtro_mercado == "Todos":
    lista_ativos = ativos_aberto + ativos_otc
elif filtro_mercado == "Aberto":
    lista_ativos = ativos_aberto
else:
    lista_ativos = ativos_otc

st.write("---")

# Varredura paralela dos ativos na tela
for ativo in lista_ativos:
    dados_historicos = puxar_dados_websocket(ativo)
    direcao, confianca, justificativa, invalidacao = calcular_analise_quantitativa(dados_historicos)
    
    # Definição visual baseada no sinal gerado
    if direcao == "CALL":
        estilo_classe = "call-bg"
        cor_sinal = "#00c853"
    elif direcao == "PUT":
        estilo_classe = "put-bg"
        cor_sinal = "#ff3d00"
    else:
        estilo_classe = "neutral-bg"
        cor_sinal = "#90a4ae"
        
    # Renderização do cartão estruturado e compacto para smartphones
    st.markdown(f"""
        <div class="stCard {estilo_classe}">
            <table style="width:100%; border:none; border-collapse:collapse;">
                <tr style="background:none;">
                    <td style="font-size: 18px; font-weight: bold; color: #ffffff; padding:0;">{ativo}</td>
                    <td style="text-align: right; font-size: 22px; font-weight: bold; color: {cor_sinal}; padding:0;">{direcao}</td>
                </tr>
                <tr style="background:none;">
                    <td style="font-size: 13px; color: #b0bec5; padding: 4px 0 0 0;">Confiança: <b>{confianca}</b></td>
                    <td style="text-align: right; font-size: 12px; color: #ffb74d; padding: 4px 0 0 0;">Risco: Alto</td>
                </tr>
            </table>
            <div style="margin-top: 12px; font-size: 13px; color: #e0e0e0; line-height: 1.4;">
                <b>Justificativa Técnica:</b> {justificativa}<br>
                <span style="color: #ff8a80;">⚠️ <b>Invalidação:</b> {invalidacao}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Botão fixo inferior de atualização rápida
if st.button("🔄 Atualizar Análise Quântica", use_container_width=True):
    st.rerun()
