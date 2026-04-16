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
st.set_page_config(
    page_title="ANALIZER V2.0 - Terminal IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS - Cajas en Gris Metálico y tipografía uniforme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .info-box { 
        background-color: #1e2130; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #808080; 
        margin-bottom: 15px; 
        margin-top: 10px;
        font-family: 'Source Sans Pro', sans-serif;
        color: #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] { color: #ffffff; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. Manejo de API Keys
with st.sidebar.expander("🔑 Configuración de APIs", expanded=False):
    groq_api_key = st.text_input("Groq API Key", 
                                value=st.secrets.get("GROQ_API_KEY", ""), 
                                type="password")
    fred_api_key = st.text_input("FRED API Key", 
                                value=st.secrets.get("FRED_API_KEY", ""), 
                                type="password")

# 3. Funciones de Datos
def get_stock_data(ticker, period="1y"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty: return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception:
        return pd.DataFrame()

# 4. Lógica de IA con Groq (Uniformidad de texto aplicada)
def get_ai_insight(prompt, api_key, system_role="Eres un estratega financiero. Responde exclusivamente en texto plano con Markdown estándar. Usa negritas para títulos. Prohibido usar caligrafías cursivas especiales, fuentes monoespaciadas para párrafos o caracteres decorativos raros."):
    if not api_key:
        return "⚠️ Error: No se detectó la API Key de Groq."
    
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_role},
                      {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error en Groq: {str(e)}"

# 5. Sidebar y Controles
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2534/2534407.png", width=100)
st.sidebar.title("TERMINAL ANALIZER")
ticker_input = st.sidebar.text_input("BUSCAR TICKER", "NVDA").upper()

# CAMBIO: Horizonte Temporal -> PERIODO DE ANÁLISIS
period_input = st.sidebar.selectbox("PERIODO DE ANÁLISIS", ["6mo", "1y", "2y", "5y", "max"], index=1)

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.data = get_stock_data(ticker_input, period_input)
    st.session_state.ticker = ticker_input

if 'data' not in st.session_state:
    st.session_state.data = get_stock_data("NVDA", "1y")
    st.session_state.ticker = "NVDA"

# 6. Dashboard Principal
st.markdown(f"## 🏛️ Terminal de Análisis: {st.session_state.ticker}")

if not st.session_state.data.empty:
    df = st.session_state.data
    m1, m2, m3, m4 = st.columns(4)
    last_close = df['Close'].iloc[-1]
    pct = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    m1.metric("Precio Actual", f"${last_close:,.2f}", f"{pct:+.2f}%")
    m2.metric("Máximo (Periodo)", f"${df['High'].max():,.2f}")
    m3.metric("Mínimo (Periodo)", f"${df['Low'].min():,.2f}")
    m4.metric("Volumen Hoy", f"{df['Volume'].iloc[-1]:,.0f}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 GRÁFICOS TÉCNICOS", "🧠 INTELIGENCIA ARTIFICIAL", "🌐 MACROECONOMÍA"])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Precio',
                                 increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#4a69bd', opacity=0.7), row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_ia_text, col_pie = st.columns([1.5, 1])
    with col_ia_text:
        st.subheader("💡 Tesis de Inversión Groq-IA")
        if st.button("GENERAR TESIS DE INVERSIÓN IA"):
            with st.spinner("Procesando tesis..."):
                recent_p = df['Close'].tail(15).tolist()
                prompt_ia = f"Analiza {st.session_state.ticker} con estos precios recientes: {recent_p}. Dame una tesis de 3 puntos: Tendencia, Riesgos y Veredicto."
                reporte = get_ai_insight(prompt_ia, groq_api_key)
                st.markdown(f'<div class="info-box">**Tesis para {st.session_state.ticker}:**\n\n{reporte}</div>', unsafe_allow_html=True)
    
    with col_pie:
        st.subheader("⚖️ Distribución de Riesgo")
        # MEJORA: Colores un tono más abajo y elegantes (Muted / Matte)
        df_risk = pd.DataFrame({'Cat': ['Acciones', 'Efectivo', 'Renta Fija'], 'Val': [70, 10, 20]})
        fig_donut = px.pie(df_risk, values='Val', names='Cat', hole=.5, 
                           color_discrete_sequence=['#8e44ad', '#2980b9', '#27ae60']) # Púrpura mate, Azul acero, Verde bosque
        fig_donut.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#1e2130', width=2)))
        fig_donut.update_layout(template="plotly_dark", showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)

with tab3:
    if fred_api_key:
        st.subheader("Indicadores Macroeconomía (FRED)")
        fred = Fred(api_key=fred_api_key)
        pib = fred.get_series('GDP').tail(15)
        st.area_chart(pib, color="#34495e") # Azul grisáceo elegante
        st.caption("Evolución del PIB (USA)")
        
        if st.button("ANALIZAR MACRO IA"):
            prompt_mac = f"El PIB actual de USA es {pib.iloc[-1]}. ¿Qué impacto tiene esto en {st.session_state.ticker}?"
            res_macro = get_ai_insight(prompt_mac, groq_api_key)
            st.markdown(f'<div class="info-box">**Análisis Macro:**\n\n{res_macro}</div>', unsafe_allow_html=True)

st.divider()

st.markdown(f"## 🛡️ Paquetes de Inversión Simulados (IA)")
if st.button("📦 GENERAR RECOMENDACIONES DE PAQUETES"):
    with st.spinner("Calculando paquetes..."):
        prompt_pkg = f"Diseña dos paquetes para {st.session_state.ticker} al precio de ${last_close:,.2f}. Detalla Costo, Ganancia estimada, Confiabilidad y Contenido. Usa un lenguaje directo, profesional y uniforme."
        pkgs_report = get_ai_insight(prompt_pkg, groq_api_key)
        st.markdown(f'<div class="info-box">{pkgs_report}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption("ANALIZER V2.0 | Groq & YFinance Edition")
