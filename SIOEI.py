"""
=============================================================================
PROJETO: SIOEI (Sistema Inteligente de Otimização e Execução de Investimentos)
VERSÃO: 2.7 (Educational Descriptions Restored)
CODENAME: Sprout 🌱 - Edição Final Otimizada
DESCRIÇÃO: Simulador completo com educacional de perfis e áreas de inflação.
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

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="SIOEI - Sprout Realista", 
    layout="wide", 
    page_icon="💰"
)

# ==============================================================================
# 2. ESTILIZAÇÃO (CSS & DARK MODE)
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
    
    .metric-detail { 
        font-size: 11px; 
        margin-top: 8px; 
        opacity: 0.8; 
        font-family: monospace; 
        color: #E0E0E0; 
        border-top: 1px solid #444; 
        padding-top: 4px; 
        width: 100%; 
        line-height: 1.2;
        white-space: normal;
    }
    
    .metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 700; }
    
    div.stButton > button { width: 100%; }
    div.row-widget.stRadio > label { display: none; }
    .streamlit-expanderHeader { font-size: 14px; color: #90CAF9; }

    .logo-container {
        position: absolute;
        top: -45px;
        right: 0px;
        z-index: 1000;
    }

    @media (max-width: 1024px) {
        .logo-container img { width: 90px !important; }
        .logo-container { top: -35px; }
        .metric-main { font-size: 20px; }
        .metric-card { min-height: 130px; padding: 8px; }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. BASE DE DADOS (CALIBRAGEM REALISTA & STRATEGY)
# ==============================================================================
plt.style.use('dark_background')

ATIVOS = {
    # --- RENDA FIXA ---
    'Tesouro Selic': {
        'retorno': 10.75, 
        'risco': 1, 
        'taxa': 1.65,     
        'tipo': 'RF', 'mercado': '🏦 Mercado Monetário', 'cor': '#4CAF50', 'desc': 'Soberano. Liquidez imediata.'
    },
    'CDB Liquidez Diária': {
        'retorno': 10.65, 
        'risco': 1, 
        'taxa': 1.60,     
        'tipo': 'RF', 'mercado': '🏦 Mercado Monetário', 'cor': '#03A9F4', 'desc': 'Reserva bancária.'
    },
    'Tesouro Prefixado': {
        'retorno': 12.50, 
        'risco': 4, 
        'taxa': 1.70,     
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#CDDC39', 'desc': 'Taxa travada na compra.'
    },
    'Tesouro IPCA+ (Curto)': {
        'retorno': 10.50, 
        'risco': 2, 
        'taxa': 1.60,     
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FFEB3B', 'desc': 'Proteção contra inflação.'
    },
    'Tesouro IPCA+ (Longo)': {
        'retorno': 10.80, 
        'risco': 5, 
        'taxa': 1.65, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF9800', 'desc': 'Aposentadoria (Volátil).'
    },
    'Tesouro Renda+': {
        'retorno': 11.00, 
        'risco': 3, 
        'taxa': 0.50,     
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF5722', 'desc': 'Fluxo de renda futura.'
    },
    'LCI/LCA (Isento)': {
        'retorno': 9.60,  
        'risco': 2, 
        'taxa': 0.00,     # ISENTO
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#0288D1', 'desc': 'Isento de IR. Eficiente.'
    },
    'CDB Banco Médio': {
        'retorno': 12.80, 
        'risco': 3, 
        'taxa': 1.90,     
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#01579B', 'desc': 'Retorno alto, mas tributado.'
    },
    'Debêntures Incent.': {
        'retorno': 11.50, 
        'risco': 5, 
        'taxa': 0.30,     # ISENTO (Spread apenas)
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#E91E63', 'desc': 'Crédito Privado Isento.'
    },
    'CRI/CRA (High Yield)': {
        'retorno': 14.50, 
        'risco': 8, 
        'taxa': 2.00,     
        'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#C2185B', 'desc': 'Alto Risco/Retorno.'
    },
    'Fundo Multimercado': {
        'retorno': 12.50, 
        'risco': 5, 
        'taxa': 3.50,     
        'tipo': 'RF', 'mercado': '📊 Fundos', 'cor': '#9C27B0', 'desc': 'Gestão ativa (Custos altos).'
    },

    # --- RENDA VARIÁVEL ---
    'Ações (Dividendos)': {
        'retorno': 14.50, 
        'risco': 6, 
        'taxa': 0.10,     
        'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#00BCD4', 'desc': 'Vacas Leiteiras.'
    },
    'Ações (Small Caps)': {
        'retorno': 18.00, 
        'risco': 9, 
        'taxa': 2.50,     
        'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#0097A7', 'desc': 'Crescimento Agressivo.'
    },
    'ETF Ibovespa (BOVA11)': {
        'retorno': 14.00, 
        'risco': 7, 
        'taxa': 2.10,     
        'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#006064', 'desc': 'Índice Brasil.'
    },
    'FIIs (Tijolo)': {
        'retorno': 12.50, 
        'risco': 4, 
        'taxa': 0.00,     
        'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#BA68C8', 'desc': 'Aluguel Isento.'
    },
    'FIIs (Papel)': {
        'retorno': 13.50, 
        'risco': 5, 
        'taxa': 0.20,     
        'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#8E24AA', 'desc': 'Juros compostos mensais.'
    },
    'Fiagro (Agronegócio)': {
        'retorno': 14.20, 
        'risco': 6, 
        'taxa': 0.50,     
        'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#4A148C', 'desc': 'Dividendos do Agro.'
    },
    'Ações EUA (S&P500)': {
        'retorno': 16.00, 
        'risco': 6, 
        'taxa': 2.75,     
        'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#3F51B5', 'desc': 'Economia Americana.'
    },
    'Tech Stocks (Nasdaq)': {
        'retorno': 18.00, 
        'risco': 8, 
        'taxa': 2.80,     
        'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#304FFE', 'desc': 'Tecnologia Global.'
    },
    'REITs (Imóveis EUA)': {
        'retorno': 15.00, 
        'risco': 6, 
        'taxa': 3.30,     
        'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#1A237E', 'desc': 'Imóveis em Dólar.'
    },
    'Ouro / Dólar': {
        'retorno': 8.50,  
        'risco': 4, 
        'taxa': 1.00,     
        'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#FFD700', 'desc': 'Proteção (Hedge).'
    },
    'Bitcoin (BTC)': {
        'retorno': 30.00, 
        'risco': 9, 
        'taxa': 4.50,     
        'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#F44336', 'desc': 'Reserva de valor digital.'
    },
    'Ethereum/Altcoins': {
        'retorno': 35.00, 
        'risco': 10,
        'taxa': 5.00,     
        'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#B71C1C', 'desc': 'Risco Extremo.'
    }
}

# --- PERFIS OTIMIZADOS E DESCRITIVOS ---
PERFIS = {
    'Conservador 🛡️': {
        'LCI/LCA (Isento)': 40, 
        'Tesouro Selic': 30, 
        'Debêntures Incent.': 15, 
        'Tesouro IPCA+ (Curto)': 15
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
    'Conservador 🛡️': 'Foco em PRESERVAÇÃO DE CAPITAL. Alocação majoritária em Renda Fixa Isenta (LCI/LCA) para superar o CDI líquido sem correr riscos desnecessários.',
    'Moderado ⚖️': 'Equilíbrio entre Segurança e Retorno. Introduz "pimentas" de Renda Variável (FIIs) e Crédito Privado para buscar ganho real acima da inflação.',
    'Agressivo 🚀': 'Foco em MULTIPLICAÇÃO DE PATRIMÔNIO. Aceita alta volatilidade para buscar retornos expressivos no longo prazo com Ações, Crypto e Dolarização.'
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
    inflacao_aa = 4.50
    cdi_aa = 10.75
    taxa_poupanca = 6.17
    
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
        ativos_usados = [{'nome': 'Dinheiro Parado (Poupança)', 'peso': 100, 'cor': '#757575', 'desc': 'DINHEIRO PARADO! Perdendo valor para inflação.', 'mercado': '⚠️ Alerta'}]
    else:
        for nome, peso in pesos_dict.items():
            if peso > 0:
                info = ATIVOS[nome]
                peso_real = peso / total
                retorno_bruto_ponderado += info['retorno'] * peso_real
                custo_ponderado += info['taxa'] * peso_real
                risco_pond += info['risco'] * peso_real
                ativos_usados.append({'nome': nome, 'peso': peso_real*100, 'cor': info['cor'], 'desc': info['desc'], 'mercado': info['mercado']})
    
    retorno_liquido_aa = retorno_bruto_ponderado - custo_ponderado
    meses = anos * 12
    mes_inicio_retirada = anos_inicio_retirada * 12
    
    tx_cart = (1 + retorno_liquido_aa/100)**(1/12) - 1
    tx_cdi = (1 + cdi_aa/100)**(1/12) - 1
    tx_poup = (1 + taxa_poupanca/100)**(1/12) - 1
    tx_inf = (1 + inflacao_aa/100)**(1/12) - 1
    
    y_cart_nom, y_cart_real = [v_inicial], [v_inicial]
    y_cdi_nom, y_cdi_real = [v_inicial], [v_inicial]
    y_poup_nom, y_poup_real = [v_inicial], [v_inicial]
    
    investido = v_inicial
    
    for m in range(meses):
        fluxo = v_mensal
        if usar_retirada and m >= mes_inicio_retirada:
            fluxo = v_mensal - renda_desejada
        
        # Carteira
        y_cart_nom.append(y_cart_nom[-1] * (1 + tx_cart) + fluxo)
        fator_real_cart = (1 + tx_cart) / (1 + tx_inf)
        y_cart_real.append(y_cart_real[-1] * fator_real_cart + fluxo)
        
        # CDI (Calculado Bruto para Benchmark Nominal, mas Real desconta inflação)
        y_cdi_nom.append(y_cdi_nom[-1] * (1 + tx_cdi) + fluxo)
        fator_real_cdi = (1 + tx_cdi) / (1 + tx_inf)
        y_cdi_real.append(y_cdi_real[-1] * fator_real_cdi + fluxo)
        
        # Poupança
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
        'y_cart_nom': y_cart_nom, 'y_cart_real': y_cart_real,
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
    
    # --- AQUI ESTÁ A CORREÇÃO: DESCRIÇÃO EDUCACIONAL DE VOLTA ---
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
                    with cols[i%3]: st.slider(k, 0, 100, key=f"sl_{k}")
                    
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
        "neutral": "#E0E0E0",
        "success": "#00CC96",
        "warning": "#FDD835",
        "danger":  "#FF4B4B",
        "primary": "#29B6F6",
        "blue_light": "#81D4FA"
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

    def fmt_pct(val):
        s = f"{val:,.0f}"
        return s.replace(",", ".")

    # Comparativo CDI (Baseado no Nominal Líquido vs CDI Bruto)
    if lucro_nominal < 0:
        cor_cdi_header = COLORS["danger"]
        txt_cdi_header = "📉 Prejuízo"
        cor_geral_card = COLORS["danger"]
    elif lucro_nominal < lucro_cdi:
        cor_cdi_header = COLORS["warning"]
        pct = calc_percent(lucro_nominal, lucro_cdi)
        txt_cdi_header = f"⚠️ {fmt_pct(pct)}% do CDI"
        cor_geral_card = COLORS["warning"]
    else:
        cor_cdi_header = COLORS["success"]
        pct = calc_percent(lucro_nominal, lucro_cdi)
        txt_cdi_header = f"🚀 {fmt_pct(pct)}% do CDI"
        cor_geral_card = COLORS["success"]

    if lucro_nominal < 0:
        cor_poup_header = COLORS["danger"]
        txt_poup_header = "📉 Prejuízo"
    elif lucro_nominal == lucro_poup:
        cor_poup_header = COLORS["warning"]
        pct_p = calc_percent(lucro_nominal, lucro_poup)
        txt_poup_header = f"⚠️ {fmt_pct(pct_p)}% da Poupança"
    else:
        cor_poup_header = COLORS["success"]
        pct_p = calc_percent(lucro_nominal, lucro_poup)
        txt_poup_header = f"📈 {fmt_pct(pct_p)}% da Poupança"

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

    # --- ÁREA DE GRÁFICOS (VISUAL FILL RESTORED) ---
    st.markdown(f"""
    <div style="
        display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; 
        margin-top: 10px; margin-bottom: 10px; 
        background-color: #262730; padding: 12px; border-radius: 5px; border: 1px solid #444; width: 100%;">
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
        COR_CART = cor_geral_card
        COR_CDI = '#FFD700'
        COR_POUP = '#FF5722'

        # Plot da Carteira
        if not d['is_poup']:
            ax.plot(d['x'], d['y_cart_nom'], color=COR_CART, linewidth=2, label='Carteira (Nominal)')
            ax.plot(d['x'], d['y_cart_real'], color=COR_CART, linewidth=1, linestyle=':', alpha=0.5)
            # Fill Carteira (Cor forte)
            ax.fill_between(d['x'], d['y_cart_nom'], d['y_cart_real'], color=COR_CART, alpha=0.15, label='Perda Inflação (Cart)')
        
        # Plot do CDI
        ax.plot(d['x'], d['y_cdi_nom'], color=COR_CDI, linewidth=1.5, linestyle='--', alpha=0.7, label='CDI (Nominal)')
        ax.plot(d['x'], d['y_cdi_real'], color=COR_CDI, linewidth=0.5, linestyle=':', alpha=0.3)
        # Fill CDI (Amarelo transparente)
        ax.fill_between(d['x'], d['y_cdi_nom'], d['y_cdi_real'], color=COR_CDI, alpha=0.08)
        
        # Plot da Poupança
        style_poup = '-' if d['is_poup'] else ':'
        alpha_line = 0.9 if d['is_poup'] else 0.5
        ax.plot(d['x'], d['y_poup_nom'], color=COR_POUP, linewidth=1.5, linestyle=style_poup, alpha=alpha_line, label='Poupança (Nominal)')
        ax.plot(d['x'], d['y_poup_real'], color=COR_POUP, linewidth=0.5, linestyle=':', alpha=0.3)
        # Fill Poupança (Laranja transparente)
        ax.fill_between(d['x'], d['y_poup_nom'], d['y_poup_real'], color=COR_POUP, alpha=0.08)
        
        ax.legend(loc='upper left', frameon=False, ncol=2, fontsize='x-small')
        ax.grid(True, alpha=0.1)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['bottom'].set_color('#444'); ax.spines['left'].set_color('#444'); ax.tick_params(colors='#aaa')
        
        st.pyplot(fig, use_container_width=True)

    with g2:
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        vals = [i['peso'] for i in d['ativos']]
        labs = [f"{i['nome']}\n{i['peso']:.0f}%" for i in d['ativos']]
        colors = [i['cor'] for i in d['ativos']]
        if not vals: vals=[1]; labs=[""]; colors=["#333"]
        ax2.pie(vals, labels=labs, colors=colors, startangle=90, textprops={'color':"white", 'fontsize': 7}, wedgeprops=dict(width=0.45, edgecolor='#222'))
        ax2.set_title("Alocação", color='white', fontsize=10)
        st.pyplot(fig2, use_container_width=True)

