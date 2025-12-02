"""
=============================================================================
PROJETO: SIOEI (Sistema Inteligente de Otimização e Execução de Investimentos)
VERSÃO: 3.6 (Weighted Average Smoothing)
CODENAME: Sprout 🌱 - Edição "Smart Hybrid"
DESCRIÇÃO: Implementação de média ponderada (50% Live / 50% Histórico) para suavização.
AUTOR: Aegra Code Guild
DATA: Dezembro/2025
=============================================================================
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import os
import base64
import yfinance as yf
import pandas as pd
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="SIOEI - Sprout Híbrido", 
    layout="wide", 
    page_icon="💰"
)

# ==============================================================================
# 2. ESTILIZAÇÃO
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    
    .metric-card {
        background-color: #262730; 
        border: 1px solid #444; 
        padding: 12px;
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        height: 100%;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .metric-main { font-size: 24px; font-weight: bold; color: white; margin: 5px 0; }
    .metric-detail { font-size: 11px; margin-top: 8px; opacity: 0.8; font-family: monospace; color: #E0E0E0; border-top: 1px solid #444; padding-top: 4px; width: 100%; line-height: 1.2; white-space: normal; }
    .metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 700; }
    
    .status-badge {
        font-size: 12px; padding: 4px 8px; border-radius: 4px; font-weight: bold; display: inline-block; margin-right: 10px;
    }
    .status-live { background-color: #1B5E20; color: #A5D6A7; border: 1px solid #2E7D32; }
    .status-warning { background-color: #F57F17; color: #FFF9C4; border: 1px solid #FBC02D; }
    .status-static { background-color: #B71C1C; color: #FFCDD2; border: 1px solid #C62828; }
    
    div.stButton > button { width: 100%; }
    div.row-widget.stRadio > label { display: none; }
    .logo-container { position: absolute; top: -45px; right: 0px; z-index: 1000; }
    @media (max-width: 1024px) {
        .logo-container img { width: 90px !important; }
        .logo-container { top: -35px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. CONEXÕES DE DADOS & LÓGICA HÍBRIDA
# ==============================================================================
plt.style.use('dark_background')

# --- 3.1 CONEXÃO BANCO CENTRAL (SGS API) ---
@st.cache_data(ttl=86400, show_spinner=False)
def obter_dados_bcb():
    macro = {'selic': 10.75, 'ipca': 4.50, 'status': False}
    try:
        url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        r_selic = requests.get(url_selic, timeout=5).json()
        macro['selic'] = float(r_selic[0]['valor'])
        
        url_ipca = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1?formato=json"
        r_ipca = requests.get(url_ipca, timeout=5).json()
        macro['ipca'] = float(r_ipca[0]['valor'])
        
        macro['status'] = True
    except:
        pass 
    return macro

# --- 3.2 CONEXÃO YAHOO FINANCE ---
TICKERS_MAP = {
    'ETF Ibovespa (BOVA11)': 'BOVA11.SA', 'Ações EUA (S&P500)': 'IVVB11.SA', 
    'Tech Stocks (Nasdaq)': 'NASD11.SA', 'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum/Altcoins': 'ETH-USD', 'Ouro / Dólar': 'GOLD11.SA',
    'FIIs (Tijolo)': 'IFIX', 'Ações (Dividendos)': 'IDIV' 
}

@st.cache_data(ttl=43200, show_spinner=False)
def obter_retornos_live():
    dados_live = {}
    tickers = list(TICKERS_MAP.values())
    valid_tickers = [t for t in tickers if t not in ['IFIX', 'IDIV']]
    try:
        data = yf.download(valid_tickers, period="1y", interval="1d", progress=False)['Adj Close']
        for nome, ticker in TICKERS_MAP.items():
            if ticker in valid_tickers and ticker in data.columns:
                try:
                    p_ini = data[ticker].iloc[0]; p_fim = data[ticker].iloc[-1]
                    if pd.notna(p_ini) and p_ini > 0:
                        ret = ((p_fim / p_ini) - 1) * 100
                        # Trava de sanidade para evitar distorções absurdas (-99% ou +400%)
                        if -90 < ret < 400: dados_live[nome] = ret
                except: pass
    except: pass
    return dados_live

# --- EXECUÇÃO DAS CONEXÕES ---
with st.spinner('Calibrando motores (BCB + Mercado + Histórico)...'):
    MACRO_DATA = obter_dados_bcb()
    LIVE_RETURNS = obter_retornos_live()

# Cálculo de Derivados
SELIC_ATUAL = MACRO_DATA['selic']
IPCA_ATUAL = MACRO_DATA['ipca']
CDI_ATUAL = SELIC_ATUAL - 0.10

if SELIC_ATUAL > 8.5:
    POUPANCA_ATUAL = ((1 + 0.005 + 0.0015)**12 - 1) * 100 
else:
    POUPANCA_ATUAL = SELIC_ATUAL * 0.70

STATUS_BCB = "ONLINE" if MACRO_DATA['status'] else "OFFLINE"
STATUS_MERCADO = "ONLINE" if len(LIVE_RETURNS) > 0 else "OFFLINE"

# --- LÓGICA DE SUAVIZAÇÃO (ALGORITMO HÍBRIDO) ---
def suavizar_retorno(nome_ativo, base_historica):
    """
    Se houver dado LIVE, retorna (50% Live + 50% Base).
    Se não, retorna 100% Base.
    """
    if nome_ativo in LIVE_RETURNS:
        retorno_live = LIVE_RETURNS[nome_ativo]
        # Média Ponderada: 50% Momento Atual / 50% Longo Prazo
        return (retorno_live * 0.5) + (base_historica * 0.5)
    return base_historica

# --- 3.3 CONSTRUÇÃO DA BASE DE ATIVOS ---
ATIVOS = {
    # RENDA FIXA (Indexada ao Macro Oficial - Não precisa suavizar pois é Taxa Contratada)
    'Tesouro Selic': {
        'retorno': SELIC_ATUAL, 'risco': 1, 'taxa': 1.65, 
        'tipo': 'RF', 'mercado': '🏦 Mercado Monetário', 'cor': '#4CAF50', 'desc': f'Taxa oficial BCB ({SELIC_ATUAL}%).'
    },
    'CDB Liquidez Diária': {
        'retorno': CDI_ATUAL * 0.99, 'risco': 1, 'taxa': 1.60, 
        'tipo': 'RF', 'mercado': '🏦 Mercado Monetário', 'cor': '#03A9F4', 'desc': 'Acompanha o CDI.'
    },
    'Tesouro Prefixado': {
        'retorno': SELIC_ATUAL + 2.0, 'risco': 4, 'taxa': 1.70, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#CDDC39', 'desc': 'Prêmio sobre a Selic.'
    },
    'Tesouro IPCA+ (Curto)': {
        'retorno': IPCA_ATUAL + 6.0, 'risco': 2, 'taxa': 1.60, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FFEB3B', 'desc': f'IPCA ({IPCA_ATUAL}%) + 6%.'
    },
    'Tesouro IPCA+ (Longo)': {
        'retorno': IPCA_ATUAL + 6.4, 'risco': 5, 'taxa': 1.65, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF9800', 'desc': 'Longo prazo.'
    },
    'Tesouro Renda+': {
        'retorno': IPCA_ATUAL + 6.5, 'risco': 3, 'taxa': 0.50, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF5722', 'desc': 'Renda Futura.'
    },
    'LCI/LCA (Isento)': {
        'retorno': CDI_ATUAL * 0.94, 'risco': 2, 'taxa': 0.00, 
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#0288D1', 'desc': 'Isento de IR (~94% CDI).'
    },
    'CDB Banco Médio': {
        'retorno': CDI_ATUAL * 1.20, 'risco': 3, 'taxa': 1.90, 
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#01579B', 'desc': '120% do CDI (Bruto).'
    },
    'Debêntures Incent.': {
        'retorno': IPCA_ATUAL + 7.5, 'risco': 5, 'taxa': 0.30, 
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#E91E63', 'desc': 'IPCA + Spread (Isento).'
    },
    'CRI/CRA (High Yield)': {
        'retorno': IPCA_ATUAL + 9.5, 'risco': 8, 'taxa': 2.00, 
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#C2185B', 'desc': 'Risco de Crédito.'
    },
    'Fundo Multimercado': {
        'retorno': CDI_ATUAL * 1.15, 'risco': 5, 'taxa': 3.50, 
        'tipo': 'RF', 'mercado': '📊 Fundos', 'cor': '#9C27B0', 'desc': 'Gestão Ativa.'
    },
    
    # RENDA VARIÁVEL (Aplicando Suavização Híbrida)
    'Ações (Dividendos)': {
        'retorno': suavizar_retorno('Ações (Dividendos)', 14.50), 'risco': 6, 'taxa': 0.10, 
        'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#00BCD4', 'desc': 'Vacas Leiteiras.'
    },
    'Ações (Small Caps)': {
        'retorno': 18.00, 'risco': 9, 'taxa': 2.50, 
        'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#0097A7', 'desc': 'Crescimento.'
    },
    'ETF Ibovespa (BOVA11)': {
        'retorno': suavizar_retorno('ETF Ibovespa (BOVA11)', 14.00), 'risco': 7, 'taxa': 2.10, 
        'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#006064', 'desc': 'Índice Brasil (Híbrido).'
    },
    'FIIs (Tijolo)': {
        'retorno': 12.50, 'risco': 4, 'taxa': 0.00, 
        'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#BA68C8', 'desc': 'Tijolo.'
    },
    'FIIs (Papel)': {
        'retorno': CDI_ATUAL * 1.05, 'risco': 5, 'taxa': 0.20, 
        'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#8E24AA', 'desc': 'Papel indexado.'
    },
    'Fiagro (Agronegócio)': {
        'retorno': CDI_ATUAL * 1.10, 'risco': 6, 'taxa': 0.50, 
        'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#4A148C', 'desc': 'Agro.'
    },
    'Ações EUA (S&P500)': {
        'retorno': suavizar_retorno('Ações EUA (S&P500)', 16.00), 'risco': 6, 'taxa': 2.75, 
        'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#3F51B5', 'desc': 'S&P 500 (Híbrido).'
    },
    'Tech Stocks (Nasdaq)': {
        'retorno': suavizar_retorno('Tech Stocks (Nasdaq)', 18.00), 'risco': 8, 'taxa': 2.80, 
        'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#304FFE', 'desc': 'Nasdaq (Híbrido).'
    },
    'REITs (Imóveis EUA)': {
        'retorno': 15.00, 'risco': 6, 'taxa': 3.30, 
        'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#1A237E', 'desc': 'Imóveis USD.'
    },
    'Ouro / Dólar': {
        'retorno': suavizar_retorno('Ouro / Dólar', 8.50), 'risco': 4, 'taxa': 1.00, 
        'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#FFD700', 'desc': 'Proteção (Híbrido).'
    },
    'Bitcoin (BTC)': {
        'retorno': suavizar_retorno('Bitcoin (BTC)', 30.00), 'risco': 9, 'taxa': 4.50, 
        'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#F44336', 'desc': 'Crypto (Híbrido).'
    },
    'Ethereum/Altcoins': {
        'retorno': suavizar_retorno('Ethereum/Altcoins', 35.00), 'risco': 10, 'taxa': 5.00, 
        'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#B71C1C', 'desc': 'Crypto (Híbrido).'
    }
}

PERFIS = {
    'Conservador 🛡️': {
        'CDB Banco Médio': 35, 
        'LCI/LCA (Isento)': 25, 
        'Tesouro Selic': 20, 
        'Debêntures Incent.': 20
    },
    'Moderado ⚖️': {
        'Debêntures Incent.': 25, 
        'FIIs (Papel)': 20, 
        'Fiagro (Agronegócio)': 15, 
        'Fundo Multimercado': 10, 
        'Ações (Dividendos)': 15, 
        'Tesouro IPCA+ (Longo)': 15
    },
    'Agressivo 🚀': {
        'Ações (Small Caps)': 20, 
        'Bitcoin (BTC)': 15, 
        'Tech Stocks (Nasdaq)': 20, 
        'FIIs (Tijolo)': 15, 
        'CRI/CRA (High Yield)': 15, 
        'Tesouro IPCA+ (Longo)': 15
    }
}

DESCRICOES_PERFIS = {
    'Conservador 🛡️': 'Foco em PRESERVAÇÃO. Mix de CDBs de Bancos Médios (Retorno Alto) e LCI/LCA (Isenção) para superar o CDI consistentemente.',
    'Moderado ⚖️': 'Equilíbrio. Renda Fixa + "Pimentas" de Renda Variável.',
    'Agressivo 🚀': 'Foco em MULTIPLICAÇÃO. Ações, Crypto e Dolarização.'
}

TESES = {
    '👑 Rei dos Dividendos (Barsi)': {'desc': 'Foco em renda passiva recorrente e isenta.', 'pesos': {'Ações (Dividendos)': 40, 'FIIs (Tijolo)': 25, 'FIIs (Papel)': 15, 'Debêntures Incent.': 20}},
    '🌍 All Weather (Ray Dalio)': {'desc': 'Blindada para qualquer cenário.', 'pesos': {'Ações EUA (S&P500)': 30, 'Tesouro IPCA+ (Longo)': 40, 'Tesouro Selic': 15, 'Ouro / Dólar': 7.5, 'CDB Liquidez Diária': 7.5}},
    '🚜 Agro é Pop (Fiagro)': {'desc': 'Foco no motor do PIB brasileiro.', 'pesos': {'Fiagro (Agronegócio)': 40, 'LCI/LCA (Isento)': 30, 'CRI/CRA (High Yield)': 30}},
    '🎓 Yale Model (David Swensen)': {'desc': 'Diversificação global.', 'pesos': {'Ações EUA (S&P500)': 30, 'Ações (Dividendos)': 15, 'FIIs (Tijolo)': 20, 'Tesouro IPCA+ (Curto)': 15, 'Tesouro IPCA+ (Longo)': 20}},
    '💰 Aposentadoria Renda+': {'desc': 'Acumulação longo prazo.', 'pesos': {'Tesouro Renda+': 40, 'FIIs (Tijolo)': 20, 'Ações (Dividendos)': 20, 'Tesouro IPCA+ (Longo)': 20}},
    '🔥 Pimenta Crypto': {'desc': 'Alto risco digitais.', 'pesos': {'Bitcoin (BTC)': 40, 'Ethereum/Altcoins': 20, 'Tech Stocks (Nasdaq)': 20, 'CDB Banco Médio': 20}}
}

# ==============================================================================
# 4. MOTOR MATEMÁTICO
# ==============================================================================
def calcular(pesos_dict, v_inicial, v_mensal, anos, renda_desejada=0, anos_inicio_retirada=99, usar_retirada=False):
    inflacao_aa = IPCA_ATUAL
    cdi_aa = CDI_ATUAL
    taxa_poupanca = POUPANCA_ATUAL
    
    total = sum(pesos_dict.values())
    usar_poupanca = False
    ativos_usados = [] 
    
    retorno_bruto_ponderado = 0
    custo_ponderado = 0
    risco_pond = 0

    if total == 0:
        usar_poupanca = True
        total = 1
        retorno_bruto_ponderado = taxa_poupanca
        custo_ponderado = 0
        risco_pond = 0.5
        ativos_usados = [{'nome': 'Dinheiro Parado (Poupança)', 'peso': 100, 'cor': '#757575', 'desc': 'DINHEIRO PARADO! Perdendo valor para inflação.', 'mercado': '⚠️ Alerta', 'retorno_real': taxa_poupanca, 'tipo': 'RF'}]
    else:
        for nome, peso in pesos_dict.items():
            if peso > 0:
                info = ATIVOS[nome]
                peso_real = peso / total
                retorno_bruto_ponderado += info['retorno'] * peso_real
                custo_ponderado += info['taxa'] * peso_real
                risco_pond += info['risco'] * peso_real
                ativos_usados.append({'nome': nome, 'peso': peso_real*100, 'cor': info['cor'], 'desc': info['desc'], 'mercado': info['mercado'], 'retorno_real': info['retorno'], 'tipo': info['tipo']})
    
    retorno_liquido_aa = retorno_bruto_ponderado - custo_ponderado
    
    meses = anos * 12
    mes_inicio_retirada = anos_inicio_retirada * 12
    
    tx_cart_bruto = (1 + retorno_bruto_ponderado/100)**(1/12) - 1 
    tx_cart = (1 + retorno_liquido_aa/100)**(1/12) - 1            
    tx_cdi = (1 + cdi_aa/100)**(1/12) - 1
    tx_poup = (1 + taxa_poupanca/100)**(1/12) - 1
    tx_inf = (1 + inflacao_aa/100)**(1/12) - 1
    
    y_cart_nom, y_cart_real, y_cart_bruto = [v_inicial], [v_inicial], [v_inicial]
    y_cdi_nom, y_cdi_real = [v_inicial], [v_inicial]
    y_poup_nom, y_poup_real = [v_inicial], [v_inicial]
    
    investido = v_inicial
    
    for m in range(meses):
        fluxo = v_mensal
        if usar_retirada and m >= mes_inicio_retirada:
            fluxo = v_mensal - renda_desejada
        
        y_cart_nom.append(y_cart_nom[-1] * (1 + tx_cart) + fluxo)
        y_cart_bruto.append(y_cart_bruto[-1] * (1 + tx_cart_bruto) + fluxo) 
        
        fator_real_cart = (1 + tx_cart) / (1 + tx_inf)
        y_cart_real.append(y_cart_real[-1] * fator_real_cart + fluxo)
        
        y_cdi_nom.append(y_cdi_nom[-1] * (1 + tx_cdi) + fluxo)
        fator_real_cdi = (1 + tx_cdi) / (1 + tx_inf)
        y_cdi_real.append(y_cdi_real[-1] * fator_real_cdi + fluxo)
        
        y_poup_nom.append(y_poup_nom[-1] * (1 + tx_poup) + fluxo)
        fator_real_poup = (1 + tx_poup) / (1 + tx_inf)
        y_poup_real.append(y_poup_real[-1] * fator_real_poup + fluxo)
        
        if not (usar_retirada and m >= mes_inicio_retirada):
            investido += v_mensal
    
    taxa_real_mensal = (1 + tx_cart) / (1 + tx_inf) - 1
    if taxa_real_mensal <= 0: taxa_real_mensal = 0.0001
    
    renda_passiva_possivel = y_cart_real[-1] * taxa_real_mensal
    
    return {
        'x': np.arange(meses + 1),
        'y_cart_nom': y_cart_nom, 'y_cart_real': y_cart_real, 'y_cart_bruto': y_cart_bruto,
        'y_cdi_nom': y_cdi_nom, 'y_cdi_real': y_cdi_real,
        'y_poup_nom': y_poup_nom, 'y_poup_real': y_poup_real,
        'final_nom': y_cart_nom[-1], 'final_real': y_cart_real[-1], 
        'investido': investido, 'retorno_aa': retorno_liquido_aa, 'risco': risco_pond, 
        'ativos': ativos_usados, 'is_poup': usar_poupanca,
        'taxa_real_mensal': taxa_real_mensal, 'renda_passiva_possivel': renda_passiva_possivel
    }

# ==============================================================================
# 5. GERENCIAMENTO DE ESTADO
# ==============================================================================
for k in ATIVOS.keys():
    if f"sl_{k}" not in st.session_state: st.session_state[f"sl_{k}"] = 0

def atualizar_reativo():
    mode = st.session_state.get("modo_op")
    pesos = {}
    if mode == "Automático":
        p = st.session_state.get("sel_perfil")
        if p: pesos = PERFIS[p]
    elif mode == "Assistido":
        t = st.session_state.get("sel_tese")
        if t: pesos = TESES[t]['pesos']
    
    if mode == "Manual": return

    for k in ATIVOS.keys():
        st.session_state[f"sl_{k}"] = pesos.get(k, 0)

# ==============================================================================
# 6. INTERFACE DE USUÁRIO (UI)
# ==============================================================================
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

try:
    if os.path.exists('SIOEI LOGO.jpg'): 
        logo_image = Image.open('SIOEI LOGO.jpg')
    else:
        url = "https://raw.githubusercontent.com/Open0Bit/SIOEI/main/SIOEI%20LOGO.jpg"
        logo_image = Image.open(BytesIO(requests.get(url).content))
    logo_ok = True
except: 
    logo_ok = False

if logo_ok:
    img_base64 = image_to_base64(logo_image)
    st.markdown(
        f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{img_base64}" width="130">
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="logo-container" style="font-size: 50px;">💰</div>', unsafe_allow_html=True)

# --- CABEÇALHO ---
c_status, c_vazio = st.columns([2, 3])
with c_status:
    cor_bcb = "status-live" if MACRO_DATA['status'] else "status-static"
    cor_mercado = "status-live" if len(LIVE_RETURNS) > 0 else "status-static"
    
    st.markdown(f"""
        <div style="display:flex; align-items:center;">
            <span class="status-badge {cor_bcb}">🏛️ BCB: {MACRO_DATA['selic']}% (Selic)</span>
            <span class="status-badge {cor_bcb}">📈 IPCA: {MACRO_DATA['ipca']}%</span>
            <span class="status-badge {cor_mercado}">🌍 Mercado: {STATUS_MERCADO}</span>
        </div>
    """, unsafe_allow_html=True)

c_controles = st.container()
with c_controles:
    st.markdown('<style>div.row-widget.stRadio { max-width: 80%; }</style>', unsafe_allow_html=True)
    modo = st.radio("Modo de Operação:", ["Manual", "Automático", "Assistido"], 
                    horizontal=True, label_visibility="collapsed", key="modo_op", on_change=atualizar_reativo)

st.divider()

c1, c2, c3 = st.columns(3)
v_inicial = c1.number_input("Aporte Inicial (R$)", value=10000.0, step=100.0)
v_mensal = c2.number_input("Aporte Mensal (R$)", value=0.0, step=100.0)
anos = c3.slider("Prazo (Anos)", 1, 40, 10)

if modo == "Automático":
    perfil_sel = st.selectbox("Selecione seu Perfil (CVM Suitability):", list(PERFIS.keys()), key="sel_perfil", on_change=atualizar_reativo)
    desc_texto = DESCRICOES_PERFIS.get(perfil_sel, "Perfil personalizado.")
    st.info(f"💡 **{perfil_sel}**: {desc_texto}")
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0: atualizar_reativo()
elif modo == "Assistido":
    st.selectbox("Selecione a Estratégia:", list(TESES.keys()), key="sel_tese", on_change=atualizar_reativo)
    st.info(TESES[st.session_state.sel_tese]['desc'])
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0: atualizar_reativo()
else:
    st.caption("Modo Manual: Abra o 'Ajuste Fino' abaixo para configurar.")

with st.expander("🎛️ AJUSTE FINO DA CARTEIRA (Clique para Abrir/Fechar)", expanded=False):
    t1, t2 = st.tabs(["🛡️ RENDA FIXA", "📈 RENDA VARIÁVEL"])
    
    def gerar_sliders_educativos(tipo_alvo, coluna_alvo):
        mercados = sorted(list(set([v['mercado'] for k,v in ATIVOS.items() if v['tipo'] == tipo_alvo])))
        for merc in mercados:
            with coluna_alvo.expander(merc, expanded=False):
                ativos_mercado = [k for k, v in ATIVOS.items() if v['mercado'] == merc]
                cols = st.columns(3)
                for i, k in enumerate(ativos_mercado):
                    with cols[i%3]: 
                        valor_atual = ATIVOS[k]['retorno']
                        is_live = k in LIVE_RETURNS
                        label_emoji = "🟢" if is_live else "🏦" if ATIVOS[k]['tipo'] == 'RF' else "🔧"
                        st.slider(f"{k} ({label_emoji} {valor_atual:.2f}%)", 0, 100, key=f"sl_{k}")
                    
    with t1: gerar_sliders_educativos('RF', st)
    with t2: gerar_sliders_educativos('RV', st)

dashboard_container = st.container()
raiox_container = st.container()

st.markdown("<br><br>", unsafe_allow_html=True)
with st.container(border=True): 
    st.markdown("### 🏖️ Planejamento de Aposentadoria (SIOEI 2.0)")
    check_aposentadoria = st.checkbox("ATIVAR SIMULAÇÃO DE MESADA", value=False)
    
    renda_desejada = 0
    anos_retirada = 99
    
    if check_aposentadoria:
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            renda_desejada = st.number_input("Mesada / Renda Mensal (R$)", value=100.0, step=50.0, min_value=0.0) 
        with c_m2:
            anos_retirada = st.slider("Começar a receber em (Anos):", 0, anos, 5)

# ==============================================================================
# 8. EXECUÇÃO E DASHBOARD
# ==============================================================================

pesos_atuais = {k: st.session_state[f"sl_{k}"] for k in ATIVOS.keys()}
d = calcular(pesos_atuais, v_inicial, v_mensal, anos, renda_desejada, anos_retirada, check_aposentadoria)

with dashboard_container:
    k1, k2, k3, k4 = st.columns(4)

    COLORS = {
        "neutral": "#E0E0E0", "success": "#00CC96", "warning": "#FDD835",
        "danger":  "#FF4B4B", "primary": "#29B6F6", "blue_light": "#81D4FA"
    }

    cdi_final = d['y_cdi_nom'][-1]
    poup_final = d['y_poup_nom'][-1]
    saldo_final = d['final_nom']
    
    lucro_nominal = saldo_final - d['investido']
    lucro_cdi = cdi_final - d['investido']
    lucro_poup = poup_final - d['investido']
    lucro_real = d['final_real'] - d['investido']

    def calc_percent(numer, denom):
        denom_safe = max(denom, 0.01)
        if numer > 0 and denom <= 0: return (numer / 0.01) * 100 
        return (numer / denom_safe) * 100

    def fmt_pct(val): return f"{val:,.0f}".replace(",", ".")

    if lucro_nominal < 0:
        cor_cdi_header = COLORS["danger"]; txt_cdi_header = "📉 Prejuízo"; cor_geral_card = COLORS["danger"]
    elif lucro_nominal < lucro_cdi:
        cor_cdi_header = COLORS["warning"]; pct = calc_percent(lucro_nominal, lucro_cdi); txt_cdi_header = f"⚠️ {fmt_pct(pct)}% do CDI"; cor_geral_card = COLORS["warning"]
    else:
        cor_cdi_header = COLORS["success"]; pct = calc_percent(lucro_nominal, lucro_cdi); txt_cdi_header = f"🚀 {fmt_pct(pct)}% do CDI"; cor_geral_card = COLORS["success"]

    if lucro_nominal < 0: cor_poup_header = COLORS["danger"]; txt_poup_header = "📉 Prejuízo"
    elif lucro_nominal == lucro_poup: cor_poup_header = COLORS["warning"]; pct_p = calc_percent(lucro_nominal, lucro_poup); txt_poup_header = f"⚠️ {fmt_pct(pct_p)}% da Poupança"
    else: cor_poup_header = COLORS["success"]; pct_p = calc_percent(lucro_nominal, lucro_poup); txt_poup_header = f"📈 {fmt_pct(pct_p)}% da Poupança"

    sinal_nominal = "-" if lucro_nominal < 0 else "+"
    sinal_real = "-" if lucro_real < 0 else "+"
    
    c_risco = COLORS["success"] if d['risco'] < 4 else COLORS["warning"] if d['risco'] < 7 else COLORS["danger"]
    l_risco = "Baixo" if d['risco'] < 4 else "Médio" if d['risco'] < 7 else "Alto"

    k1.markdown(f"""
    <div class="metric-card">
        <div class="metric-label" style="color:{COLORS['neutral']}">TOTAL INVESTIDO</div>
        <div class="metric-main">R$ {d['investido']:,.2f}</div>
        <div class="metric-detail"> </div>
    </div>""", unsafe_allow_html=True)
    
    k2.markdown(f"""
    <div class="metric-card" style="border-bottom: 3px solid {cor_geral_card};">
        <div class="metric-label" style="color:{cor_geral_card}">SALDO BRUTO (NOMINAL)</div>
        <div class="metric-main" style="color:white;">R$ {d['final_nom']:,.2f}</div>
        <div class="metric-detail">Líquido Real (Ajustado): <span style="color:{cor_geral_card};">R$ {d['final_real']:,.2f}</span></div>
    </div>""", unsafe_allow_html=True)
    
    k3.markdown(f"""
    <div class="metric-card" style="border-bottom: 3px solid {cor_geral_card};">
        <div class="metric-label" style="color:{cor_geral_card}">LUCRO BRUTO (NOMINAL)</div>
        <div class="metric-main" style="color:white;">{sinal_nominal} R$ {abs(lucro_nominal):,.2f}</div>
        <div class="metric-detail">Líquido Real (Ajustado): <span style="color:{cor_geral_card}">{sinal_real} R$ {abs(lucro_real):,.2f}</span></div>
    </div>""", unsafe_allow_html=True)
    
    k4.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">RISCO ({l_risco})</div>
        <div class="metric-main" style="color:{c_risco}">{d['risco']:.1f}/10</div>
        <div class="metric-detail"> </div>
    </div>""", unsafe_allow_html=True)

    if d['is_poup']:
        st.warning("⚠️ MODO POUPANÇA (CARTEIRA VAZIA). Adicione ativos ou escolha uma estratégia.")

    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 10px; background-color: #262730; padding: 12px; border-radius: 5px; border: 1px solid #444; width: 100%;">
        <div style="font-size: 16px; font-weight: bold; color: #E0E0E0; margin-right: 10px;">📊 Raio-X: Nominal vs Real ({anos} Anos)</div>
        <div style="font-size: 13px; font-family: sans-serif; font-weight: bold; white-space: nowrap;">
            <span style="color: {cor_cdi_header}; margin-right: 15px;">{txt_cdi_header}</span>
            <span style="color: {cor_poup_header};">{txt_poup_header}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns([3, 1.2])

    with g1:
        fig, ax = plt.subplots(figsize=(10, 4))
        COR_CART = cor_geral_card; COR_CDI = '#FFD700'; COR_POUP = '#FF5722'
        COR_BRUTO = '#29B6F6'

        if not d['is_poup']:
            ax.plot(d['x'], d['y_cart_bruto'], color=COR_BRUTO, linewidth=1, linestyle='--', label='Bruto (Sem taxas)')
            ax.plot(d['x'], d['y_cart_nom'], color=COR_CART, linewidth=2, label='Carteira (Líquida)')
            ax.plot(d['x'], d['y_cart_real'], color=COR_CART, linewidth=1, linestyle=':', alpha=0.5)
            
            ax.fill_between(d['x'], d['y_cart_nom'], d['y_cart_bruto'], color=COR_BRUTO, alpha=0.10, label='Impacto Tributário')
            ax.fill_between(d['x'], d['y_cart_nom'], d['y_cart_real'], color=COR_CART, alpha=0.15, label='Perda Inflação')
        
        ax.plot(d['x'], d['y_cdi_nom'], color=COR_CDI, linewidth=1.5, linestyle='--', alpha=0.7, label='CDI (Nominal)')
        ax.plot(d['x'], d['y_cdi_real'], color=COR_CDI, linewidth=0.5, linestyle=':', alpha=0.3)
        ax.fill_between(d['x'], d['y_cdi_nom'], d['y_cdi_real'], color=COR_CDI, alpha=0.08)
        
        style_poup = '-' if d['is_poup'] else ':'
        alpha_line = 0.9 if d['is_poup'] else 0.5
        ax.plot(d['x'], d['y_poup_nom'], color=COR_POUP, linewidth=1.5, linestyle=style_poup, alpha=alpha_line, label='Poupança (Nominal)')
        ax.plot(d['x'], d['y_poup_real'], color=COR_POUP, linewidth=0.5, linestyle=':', alpha=0.3)
        ax.fill_between(d['x'], d['y_poup_nom'], d['y_poup_real'], color=COR_POUP, alpha=0.08)
        
        ax.legend(loc='upper left', frameon=False, ncol=2, fontsize='x-small')
        ax.grid(True, alpha=0.1)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['bottom'].set_color('#444'); ax.spines['left'].set_color('#444'); ax.tick_params(colors='#aaa')
        st.pyplot(fig)

    with g2:
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        vals = [i['peso'] for i in d['ativos']]
        labs = [f"{i['nome']}\n{i['peso']:.0f}%" for i in d['ativos']]
        colors = [i['cor'] for i in d['ativos']]
        if not vals: vals=[1]; labs=[""]; colors=["#333"]
        ax2.pie(vals, labels=labs, colors=colors, startangle=90, textprops={'color':"white", 'fontsize': 7}, wedgeprops=dict(width=0.45, edgecolor='#222'))
        ax2.set_title("Alocação", color='white', fontsize=10)
        st.pyplot(fig2)

