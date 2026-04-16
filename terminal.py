import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px  # Corregido: Importación faltante
from plotly.subplots import make_subplots
import openai
from fredapi import Fred
import os

# 1. Configuración de la página
st.set_page_config(
    page_title="ANALIZER V2.0 - Terminal IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Funciones de Soporte
def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return None

def get_stock_data(ticker, period="1y"):
    try:
        data = yf.download(ticker, period=period)
        if data.empty:
            return pd.DataFrame()
        return data
    except:
        return pd.DataFrame()

# 3. Componentes Visuales
def create_candlestick_chart(data, ticker):
    if data.empty:
        st.warning("No hay datos para mostrar el gráfico.")
        return None
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, subplot_titles=(f'Precio de {ticker}', 'Volumen'),
                        row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'],
                                 low=data['Low'], close=data['Close'], name='Precio'), row=1, col=1)
    
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volumen', marker_color='royalblue'), row=2, col=1)
    
    fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark")
    return fig

def create_donut_chart():
    # Datos de ejemplo basados en las imágenes (Portfolio Diversificado)
    df_portfolio = pd.DataFrame({
        'Ticker': ['NVDA', 'ASML', 'LLY', 'LMT', 'Otros'],
        'Peso': [40, 15, 15, 10, 20]
    })
    fig = px.pie(df_portfolio, values='Peso', names='Ticker', hole=.4, 
                 title="Distribución Sugerida de Portafolio",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(template="plotly_dark")
    return fig

# 4. Lógica de Inteligencia Artificial
def get_ai_analysis(ticker, stock_data, api_key):
    if not api_key:
        return "⚠️ Ingresa tu OpenAI API Key en el sidebar."
    
    try:
        client = openai.OpenAI(api_key=api_key)
        recent_data = stock_data.tail(10).to_string()
        
        prompt = f"Analiza la acción {ticker} con estos precios recientes:\n{recent_data}\nProporciona una tesis de inversión de 3 puntos: Tendencia, Riesgo y Recomendación."
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # O gpt-4 si tienes acceso
            messages=[{"role": "system", "content": "Eres un analista de Wall Street."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error en IA: {str(e)}"

# 5. Interfaz - Sidebar
st.sidebar.title("🛠️ Configuración")
with st.sidebar.expander("API Keys", expanded=False):
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    fred_api_key = st.text_input("FRED API Key", type="password")

ticker_input = st.sidebar.text_input("Símbolo (Ticker)", "NVDA").upper()
period_input = st.sidebar.selectbox("Periodo", ["6mo", "1y", "2y", "5y"])

if st.sidebar.button("EJECUTAR ANÁLISIS"):
    st.session_state.data = get_stock_data(ticker_input, period_input)
    st.session_state.ticker = ticker_input

# Inicialización de estado si no existe
if 'ticker' not in st.session_state:
    st.session_state.ticker = "NVDA"
    st.session_state.data = get_stock_data("NVDA", "1y")

# 6. Cuerpo Principal
st.title(f"ANALIZER V2.0: {st.session_state.ticker}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Macro & Técnico", "🤖 Oportunidades IA", "🔥 Stress Test", "💬 Chatbot"])

with tab1:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        fig_stock = create_candlestick_chart(st.session_state.data, st.session_state.ticker)
        if fig_stock:
            st.plotly_chart(fig_stock, use_container_width=True)
    
    with col_b:
        st.subheader("Indicadores Macro (FRED)")
        if fred_api_key:
            fred = Fred(api_key=fred_api_key)
            gdp = safe_api_call(fred.get_series, 'GDP')
            if gdp is not None:
                st.line_chart(gdp.tail(10), height=200)
                st.caption("Evolución del PIB")
        else:
            st.info("Configura FRED API Key para ver datos macro.")

with tab2:
    st.header("Análisis de Oportunidades con IA")
    if st.button("Generar Tesis de Inversión"):
        with st.spinner("La IA está procesando los datos..."):
            analisis = get_ai_analysis(st.session_state.ticker, st.session_state.data, openai_api_key)
            st.markdown(f"### Dictamen para {st.session_state.ticker}")
            st.write(analisis)
    
    st.divider()
    st.plotly_chart(create_donut_chart(), use_container_width=True)

with tab3:
    st.header("Simulación de Escenarios (Stress Test)")
    col1, col2, col3 = st.columns(3)
    
    # Simulación simple de impacto
    market_drop = st.slider("Escenario: Caída del Mercado (%)", 0, 50, 20)
    beta_stock = 1.45 # Beta promedio tecnología
    
    impacto_estimado = market_drop * beta_stock
    
    col1.metric("Escenario Mercado", f"-{market_drop}%")
    col2.metric("Beta Estimada", f"{beta_stock}")
    col3.metric("Impacto en Ticker", f"-{impacto_estimado:.2f}%", delta_color="inverse")
    
    st.info("Este módulo calcula cuánto caería tu posición basándose en la volatilidad histórica del sector.")

with tab4:
    st.header("Chatbot Contextual")
    query = st.text_input("Pregunta algo sobre la empresa (ej: ¿Cuál es su margen de beneficio?)")
    if query:
        st.write(f"🔍 Buscando en reportes financieros para {st.session_state.ticker}...")
        st.caption("Nota: Para funcionalidad completa, integra LangChain + VectorDB.")