with raiox_container:
    st.markdown("### 🧠 Raio-X da Estratégia")
    for item in d['ativos']:
        c1, c2 = st.columns([1, 4])
        c1.markdown(f"<span style='color:{item['cor']}; font-weight:bold;'>● {item['nome']}</span>", unsafe_allow_html=True)
        c2.caption(f"**{item['mercado']}** • {item['desc']}")
        st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", unsafe_allow_html=True)

if check_aposentadoria:
    st.markdown("### 🏖️ Análise de Viabilidade (Resultados)")
    
    if d['taxa_real_mensal'] > 0 and renda_desejada > 0:
        patrimonio_necessario = renda_desejada / d['taxa_real_mensal']
    else:
        patrimonio_necessario = 0
        
    saldo_final_real = d['final_real']
    atingiu = saldo_final_real >= patrimonio_necessario and saldo_final_real > 0
    
    if patrimonio_necessario > 0:
        prog = min(1.0, max(0.0, saldo_final_real / patrimonio_necessario))
    else:
        prog = 0.0
        
    if atingiu:
        st.success(f"🚀 **META ATINGIDA!** Sua carteira suporta a retirada e ainda cresce.")
        st.progress(prog, text=f"Sustentabilidade: {prog*100:.1f}%")
    else:
        if saldo_final_real < d['investido']:
            st.error("📉 **ALERTA CRÍTICO:** As retiradas estão consumindo seu patrimônio principal.")
        else:
            st.warning(f"⚠️ **Atenção:** Você tem saldo, mas não o suficiente para viver apenas de renda passiva perpétua.")
        
        st.progress(prog, text=f"Cobertura da Meta de Independência: {prog*100:.1f}%")
        st.caption(f"Para uma renda perpétua de R$ {renda_desejada}, você precisaria de R$ {patrimonio_necessario:,.2f} acumulados.")

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