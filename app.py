import streamlit as st
import pandas as pd
import numpy as np
from iqoptionapi.stable_api import IQ_Option
import time

# Configuração Mobile-First
st.set_page_config(page_title="Monitor Quant Real", layout="centered")

# Injeção de CSS para o visual Dark Mode no Android
st.markdown("""
    <style>
    .stApp { background-color: #0b0e11; }
    .stCard { border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #1f2226; }
    .call-bg { background-color: #162a1c; border-left: 6px solid #00c853; }
    .put-bg { background-color: #2d1919; border-left: 6px solid #ff3d00; }
    .neutral-bg { background-color: #181a1e; border-left: 6px solid #546e7a; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Monitor Quant Real")
st.caption("Conectado via WebSocket - Dados reais do mercado aberto e OTC.")

# -------------------------------------------------------------------------
# AUTENTICAÇÃO E GERENCIAMENTO DE SESSÃO VIA WEBSOCKET
# -------------------------------------------------------------------------
# Para produção: use st.secrets para ocultar e-mail e senha com segurança
USER_EMAIL = st.sidebar.text_input("E-mail da Corretora:", type="default")
USER_PASSWORD = st.sidebar.text_input("Senha da Corretora:", type="password")

@st.cache_resource(ttl=3600)  # Mantém a conexão ativa por 1 hora sem deslogar
def inicializar_corretora(email, senha):
    if not email or not senha:
        return None
    try:
        # Inicia o cliente da API
        API = IQ_Option(email, senha)
        check, reason = API.connect()
        if check:
            API.change_balance("PRACTICE") # Força o uso estrito da conta de treinamento
            return API
        else:
            st.error(f"Erro na conexão: {reason}")
            return None
    except Exception as e:
        st.error(f"Falha técnica de comunicação: {str(e)}")
        return None

# Chamar o inicializador
api_conectada = inicializar_corretora(USER_EMAIL, USER_PASSWORD)

# -------------------------------------------------------------------------
# CAPTURA DE CANDLES EM TEMPO REAL (MERCADO ABERTO E OTC)
# -------------------------------------------------------------------------
def puxar_candles_reais(API, ativo, timeframe_minutos=1, quantidade_candles=70):
    """
    Substitui a simulação por dados transmitidos via WebSocket da corretora.
    Mapeia os pares tradicionais e converte dinamicamente para o padrão OTC.
    """
    if API is None:
        # Fallback de segurança: gera dados caso não esteja logado
        fechamentos = [1.0850]
        for _ in range(quantidade_candles):
            fechamentos.append(fechamentos[-1] + np.random.normal(0, 0.0003))
        return pd.DataFrame({"close": fechamentos})

    # Tratamento para ativos OTC na API (geralmente sem barras ou com sufixos específicos)
    nome_ativo_api = ativo.replace("/", "").replace("-", "") 
    
    # Converte minutos para segundos exigidos pela API (Ex: 1 min = 60s)
    size = timeframe_minutos * 60 
    
    # Solicita a carga histórica de candles
    API.start_candles_stream(nome_ativo_api, size, quantidade_candles)
    time.sleep(0.5) # Aguarda o buffer do WebSocket receber os dados
    candles = API.get_candles(nome_ativo_api, size, quantidade_candles)
    API.stop_candles_stream(nome_ativo_api, size)
    
    # Converte o retorno em DataFrame estruturado para os cálculos quantitativos
    df = pd.DataFrame(candles)
    if not df.empty and 'close' in df.columns:
        return df[['close']]
    else:
        return pd.DataFrame({"close": [1.0850] * quantidade_candles})

# -------------------------------------------------------------------------
# MOTOR DE ANÁLISE QUANTITATIVA MATEMÁTICA
# -------------------------------------------------------------------------
def calcular_analise_quantitativa(df):
    if len(df) < 30:
        return "SEM ENTRADA", "Nenhuma", "Dados insuficientes no WebSocket.", "N/A"
        
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['std_20'] = df['close'].rolling(window=20).std()
    df['bollinger_superior'] = df['sma_20'] + (df['std_20'] * 2)
    df['bollinger_inferior'] = df['sma_20'] - (df['std_20'] * 2)
    
    delta = df['close'].diff()
    ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = ganho / (perda + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    ultimo = df.iloc[-1]
    
    if ultimo['rsi'] <= 32 and ultimo['close'] <= ultimo['bollinger_inferior']:
        return "CALL", "Alta", "Preço estacionado na banda inferior de volatilidade com RSI sobrevendido.", "Rompimento contínuo da banda sem retração técnica."
    elif ultimo['rsi'] >= 68 and ultimo['close'] >= ultimo['bollinger_superior']:
        return "PUT", "Alta", "Preço estacionado na banda superior de volatilidade com RSI sobrecomprado.", "Rompimento contínuo da banda sem retração técnica."
    else:
        return "SEM ENTRADA", "Nenhuma", "Oscilação em zona cinzenta de volatilidade, sem confluência estatística.", "N/A"

# -------------------------------------------------------------------------
# RENDERIZAÇÃO DA GRADE DE ATIVOS
# -------------------------------------------------------------------------
if api_conectada:
    st.success("🟢 Conexão WebSocket estabelecida com sucesso (Modo Demonstração)!")
else:
    st.info("ℹ️ Preencha as credenciais na barra lateral para ativar as cotações reais. Exibindo dados simulados de teste.")

filtro_mercado = st.radio("Selecione os pares:", ["Todos", "Aberto", "OTC"], horizontal=True)

ativos_aberto = ["EUR/USD", "GBP/USD", "USD/JPY"]
ativos_otc = ["EUR/USD-OTC", "GBP/USD-OTC", "USD/JPY-OTC"]

lista_ativos = ativos_aberto + ativos_otc if filtro_mercado == "Todos" else (ativos_aberto if filtro_mercado == "Aberto" else ativos_otc)

for ativo in lista_ativos:
    dados_historicos = puxar_candles_reais(api_conectada, ativo)
    direcao, confianca, justificativa, invalidacao = calcular_analise_quantitativa(dados_historicos)
    
    if direcao == "CALL":
        estilo_classe, cor_sinal = "call-bg", "#00c853"
    elif direcao == "PUT":
        estilo_classe, cor_sinal = "put-bg", "#ff3d00"
    else:
        estilo_classe, cor_sinal = "neutral-bg", "#90a4ae"
        
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

if st.button("🔄 Atualizar Cotações via WebSocket", use_container_width=True):
    st.clear_cache()  # Limpa o cache antigo para buscar novos blocos de segundos atuais
    st.rerun()
