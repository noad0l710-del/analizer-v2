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

# Estilo CSS Avanzado
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
    .title-main { 
        font-size: 38px; font-weight: bold; color: #ffffff; 
        text-align: center; margin-bottom: 25px; 
        border-bottom: 3px solid #4a69bd; padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Funciones de Soporte
def get_ai_insight(prompt, api_key, system_role="Eres un estratega financiero Senior. Si hablas de beneficios usa <span class='gain'>texto</span>, si hablas de riesgos usa <span class='loss'>texto</span>."):
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
    try:
        s = yf.Ticker(ticker)
        info = s.info
        hist = s.history(period=period)
        if isinstance(hist.columns, pd.MultiIndex): hist.columns = hist.columns.get_level_values(0)
        sector = info.get('sector', 'General Market')
        return info, hist, sector
    except:
        return {}, pd.DataFrame(), "Unknown"

# 3. SIDEBAR (Controles)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2534/2534407.png", width=80)
st.sidebar.title("CONTROLES")
ticker_input = st.sidebar.text_input("BUSCAR TICKER", "NVDA").upper()
period_input = st.sidebar.selectbox("PERIODO DE ANÁLISIS", ["6mo", "1y", "2y", "5y", "max"], index=1)

# Priorizar carga de llaves
groq_key = st.sidebar.text_input("Groq Key", value=st.secrets.get("GROQ_API_KEY", ""), type="password")
fred_key = st.sidebar.text_input("FRED Key", value=st.secrets.get("FRED_API_KEY", ""), type="password")

if st.sidebar.button("🚀 ACTUALIZAR TERMINAL"):
    st.session_state.ticker = ticker_input
    with st.spinner('Actualizando datos...'):
        info, df, sector = fetch_data(ticker_input, period_input)
        st.session_state.info, st.session_state.df, st.session_state.sector = info, df, sector

# Inicialización por defecto
if 'ticker' not in st.session_state:
    st.session_state.ticker = "NVDA"
    info, df, sector = fetch_data("NVDA", "1y")
    st.session_state.info, st.session_state.df, st.session_state.sector = info, df, sector

# 4. TITULO PRINCIPAL
st.markdown('<div class="title-main">🏛️ TERMINAL ANALIZER V2.0 PRO</div>', unsafe_allow_html=True)
st.markdown(f"<h3 style='text-align: center; color: #808080;'>Ticker Activo: {st.session_state.ticker}</h3>", unsafe_allow_html=True)

# Métricas de Cabecera
inf = st.session_state.info
df = st.session_state.df
if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    last_p = df['Close'].iloc[-1]
    prev_p = df['Close'].iloc[-2]
    pct = ((last_p - prev_p) / prev_p) * 100
    
    m1.metric("Precio Actual", f"${last_p:,.2f}", f"{pct:+.2f}%")
    m2.metric("Cap. de Mercado", f"{inf.get('marketCap', 0)/1e12:.2f}T")
    m3.metric("Calidad (ROE)", f"{inf.get('returnOnEquity', 0)*100:.1f}%")
    m4.metric("Div. Yield", f"{inf.get('dividendYield', 0)*100:.2f}%")

st.divider()

# 5. TABS PRINCIPALES
tabs = st.tabs(["📊 TÉCNICO", "🧠 TESIS IA", "🎯 OPORTUNIDADES", "🏁 COMPETIDORES", "🌐 MACRO", "🛒 PAQUETES", "💬 CHAT"])

with tabs[0]: # TÉCNICO
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volumen', marker_color='#4a69bd'), row=2, col=1)
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=550, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]: # TESIS IA
    st.subheader("💡 Tesis Estructural del Activo")
    if st.button("GENERAR TESIS PROFESIONAL"):
        prompt = f"Dame una tesis de inversión para {st.session_state.ticker}. Sector: {st.session_state.sector}. ROE: {inf.get('returnOnEquity')}. Sé directo y profesional."
        res = get_ai_insight(prompt, groq_key)
        st.markdown(f'<div class="info-box">{res}</div>', unsafe_allow_html=True)

with tabs[2]: # OPORTUNIDADES
    st.subheader("🎯 Oportunidades de Entrada y Crecimiento")
    if st.button("DETECTAR OPORTUNIDADES"):
        prompt = f"Analiza oportunidades de compra/venta para {st.session_state.ticker} a ${last_p:.2f}. Usa verde para compras y rojo para riesgos."
        res = get_ai_insight(prompt, groq_key)
        st.markdown(f'<div class="info-box">{res}</div>', unsafe_allow_html=True)

with tabs[3]: # COMPETIDORES (CORREGIDO)
    st.subheader(f"🏁 Benchmarking del Sector: {st.session_state.sector}")
    sector_map = {"Technology": ["AAPL", "MSFT", "GOOGL", "AMD"], "Financial Services": ["JPM", "BAC", "GS"]}
    comps = sector_map.get(st.session_state.sector, ["SPY", "QQQ"])
    
    comp_list = []
    for c in comps:
        t_comp = yf.Ticker(c)
        c_i = t_comp.info
        # Corrección: Uso de .history para obtener el precio más seguro
        h_comp = t_comp.history(period="1d")
        p_c = h_comp['Close'].iloc[-1] if not h_comp.empty else 0
        comp_list.append({
            "Ticker": c,
            "Precio": f"${p_c:,.2f}",
            "ROE": f"{c_i.get('returnOnEquity', 0)*100:.1f}%",
            "Margen": f"{c_i.get('profitMargins', 0)*100:.1f}%"
        })
    st.table(pd.DataFrame(comp_list))

with tabs[5]: # PAQUETES DE INVERSIÓN REALES
    st.subheader("🛒 Adquisición de Paquetes de Activos")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<div class="info-box">**PAQUETE CRECIMIENTO**<br>Enfoque en NVIDIA/Apple<br><span class="gain">+15% Proyectado</span></div>', unsafe_allow_html=True)
        st.button("ADQUIRIR PAQUETE ALFA", use_container_width=True)
    with p2:
        st.markdown('<div class="info-box">**PAQUETE DIVIDENDOS**<br>Flujo de caja trimestral<br><span class="gain">Yield: 5.2%</span></div>', unsafe_allow_html=True)
        st.button("ADQUIRIR PAQUETE FLUJO", use_container_width=True)
    with p3:
        st.markdown('<div class="info-box">**PAQUETE COBERTURA**<br>Protección contra caídas<br><span class="loss">Riesgo Bajo</span></div>', unsafe_allow_html=True)
        st.button("ADQUIRIR PAQUETE DEFENSIVO", use_container_width=True)

with tabs[6]: # CHAT
    st.subheader("💬 Consultoría Contextual IA")
    if 'chat_hist' not in st.session_state: st.session_state.chat_hist = []
    u_msg = st.text_input("Pregunta sobre tu estrategia...")
    if st.button("PREGUNTAR"):
        ans = get_ai_insight(f"Sobre {st.session_state.ticker}: {u_msg}", groq_key)
        st.session_state.chat_hist.append((u_msg, ans))
    for q, a in reversed(st.session_state.chat_hist):
        st.write(f"👤: {q}")
        st.markdown(f"🤖: {a}", unsafe_allow_html=True)

st.divider()
st.caption(f"Terminal Analizer V2.0 | Groq Llama 3 | {st.session_state.ticker} Market View")
