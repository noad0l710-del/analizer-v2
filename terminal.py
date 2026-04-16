import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from groq import Groq
from fredapi import Fred

# 1. Configuración de la página
st.set_page_config(page_title="ANALIZER V2.0 - Terminal IA", page_icon="📈", layout="wide")

# Estilo CSS Avanzado (Cajas Grises + Colores Dinámicos)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    .info-box { 
        background-color: #1e2130; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #808080; margin-bottom: 15px; color: #e0e0e0;
    }
    .gain { color: #2ecc71; font-weight: bold; }
    .loss { color: #e74c3c; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { color: #ffffff; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. Funciones de Soporte
def get_ai_insight(prompt, api_key, system_role="Eres un estratega financiero Senior. Si hablas de beneficios/ganancias usa <span class='gain'>texto</span>. Si hablas de riesgos/pérdidas usa <span class='loss'>texto</span>."):
    if not api_key: return "⚠️ Configura la API Key de Groq."
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_role}, {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e: return f"❌ Error: {str(e)}"

@st.cache_data(ttl=3600)
def fetch_data(ticker, period):
    s = yf.Ticker(ticker)
    return s.info, s.history(period=period)

# 3. SIDEBAR (Controles Originales)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2534/2534407.png", width=80)
st.sidebar.title("CONTROLES")
ticker_input = st.sidebar.text_input("BUSCAR TICKER", "NVDA").upper()
period_input = st.sidebar.selectbox("PERIODO DE ANÁLISIS", ["6mo", "1y", "2y", "5y", "max"], index=1)

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.ticker = ticker_input
    st.session_state.period = period_input
    info, df = fetch_data(ticker_input, period_input)
    st.session_state.info = info
    st.session_state.df = df

# Inicialización
if 'ticker' not in st.session_state:
    st.session_state.ticker = "NVDA"
    info, df = fetch_data("NVDA", "1y")
    st.session_state.info = info
    st.session_state.df = df

# 4. DASHBOARD PRINCIPAL
st.title(f"🏛️ Terminal Analizer: {st.session_state.ticker}")

# Métricas de Cabecera
inf = st.session_state.info
df = st.session_state.df
m1, m2, m3, m4 = st.columns(4)
last_p = df['Close'].iloc[-1]
pct = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
m1.metric("Precio Actual", f"${last_p:,.2f}", f"{pct:+.2f}%")
m2.metric("Market Cap", f"{inf.get('marketCap', 0)/1e12:.2f}T")
m3.metric("Puntaje Calidad (ROE)", f"{inf.get('returnOnEquity', 0)*100:.1f}%")
m4.metric("Div. Yield", f"{inf.get('dividendYield', 0)*100:.2f}%")

st.divider()

# TABS (Chat incluido ahora como Tab)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 TÉCNICO", "🧠 IA & TESIS", "🌐 MACRO", "🏁 COMPETIDORES", "💬 CHAT IA"])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#4a69bd'), row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_a, col_b = st.columns([1.5, 1])
    with col_a:
        st.subheader("💡 Tesis de Calidad e IA")
        if st.button("GENERAR ANÁLISIS"):
            prompt = f"Analiza {st.session_state.ticker}. ROE: {inf.get('returnOnEquity')}, Margen: {inf.get('profitMargins')}. Veredicto con colores."
            res = get_ai_insight(prompt, st.secrets.get("GROQ_API_KEY"))
            st.markdown(f'<div class="info-box">{res}</div>', unsafe_allow_html=True)
    with col_b:
        st.subheader("⚖️ Distribución de Riesgo")
        df_risk = pd.DataFrame({'Cat': ['Acciones', 'Efectivo', 'Renta Fija'], 'Val': [70, 10, 20]})
        fig_pie = px.pie(df_risk, values='Val', names='Cat', hole=.5, color_discrete_sequence=['#8e44ad', '#2980b9', '#27ae60'])
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("Indicadores Macroeconomía (FRED)")
    fred_key = st.secrets.get("FRED_API_KEY")
    if fred_key:
        fred = Fred(api_key=fred_key)
        pib = fred.get_series('GDP').tail(15)
        st.area_chart(pib, color="#34495e")
        if st.button("Analizar Contexto Macro"):
            res = get_ai_insight(f"Impacto del PIB {pib.iloc[-1]} en {st.session_state.ticker}", st.secrets.get("GROQ_API_KEY"))
            st.info(res)

with tab4:
    st.subheader("🏁 Análisis de Competidores")
    # Simulación de competidores pro
    comps = ["AAPL", "MSFT", "GOOGL", "AMD"]
    comp_list = []
    for c in comps:
        t = yf.Ticker(c)
        comp_list.append({"Ticker": c, "Precio": t.fast_info['last_price'], "ROE": t.info.get('returnOnEquity', 0)*100})
    st.table(pd.DataFrame(comp_list))

with tab5:
    st.subheader("💬 Chatbot Contextual")
    if 'chat_hist' not in st.session_state: st.session_state.chat_hist = []
    msg = st.text_input("Pregunta sobre esta acción...")
    if st.button("Consultar IA"):
        ans = get_ai_insight(f"Contexto {st.session_state.ticker}: {msg}", st.secrets.get("GROQ_API_KEY"))
        st.session_state.chat_hist.append((msg, ans))
    for q, a in reversed(st.session_state.chat_hist):
        st.write(f"👤: {q}")
        st.markdown(f"🤖: {a}")

st.divider()
st.markdown("## 🛡️ Paquetes de Inversión Simulados")
if st.button("📦 CALCULAR PAQUETES"):
    reporte = get_ai_insight(f"Crea 2 paquetes para {st.session_state.ticker}. Precio: {last_p}", st.secrets.get("GROQ_API_KEY"))
    st.markdown(f'<div class="info-box">{reporte}</div>', unsafe_allow_html=True)
