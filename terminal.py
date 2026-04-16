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

# Estilo CSS Avanzado (Cajas Grises + Colores Dinámicos de IA)
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

# 2. Lógica de IA Mejorada (Colores y Chat)
def ask_groq(prompt, api_key, system_role):
    if not api_key: return "⚠️ Configura la API Key."
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_role}, {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e: return f"❌ Error: {str(e)}"

# 3. Sidebar: Datos y CHATBOT CONTEXTUAL
st.sidebar.title("🤖 CHATBOT CONTEXTUAL")
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

ticker_input = st.sidebar.text_input("TICKER ACTUAL", "NVDA").upper()
period_input = st.sidebar.selectbox("PERIODO DE ANÁLISIS", ["6mo", "1y", "2y", "5y"], index=1)

# El Chatbot sabe qué acción estás viendo
user_question = st.sidebar.text_input("Pregúntame sobre esta acción...")
if user_question and st.sidebar.button("Enviar"):
    resp = ask_groq(f"Sobre {ticker_input}: {user_question}", st.secrets.get("GROQ_API_KEY"), "Eres un asesor financiero veloz.")
    st.session_state.chat_history.append((user_question, resp))

for q, r in st.session_state.chat_history[-3:]:
    st.sidebar.write(f"🗨️ **Tú:** {q}")
    st.sidebar.write(f"🤖 **IA:** {r}")

# 4. Obtención de Datos Profesionales
@st.cache_data(ttl=3600)
def fetch_pro_data(ticker):
    s = yf.Ticker(ticker)
    info = s.info
    hist = s.history(period="1y")
    # Simulación de competidores basada en sector
    sector = info.get('sector', 'Technology')
    return info, hist, sector

info, df, sector = fetch_pro_data(ticker_input)

# 5. DASHBOARD PRINCIPAL
st.title(f"🏛️ Terminal Analizer: {ticker_input}")

# Fila 1: Quality Score y Métricas (Inspirado en tus imágenes)
q1, q2, q3, q4 = st.columns(4)
roe = info.get('returnOnEquity', 0)
quality_score = round((roe * 10) + (info.get('profitMargins', 0) * 10), 1)
quality_score = min(max(quality_score, 1), 10) # Escala 1-10

q1.metric("PUNTAJE CALIDAD", f"{quality_score}/10", "Score IA")
q2.metric("Market Cap", f"{info.get('marketCap', 0)/1e12:.2f}T")
q3.metric("PER Ratio", f"{info.get('trailingPE', 'N/A')}")
q4.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📊 TÉCNICO", "🧠 IA & OPORTUNIDADES", "🏁 COMPETIDORES", "🌐 MACRO"])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#4a69bd'), row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("💡 Oportunidades de Inversión e IA")
    if st.button("ANALIZAR OPORTUNIDADES"):
        sys_role = """Eres un analista pro. Si hablas de ganancias usa <span class='gain'>texto</span>. 
        Si hablas de riesgos o pérdidas usa <span class='loss'>texto</span>. Responde en Markdown."""
        prompt = f"Analiza {ticker_input} con ROE de {roe} y Margen de {info.get('profitMargins')}. ¿Es una oportunidad?"
        reporte = ask_groq(prompt, st.secrets.get("GROQ_API_KEY"), sys_role)
        st.markdown(f'<div class="info-box">{reporte}</div>', unsafe_allow_html=True)

with tab3:
    st.subheader(f"🏁 Comparativa Sector: {sector}")
    # Simulación de competidores (en una app real usarías una lista por sector)
    comps = ["AAPL", "MSFT", "GOOGL", "AMD"] if ticker_input != "AAPL" else ["MSFT", "GOOGL", "AMD", "INTC"]
    comp_data = []
    for c in comps:
        t = yf.Ticker(c)
        comp_data.append({"Ticker": c, "PER": t.info.get('trailingPE'), "Profit Margin": t.info.get('profitMargins')})
    st.table(pd.DataFrame(comp_data))

with tab4:
    st.write("Datos Macro FRED y PIB")
    # (Aquí iría tu lógica de FRED ya implementada)

st.divider()
st.caption("Terminal Analizer V2.0 - Datos en tiempo real de Yahoo Finance")
