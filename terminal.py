import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from groq import Groq
from fredapi import Fred

# 1. Configuración de la página (Tu estilo original)
st.set_page_config(
    page_title="ANALIZER V2.0 - Terminal IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS - ACTUALIZADO: Cajas de IA con borde GRIS METÁLICO
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4250; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    /* NUEVO: Cajas de IA en Gris (#808080) */
    .info-box { background-color: #1e2130; padding: 20px; border-radius: 10px; border-left: 5px solid #808080; margin-bottom: 15px; margin-top: 10px; }
    .stTabs [data-baseweb="tab"] { color: #ffffff; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. Manejo de API Keys (Prioridad: Secrets de Streamlit > Entrada Manual)
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

# 4. Lógica de IA con Groq (Optimizada para los nuevos Paquetes)
def get_ai_insight(prompt, api_key, system_role="Eres un estratega financiero Senior de Hedge Fund."):
    if not api_key:
        return "⚠️ Error: No se detectó la API Key de Groq. Configúrala en el sidebar."
    
    try:
        client = Groq(api_key=api_key)
        # Usamos el modelo más potente y rápido de Groq para finanzas
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
ticker_input = st.sidebar.text_input("BUSCAR TICKER (Ej: NVDA, TSLA, BTC-USD)", "NVDA").upper()
period_input = st.sidebar.selectbox("HORIZONTE TEMPORAL", ["6mo", "1y", "2y", "5y", "max"], index=1)

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.data = get_stock_data(ticker_input, period_input)
    st.session_state.ticker = ticker_input

# Inicializar datos por defecto
if 'data' not in st.session_state:
    st.session_state.data = get_stock_data("NVDA", "1y")
    st.session_state.ticker = "NVDA"

# 6. Dashboard Principal
st.markdown(f"## 🏛️ Terminal de Análisis: {st.session_state.ticker}")

# Métricas rápidas
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

# TABS PRINCIPALES (Tus nombres originales con iconos)
tab1, tab2, tab3 = st.tabs(["📊 GRÁFICOS TÉCNICOS", "🧠 INTELIGENCIA ARTIFICIAL", "🌐 MACROECONOMÍA"])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    # Velas con colores institucionales claros (Verde/Rojo vibrante)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Precio',
                                 increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)
    # Volumen
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#3a7bd5', opacity=0.7), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600,
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_ia_text, col_pie = st.columns([1.5, 1])
    with col_ia_text:
        st.subheader("💡 Tesis de Inversión Groq-IA")
        if st.button("GENERAR TESIS DE INVERSIÓN IA"):
            with st.spinner("Procesando tesis..."):
                recent_p = df['Close'].tail(15).tolist()
                prompt_ia = f"Analiza {st.session_state.ticker} con estos precios recientes: {recent_p}. Dame una tesis rápida de 3 puntos: Tendencia, Riesgos y Veredicto."
                reporte = get_ai_insight(prompt_ia, groq_api_key)
                st.markdown(f'<div class="info-box">**Tesis para {st.session_state.ticker}:**\n\n{reporte}</div>', unsafe_allow_html=True)
    
    with col_pie:
        st.subheader("⚖️ Distribución de Riesgo Recomendada")
        # MEJORA: Paleta de colores más clara y vibrante
        df_risk = pd.DataFrame({'Cat': ['Acciones', 'Efectivo', 'Renta Fija'], 'Val': [70, 10, 20]})
        fig_donut = px.pie(df_risk, values='Val', names='Cat', hole=.5, 
                           color_discrete_sequence=['#e91e63', '#2196f3', '#4caf50']) # Rubí, Zafiro, Esmeralda
        # Mantenemos las etiquetas claras (Porcentaje + Nombre)
        fig_donut.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=1)))
        fig_donut.update_layout(template="plotly_dark", showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)

with tab3:
    if fred_api_key:
        st.subheader("Indicadores Macroeconomía (FRED)")
        fred = Fred(api_key=fred_api_key)
        
        # Traer y graficar PIB (GDP)
        pib = fred.get_series('GDP').tail(15)
        st.line_chart(pib, color="#00d2ff")
        st.caption("Crecimiento del PIB (USA)")
        
        if st.button("ANALIZAR MACRO IA"):
            prompt_mac = f"El PIB actual de USA es {pib.iloc[-1]}. ¿Qué impacto tiene esto en el sector tecnológico y en empresas como {st.session_state.ticker}? Sé técnico."
            res_macro = get_ai_insight(prompt_mac, groq_api_key, "Eres un macroeconomista estratega.")
            st.markdown(f'<div class="info-box">**Análisis Macro:**\n\n{res_macro}</div>', unsafe_allow_html=True)
    else:
        st.info("Configura FRED API Key para ver datos macro.")

st.divider()

# ==============================================================================
# NUEVA SECCIÓN: PAQUETES DE INVERSIÓN RECOMENDADOS (LA IA CALCULA COSTOS/GANANCIAS)
# ==============================================================================
st.markdown(f"## 🛡️ Paquetes de Inversión Simulados (IA)")
st.caption("La IA simula estos paquetes basándose en la acción seleccionada y los datos actuales. Esto NO es una oferta real de compra.")

if st.button("📦 GENERAR RECOMENDACIONES DE PAQUETES"):
    with st.spinner("La IA está calculando los paquetes..."):
        # Le damos los datos necesarios para que la IA simule los cálculos
        stock_summary = {
            "Ticker": st.session_state.ticker,
            "Precio Actual": last_close,
            "Máximo Anual": df['High'].max(),
            "Riesgo/RSI": pct # RSI simplificado
        }
        
        prompt_pkg = f"""Diseña dos paquetes de inversión que contengan al ticker {stock_summary['Ticker']}.
        El precio actual es ${stock_summary['Precio Actual']:.2f}.
        Simula y calcula para cada paquete:
        1. COSTO TOTAL estimado.
        2. GANANCIA POTENCIAL (%) estimada a 1 año.
        3. CONFIABILIDAD (Riesgo): ¿Es confiable? (Alto, Medio, Bajo).
        4. CONTENIDO del paquete (Ej: 100% Ticker, o 50% Ticker + 50% Bonos).
        """
        
        system_role_pkg = "Eres un gestor de portafolios de inversión Senior. Genera paquetes concretos simulando números reales."
        pkgs_report = get_ai_insight(prompt_pkg, groq_api_key, system_role_pkg)
        
        # Mostramos los paquetes en el diseño gris
        st.markdown(f'<div class="info-box">**Paquetes Generados para {stock_summary['Ticker']}:**\n\n{pkgs_report}</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption("ANALIZER V2.0 | Groq & YFinance Edition")
