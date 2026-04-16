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

# Estilo CSS mejorado
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .info-box { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #00d2ff; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. Manejo de API Keys
with st.sidebar.expander("🔑 Configuración de APIs", expanded=False):
    groq_api_key = st.text_input("Groq API Key", value=st.secrets.get("GROQ_API_KEY", ""), type="password")
    fred_api_key = st.text_input("FRED API Key", value=st.secrets.get("FRED_API_KEY", ""), type="password")

# 3. Funciones de Datos
def get_stock_data(ticker, period="1y"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty: return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except: return pd.DataFrame()

# 4. Lógica de IA (Genérica para Stock y Macro)
def get_ai_insight(prompt, api_key):
    if not api_key: return "⚠️ API Key de Groq faltante."
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Eres un estratega financiero de Wall Street. Sé conciso y técnico."},
                      {"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

# 5. Sidebar
st.sidebar.title("TERMINAL ANALIZER")
ticker_input = st.sidebar.text_input("BUSCAR TICKER", "NVDA").upper()
period_input = st.sidebar.selectbox("HORIZONTE", ["6mo", "1y", "2y", "5y"], index=1)

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.data = get_stock_data(ticker_input, period_input)
    st.session_state.ticker = ticker_input

if 'data' not in st.session_state:
    st.session_state.data = get_stock_data("NVDA", "1y")
    st.session_state.ticker = "NVDA"

# 6. UI Principal
st.markdown(f"## 🏛️ Terminal de Análisis: {st.session_state.ticker}")

if not st.session_state.data.empty:
    df = st.session_state.data
    m1, m2, m3, m4 = st.columns(4)
    last_p = df['Close'].iloc[-1]
    pct = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
    m1.metric("Precio", f"${last_p:,.2f}", f"{pct:+.2f}%")
    m2.metric("Máximo", f"${df['High'].max():,.2f}")
    m3.metric("Mínimo", f"${df['Low'].min():,.2f}")
    m4.metric("Volumen", f"{df['Volume'].iloc[-1]:,.0f}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 TÉCNICO", "🧠 INTELIGENCIA ARTIFICIAL", "🌐 MACRO"])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#3a7bd5'), row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("💡 Tesis de Inversión")
        if st.button("GENERAR ANÁLISIS TÉCNICO IA"):
            prompt = f"Analiza la tendencia de {st.session_state.ticker} con estos precios: {df['Close'].tail(10).tolist()}. Da soporte, resistencia y veredicto."
            reporte = get_ai_insight(prompt, groq_api_key)
            st.markdown(f'<div class="info-box">{reporte}</div>', unsafe_allow_html=True)
    
    with c2:
        st.subheader("📊 Riesgo de Portafolio")
        df_risk = pd.DataFrame({'Activo': ['Acciones', 'Efectivo', 'Renta Fija'], 'Porcentaje': [70, 10, 20]})
        fig_donut = px.pie(df_risk, values='Porcentaje', names='Activo', hole=.6, 
                           color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_donut.update_layout(template="plotly_dark", showlegend=True, # Leyenda activada
                                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        fig_donut.update_traces(textinfo='percent+label') # Muestra nombre y % en el gráfico
        st.plotly_chart(fig_donut, use_container_width=True)

with tab3:
    if fred_api_key:
        fred = Fred(api_key=fred_api_key)
        col_m1, col_m2 = st.columns([1, 1])
        
        with col_m1:
            st.subheader("📈 Crecimiento PIB (USA)")
            gdp = fred.get_series('GDP').tail(12)
            st.area_chart(gdp, color="#00d2ff")
            
        with col_m2:
            st.subheader("🧠 Análisis Macro IA")
            if st.button("EXPLICAR CONTEXTO MACRO"):
                prompt = f"El PIB actual es {gdp.iloc[-1]}. ¿Cómo afecta esto a empresas tecnológicas como {st.session_state.ticker}? Explica la correlación brevemente."
                macro_info = get_ai_insight(prompt, groq_api_key)
                st.markdown(f'<div class="info-box">{macro_info}</div>', unsafe_allow_html=True)
        
        st.subheader("📉 Inflación vs Tipos de Interés")
        inf = fred.get_series('CPIAUCSL').tail(12)
        st.line_chart(inf, color="#ff4b4b")
    else:
        st.warning("Introduce la FRED API Key para desbloquear esta sección.")

st.sidebar.markdown("---")
st.sidebar.caption("ANALIZER V2.0 | Pro Edition")