with raiox_container:
    st.markdown("### 🧠 Raio-X da Estratégia (Live Check)")
    for item in d['ativos']:
        is_live = item['nome'] in LIVE_RETURNS
        is_bcb = item['tipo'] == 'RF' and MACRO_DATA['status']
        
        # Lógica de Tag Inteligente
        if is_live: 
            # Verifica se está usando suavização (ativos com LIVE_RETURNS)
            tag = "<span style='color:#BB86FC; font-size:10px; border:1px solid #BB86FC; padding:1px 4px; border-radius:3px;'>HÍBRIDO (50/50)</span>"
        elif is_bcb: 
            tag = "<span style='color:#29B6F6; font-size:10px; border:1px solid #29B6F6; padding:1px 4px; border-radius:3px;'>BCB OFICIAL</span>"
        else: 
            tag = "<span style='color:#757575; font-size:10px; border:1px solid #757575; padding:1px 4px; border-radius:3px;'>ESTIMADO</span>"
        
        c1, c2 = st.columns([1.2, 3.8])
        c1.markdown(f"<span style='color:{item['cor']}; font-weight:bold;'>● {item['nome']}</span><br>{tag}", unsafe_allow_html=True)
        c2.caption(f"**{item['mercado']}** • Retorno Base: **{item['retorno_real']:.2f}%** a.a. • {item['desc']}")
        st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", unsafe_allow_html=True)

