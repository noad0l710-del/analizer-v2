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
    .title-main { font-size: 32px; font-weight: bold; color: #ffffff; margin-bottom: 20px; border-bottom: 2px solid #3e4250; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. Funciones de Soporte
def get_ai_insight(prompt, api_key, system_role="Eres un estratega financiero Senior. Si hablas de beneficios/ganancias usa <span class='gain'>texto</span>. Si hablas de riesgos/pérdidas usa <span class='loss'>texto</span>."):
    if not api_key: return "⚠️ Configura la API Key de Groq en Secrets o Sidebar."
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
    info = s.info
    hist = s.history(period=period)
    # Identificar competidores reales por sector
    sector = info.get('sector', '')
    return info, hist, sector

# 3. SIDEBAR (Controles)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2534/2534407.png", width=80)
st.sidebar.title("TERMINAL ANALIZER")
ticker_input = st.sidebar.text_input("BUSCAR TICKER", "NVDA").upper()
period_input = st.sidebar.selectbox("PERIODO DE ANÁLISIS", ["6mo", "1y", "2y", "5y", "max"], index=1)

groq_key = st.secrets.get("GROQ_API_KEY", "")
fred_key = st.secrets.get("FRED_API_KEY", "")

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.ticker = ticker_input
    info, df, sector = fetch_data(ticker_input, period_input)
    st.session_state.info = info
    st.session_state.df = df
    st.session_state.sector = sector

# Inicialización
if 'ticker' not in st.session_state:
    st.session_state.ticker = "NVDA"
    info, df, sector = fetch_data("NVDA", "1y")
    st.session_state.info = info
    st.session_state.df = df
    st.session_state.sector = sector

# 4. TITULO Y DASHBOARD
st.markdown(f'<div class="title-main">🏛️ TERMINAL ANALIZER V2.0: {st.session_state.ticker}</div>', unsafe_allow_html=True)

inf = st.session_state.info
df = st.session_state.df
m1, m2, m3, m4 = st.columns(4)
last_p = df['Close'].iloc[-1]
pct = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
m1.metric("Precio Actual", f"${last_p:,.2f}", f"{pct:+.2f}%")
m2.metric("Cap. de Mercado", f"{inf.get('marketCap', 0)/1e12:.2f}T")
m3.metric("Calidad (ROE)", f"{inf.get('returnOnEquity', 0)*100:.1f}%")
m4.metric("Div. Yield", f"{inf.get('dividendYield', 0)*100:.2f}%")

st.divider()

# TABS PRINCIPALES
tabs = st.tabs(["📊 TÉCNICO", "🧠 TESIS IA", "🚀 OPORTUNIDADES", "🏁 COMPETIDORES", "🌐 MACRO", "🛒 PAQUETES", "💬 CHAT"])

with tabs[0]: # TÉCNICO
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#4a69bd'), row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]: # TESIS IA
    col_a, col_b = st.columns([1.5, 1])
    with col_a:
        st.subheader("💡 Tesis Estructural")
        if st.button("GENERAR TESIS PROFESIONAL"):
            prompt = f"Analiza {st.session_state.ticker}. Sector: {st.session_state.sector}. ROE: {inf.get('returnOnEquity')}. Dame una tesis de inversión institucional."
            res = get_ai_insight(prompt, groq_key)
            st.markdown(f'<div class="info-box">{res}</div>', unsafe_allow_html=True)
    with col_b:
        st.subheader("⚖️ Asset Allocation")
        df_risk = pd.DataFrame({'Cat': ['Equity', 'Cash', 'Fixed Income'], 'Val': [75, 5, 20]})
        fig_pie = px.pie(df_risk, values='Val', names='Cat', hole=.5, color_discrete_sequence=['#8e44ad', '#2980b9', '#27ae60'])
        st.plotly_chart(fig_pie, use_container_width=True)

with tabs[2]: # OPORTUNIDADES
    st.subheader("🎯 Oportunidades de Entrada/Salida")
    if st.button("DETECTAR OPORTUNIDADES"):
        prompt = f"Basado en el ticker {st.session_state.ticker} y su precio actual ${last_p:.2f}, identifica puntos de entrada técnicos y oportunidades de crecimiento a largo plazo. Usa colores verde/rojo."
        res = get_ai_insight(prompt, groq_key)
        st.markdown(f'<div class="info-box">{res}</div>', unsafe_allow_html=True)

with tabs[3]: # COMPETIDORES
    st.subheader(f"🏁 Benchmarking: Sector {st.session_state.sector}")
    # Definición de competidores por contexto
    sector_map = {"Technology": ["AAPL", "MSFT", "GOOGL", "AMD", "INTC"], "Financial Services": ["JPM", "BAC", "GS", "MS"]}
    comps = sector_map.get(st.session_state.sector, ["SPY", "QQQ", "DIA"])
    
    comp_list = []
    for c in comps:
        t = yf.Ticker(c)
        c_inf = t.info
        comp_list.append({
            "Ticker": c,
            "Precio": f"${t.fast_info['last_price']:.2f}",
            "ROE": f"{c_inf.get('returnOnEquity', 0)*100:.1f}%",
            "PER": c_inf.get('trailingPE', 'N/A'),
            "Margen": f"{c_inf.get('profitMargins', 0)*100:.1f}%"
        })
    st.table(pd.DataFrame(comp_list))

with tabs[4]: # MACRO
    if fred_key:
        st.subheader("Indicadores Macroeconomía (FRED)")
        fred = Fred(api_key=fred_key)
        pib = fred.get_series('GDP').tail(15)
        st.area_chart(pib, color="#34495e")
        if st.button("ANALIZAR IMPACTO MACRO"):
            res = get_ai_insight(f"PIB actual {pib.iloc[-1]}. Impacto en {st.session_state.ticker}.", groq_key)
            st.info(res)

with tabs[5]: # PAQUETES
    st.subheader("🛒 Paquetes de Inversión en Venta")
    st.write("Selecciona un paquete para ejecutar en tu cuenta de corretaje:")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<div class="info-box">**PAQUETE CRECIMIENTO**<br>70% Ticker + 30% ETF<br><span class="gain">Rend. Est: 15%</span></div>', unsafe_allow_html=True)
        st.button("COMPRAR CRECIMIENTO", key="p1")
    with p2:
        st.markdown('<div class="info-box">**PAQUETE DEFENSIVO**<br>40% Ticker + 60% Bonos<br><span class="gain">Rend. Est: 6%</span></div>', unsafe_allow_html=True)
        st.button("COMPRAR DEFENSIVO", key="p2")
    with p3:
        st.markdown('<div class="info-box">**PAQUETE DIVIDENDOS**<br>Foco en Yield y Flujo de Caja<br><span class="gain">Yield: 4.5%</span></div>', unsafe_allow_html=True)
        st.button("COMPRAR DIVIDENDOS", key="p3")

with tabs[6]: # CHAT
    st.subheader("💬 Consultas Contextuales")
    if 'chat_hist' not in st.session_state: st.session_state.chat_hist = []
    msg = st.text_input("Escribe tu duda sobre la estrategia actual...")
    if st.button("PREGUNTAR"):
        ans = get_ai_insight(f"Ticker {st.session_state.ticker}. Pregunta: {msg}", groq_key)
        st.session_state.chat_hist.append((msg, ans))
    for q, a in reversed(st.session_state.chat_hist):
        st.write(f"👤: {q}")
        st.markdown(f"🤖: {a}", unsafe_allow_html=True)

st.divider()
st.caption("Terminal Analizer V2.0 | Conectado a Yahoo Finance & Groq Llama 3")
