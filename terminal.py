import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from groq import Groq
from fredapi import Fred
import os

# 1. Configuración de la página (Diseño Oscuro Profesional)
st.set_page_config(
    page_title="ANALIZER V2.0 - Terminal IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para mejorar el diseño
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e2130; 
        border-radius: 5px 5px 0px 0px; 
        padding: 10px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Manejo de API Keys (Prioridad: Secrets de Streamlit > Entrada Manual)
with st.sidebar.expander("🔑 Configuración de APIs", expanded=False):
    # Si existen en secrets, se usan automáticamente, si no, se pide el input
    groq_api_key = st.text_input("Groq API Key", 
                                value=st.secrets.get("GROQ_API_KEY", ""), 
                                type="password")
    fred_api_key = st.text_input("FRED API Key", 
                                value=st.secrets.get("FRED_API_KEY", ""), 
                                type="password")

# 3. Funciones de Datos
def get_stock_data(ticker, period="1y"):
    try:
        data = yf.download(ticker, period=period)
        if data.empty: return pd.DataFrame()
        # Limpiar nombres de columnas (yfinance a veces devuelve multi-index)
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
        return data
    except:
        return pd.DataFrame()

def create_candlestick_chart(data, ticker):
    if data.empty: return None
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # Velas
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                 low=data['Low'], close=data['Close'], name='Precio'), row=1, col=1)
    
    # Volumen
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volumen', marker_color='#26a69a'), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600,
                      margin=dict(l=10, r=10, t=30, b=10))
    return fig

# 4. Lógica de IA con Groq
def get_ai_analysis(ticker, stock_data, api_key):
    if not api_key:
        return "⚠️ Error: No se detectó la API Key de Groq."
    
    try:
        client = Groq(api_key=api_key)
        recent_data = stock_data.tail(15).to_string() # Enviamos los últimos 15 días
        
        prompt = f"""Actúa como un analista Senior de Hedge Fund. 
        Analiza el ticker {ticker} con estos datos recientes de mercado:
        {recent_data}
        
        Proporciona:
        1. TENDENCIA: Resumen técnico.
        2. RIESGOS: Factores críticos a vigilar.
        3. VERDICTO: ¿Compra, Venta o Mantener? Sé directo.
        """
        
        completion = client.chat.completions.create(
            model="llama3-70b-8192", # Usamos el modelo más potente
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error en Groq: {str(e)}"

# 5. Sidebar y Controles
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2534/2534407.png", width=100)
st.sidebar.title("TERMINAL ANALIZER")
ticker_input = st.sidebar.text_input("BUSCAR TICKER (Ej: NVDA, TSLA, BTC-USD)", "NVDA").upper()
period_input = st.sidebar.selectbox("HORIZONTE TEMPORAL", ["6mo", "1y", "2y", "5y", "max"], index=1)

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.data = get_stock_data(ticker_input, period_input)
    st.session_state.ticker = ticker_input

# Inicializar datos
if 'data' not in st.session_state:
    st.session_state.data = get_stock_data("NVDA", "1y")
    st.session_state.ticker = "NVDA"

# 6. Dashboard Principal
st.markdown(f"## 🏛️ Terminal de Análisis: {st.session_state.ticker}")

# Métricas rápidas
if not st.session_state.data.empty:
    last_close = st.session_state.data['Close'].iloc[-1]
    prev_close = st.session_state.data['Close'].iloc[-2]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precio Actual", f"${last_close:,.2f}", f"{pct_change:+.2f}%")
    m2.metric("Máximo (Periodo)", f"${st.session_state.data['High'].max():,.2f}")
    m3.metric("Mínimo (Periodo)", f"${st.session_state.data['Low'].min():,.2f}")
    m4.metric("Volumen Hoy", f"{st.session_state.data['Volume'].iloc[-1]:,.0f}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📈 GRÁFICOS TÉCNICOS", "🧠 INTELIGENCIA ARTIFICIAL", "🌐 MACROECONOMÍA"])

with tab1:
    fig_stock = create_candlestick_chart(st.session_state.data, st.session_state.ticker)
    if fig_stock:
        st.plotly_chart(fig_stock, use_container_width=True)

with tab2:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("💡 Tesis de Inversión Groq-IA")
        if st.button("GENERAR ANÁLISIS IA"):
            with st.spinner("Analizando mercado..."):
                reporte = get_ai_analysis(st.session_state.ticker, st.session_state.data, groq_api_key)
                st.markdown(f'<div style="background-color:#1e2130; padding:20px; border-radius:10px;">{reporte}</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 Distribución de Riesgo")
        # Gráfico de Donut Estilizado
        df_risk = pd.DataFrame({'Cat': ['Equity', 'Cash', 'Fixed Income'], 'Val': [70, 10, 20]})
        fig_donut = px.pie(df_risk, values='Val', names='Cat', hole=.6, color_discrete_sequence=['#00d2ff', '#3a7bd5', '#12c2e9'])
        fig_donut.update_layout(template="plotly_dark", showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)

with tab3:
    st.subheader("Indicadores de la Reserva Federal (FRED)")
    if fred_api_key:
        try:
            fred = Fred(api_key=fred_api_key)
            # Traer PIB e Inflación
            pib_data = fred.get_series('GDP').tail(20)
            st.line_chart(pib_data)
            st.caption("Crecimiento del PIB (Datos FRED)")
        except:
            st.error("Error al conectar con FRED. Verifica tu API Key.")
    else:
        st.warning("Introduce tu FRED API Key para ver datos macro.")

st.sidebar.markdown("---")
st.sidebar.caption("ANALIZER V2.0 | Groq & YFinance Edition")