if check_aposentadoria:
    st.markdown("### 🏖️ Análise de Viabilidade (Resultados)")
    if d['taxa_real_mensal'] > 0 and renda_desejada > 0: patrimonio_necessario = renda_desejada / d['taxa_real_mensal']
    else: patrimonio_necessario = 0
    saldo_final_real = d['final_real']
    atingiu = saldo_final_real >= patrimonio_necessario and saldo_final_real > 0
    prog = min(1.0, max(0.0, saldo_final_real / patrimonio_necessario)) if patrimonio_necessario > 0 else 0.0
        
    if atingiu:
        st.success(f"🚀 **META ATINGIDA!** Sua carteira suporta a retirada e ainda cresce.")
        st.progress(prog, text=f"Sustentabilidade: {prog*100:.1f}%")
    else:
        if saldo_final_real < d['investido']: st.error("📉 **ALERTA CRÍTICO:** As retiradas estão consumindo seu patrimônio principal.")
        else: st.warning(f"⚠️ **Atenção:** Você tem saldo, mas não o suficiente para viver apenas de renda passiva perpétua.")
        st.progress(prog, text=f"Cobertura da Meta de Independência: {prog*100:.1f}%")
        st.caption(f"Para uma renda perpétua de R$ {renda_desejada}, você precisaria de R$ {patrimonio_necessario:,.2f} acumulados.")

# ==============================================================================
# 9. RODAPÉ (CRÉDITOS RESTAURADOS COMPLETOS)
# ==============================================================================
st.markdown("""
<div style='text-align: center; margin-top: 50px; color: #888; font-size: 14px;'>
    <hr style='border: 1px solid #333;'>
    <p style='margin-bottom: 5px; font-weight: bold; letter-spacing: 1px;'>AEGRA CODE GUILD</p>
    <p>
        🌐 Site: <a href='https://sioei.com' target='_blank' style='color: #00E676; text-decoration: none;'>sioei.com</a>
        &nbsp; | &nbsp;
        📧 Email: <a href='mailto:sioei@sioei.com.br' style='color: #00E676; text-decoration: none;'>sioei@sioei.com.br</a>
    </p>
</div>
""", unsafe_allow_html=True)