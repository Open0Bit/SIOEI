import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SIOEI", layout="wide", page_icon="💰")

# --- 2. ESTILO CSS (DARK MODE) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .metric-card {
        background-color: #262730; border: 1px solid #444; padding: 15px;
        border-radius: 10px; text-align: center; margin-bottom: 10px;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: white; }
    .metric-label { font-size: 12px; color: #aaa; text-transform: uppercase; }
    div.stButton > button { width: 100%; }
    /* Ajuste para esconder o label do radio button se necessário */
    div.row-widget.stRadio > label { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 3. DADOS (UNIVERSO DE ATIVOS) ---
plt.style.use('dark_background')

ATIVOS = {
    # 1.1 TESOURO
    'Tesouro Selic':        {'retorno': 10.75, 'risco': 1, 'tipo': 'RF', 'cat': 'Tesouro Direto', 'cor': '#4CAF50', 'desc': 'Risco Zero. Liquidez diária.'},
    'Tesouro Prefixado':    {'retorno': 12.90, 'risco': 3, 'tipo': 'RF', 'cat': 'Tesouro Direto', 'cor': '#CDDC39', 'desc': 'Taxa travada. Ganha na queda.'},
    'Tesouro IPCA+ (Curto)':{'retorno': 11.80, 'risco': 2, 'tipo': 'RF', 'cat': 'Tesouro Direto', 'cor': '#FFEB3B', 'desc': 'Proteção inflação curto prazo.'},
    'Tesouro IPCA+ (Longo)':{'retorno': 12.30, 'risco': 4, 'tipo': 'RF', 'cat': 'Tesouro Direto', 'cor': '#FF9800', 'desc': 'Aposentadoria. Volátil.'},
    'Tesouro Renda+':       {'retorno': 12.60, 'risco': 3, 'tipo': 'RF', 'cat': 'Tesouro Direto', 'cor': '#FF5722', 'desc': 'Renda mensal futura.'},
    # 1.2 BANCÁRIOS
    'CDB Liquidez Diária':  {'retorno': 10.60, 'risco': 1, 'tipo': 'RF', 'cat': 'Emissão Bancária', 'cor': '#03A9F4', 'desc': 'Reserva de emergência.'},
    'LCI/LCA (Isento)':     {'retorno': 11.20, 'risco': 2, 'tipo': 'RF', 'cat': 'Emissão Bancária', 'cor': '#0288D1', 'desc': 'Isento de IR. Imóveis/Agro.'},
    'CDB Banco Médio':      {'retorno': 12.80, 'risco': 3, 'tipo': 'RF', 'cat': 'Emissão Bancária', 'cor': '#01579B', 'desc': 'Retorno maior c/ FGC.'},
    'LC / RDB':             {'retorno': 13.00, 'risco': 4, 'tipo': 'RF', 'cat': 'Emissão Bancária', 'cor': '#0D47A1', 'desc': 'Financeiras. Alto retorno.'},
    # 1.3 CRÉDITO
    'Debêntures Incent.':   {'retorno': 13.50, 'risco': 4, 'tipo': 'RF', 'cat': 'Crédito Privado', 'cor': '#E91E63', 'desc': 'Infraestrutura. Isento IR.'},
    'Debêntures Comuns':    {'retorno': 14.20, 'risco': 5, 'tipo': 'RF', 'cat': 'Crédito Privado', 'cor': '#880E4F', 'desc': 'Empresas gerais. Tributado.'},
    'CRI/CRA (High Grade)': {'retorno': 13.20, 'risco': 5, 'tipo': 'RF', 'cat': 'Crédito Privado', 'cor': '#AD1457', 'desc': 'Securitização segura.'},
    'CRI/CRA (High Yield)': {'retorno': 15.80, 'risco': 7, 'tipo': 'RF', 'cat': 'Crédito Privado', 'cor': '#C2185B', 'desc': 'Alto risco e retorno.'},
    'Fundo Multimercado':   {'retorno': 12.00, 'risco': 5, 'tipo': 'RF', 'cat': 'Fundos', 'cor': '#9C27B0', 'desc': 'Gestão ativa (Juros/Câmbio).'},
    # 2.1 AÇÕES BR
    'Ações (Dividendos)':   {'retorno': 14.00, 'risco': 6, 'tipo': 'RV', 'cat': 'Ações Brasil', 'cor': '#00BCD4', 'desc': 'Empresas maduras.'},
    'Ações (Small Caps)':   {'retorno': 18.00, 'risco': 8, 'tipo': 'RV', 'cat': 'Ações Brasil', 'cor': '#0097A7', 'desc': 'Empresas crescimento.'},
    'ETF Ibovespa (BOVA11)':{'retorno': 14.50, 'risco': 7, 'tipo': 'RV', 'cat': 'Ações Brasil', 'cor': '#006064', 'desc': 'Média do mercado.'},
    # 2.2 FIIs
    'FIIs (Tijolo)':        {'retorno': 12.50, 'risco': 4, 'tipo': 'RV', 'cat': 'FIIs & Fiagros', 'cor': '#BA68C8', 'desc': 'Imóveis físicos.'},
    'FIIs (Papel)':         {'retorno': 13.50, 'risco': 5, 'tipo': 'RV', 'cat': 'FIIs & Fiagros', 'cor': '#8E24AA', 'desc': 'Dívida imobiliária.'},
    'Fiagro (Agronegócio)': {'retorno': 14.20, 'risco': 6, 'tipo': 'RV', 'cat': 'FIIs & Fiagros', 'cor': '#4A148C', 'desc': 'Cadeias produtivas agro.'},
    # 2.3 INTERNACIONAL
    'Ações EUA (S&P500)':   {'retorno': 15.00, 'risco': 6, 'tipo': 'RV', 'cat': 'Internacional', 'cor': '#3F51B5', 'desc': '500 maiores dos EUA.'},
    'Tech Stocks (Nasdaq)': {'retorno': 17.00, 'risco': 7, 'tipo': 'RV', 'cat': 'Internacional', 'cor': '#304FFE', 'desc': 'Big Techs (Apple, AI).'},
    'REITs (Imóveis EUA)':  {'retorno': 14.00, 'risco': 6, 'tipo': 'RV', 'cat': 'Internacional', 'cor': '#1A237E', 'desc': 'Dividendos em Dólar.'},
    # 2.4 ALTERNATIVOS
    'Ouro / Dólar':         {'retorno': 8.50,  'risco': 4, 'tipo': 'RV', 'cat': 'Alternativos', 'cor': '#FFD700', 'desc': 'Proteção (Hedge).'},
    'Bitcoin (BTC)':        {'retorno': 25.00, 'risco': 9, 'tipo': 'RV', 'cat': 'Alternativos', 'cor': '#F44336', 'desc': 'Ouro Digital.'},
    'Ethereum/Altcoins':    {'retorno': 30.00, 'risco': 10,'tipo': 'RV', 'cat': 'Alternativos', 'cor': '#B71C1C', 'desc': 'Blockchain & Web3.'}
}

PERFIS = {
    'Conservador 🛡️': {'Tesouro Selic': 30, 'CDB Liquidez Diária': 30, 'LCI/LCA (Isento)': 20, 'Tesouro IPCA+ (Curto)': 20},
    'Moderado ⚖️':    {'Tesouro Selic': 20, 'LCI/LCA (Isento)': 20, 'Fundo Multimercado': 10, 'FIIs (Tijolo)': 20, 'Ações (Dividendos)': 15, 'Ações EUA (S&P500)': 15},
    'Agressivo 🚀':   {'Ações (Small Caps)': 20, 'Ações EUA (S&P500)': 20, 'Tech Stocks (Nasdaq)': 20, 'FIIs (Papel)': 20, 'Bitcoin (BTC)': 10, 'Tesouro IPCA+ (Longo)': 10}
}

TESES = {
    '👑 Rei dos Dividendos (Barsi)': {'desc': 'Foco em renda passiva recorrente e isenta.', 'pesos': {'Ações (Dividendos)': 40, 'FIIs (Tijolo)': 25, 'FIIs (Papel)': 15, 'Debêntures Incent.': 20}},
    '🌍 All Weather (Ray Dalio)': {'desc': 'Blindada para qualquer cenário econômico.', 'pesos': {'Ações EUA (S&P500)': 30, 'Tesouro IPCA+ (Longo)': 40, 'Tesouro Selic': 15, 'Ouro / Dólar': 7.5, 'CDB Liquidez Diária': 7.5}},
    '🚜 Agro é Pop (Fiagro)': {'desc': 'Foco total no motor do PIB brasileiro.', 'pesos': {'Fiagro (Agronegócio)': 40, 'LCI/LCA (Isento)': 30, 'CRI/CRA (High Grade)': 30}},
    '🏋️ Barbell (Nassim Taleb)': {'desc': 'Segurança extrema (90%) e Risco extremo (10%).', 'pesos': {'Tesouro Selic': 85, 'Bitcoin (BTC)': 10, 'Ethereum/Altcoins': 5}},
    '🎓 Yale Model (David Swensen)': {'desc': 'Diversificação institucional global.', 'pesos': {'Ações EUA (S&P500)': 30, 'Ações (Dividendos)': 15, 'FIIs (Tijolo)': 20, 'Tesouro IPCA+ (Curto)': 15, 'Tesouro IPCA+ (Longo)': 20}},
    '🛡️ Blindagem Total': {'desc': 'Proteção contra inflação e desvalorização.', 'pesos': {'Tesouro IPCA+ (Curto)': 25, 'Ações EUA (S&P500)': 25, 'Ouro / Dólar': 20, 'Tesouro Selic': 30}},
    '💰 Aposentadoria Renda+': {'desc': 'Acumulação focada no longo prazo.', 'pesos': {'Tesouro Renda+': 40, 'FIIs (Tijolo)': 20, 'Ações (Dividendos)': 20, 'Tesouro IPCA+ (Longo)': 20}},
    '🇺🇸 Dolarização Tech': {'desc': 'Exposição à economia americana e Techs.', 'pesos': {'Ações EUA (S&P500)': 40, 'Tech Stocks (Nasdaq)': 30, 'REITs (Imóveis EUA)': 10, 'Tesouro Selic': 20}},
    '🔥 Pimenta Crypto': {'desc': 'Alto risco em ativos digitais.', 'pesos': {'Bitcoin (BTC)': 40, 'Ethereum/Altcoins': 20, 'Tech Stocks (Nasdaq)': 20, 'LC / RDB': 20}}
}

# --- 4. MOTOR MATEMÁTICO ---
def calcular(pesos_dict, v_inicial, v_mensal, anos):
    inflacao_aa = 4.5; cdi_aa = 10.65; taxa_poupanca = 6.17
    total = sum(pesos_dict.values())
    
    usar_poupanca = False
    if total == 0:
        usar_poupanca = True
        total = 1
        retorno_cart = taxa_poupanca
        risco_pond = 0.5
        ativos_usados = [{'nome': 'Dinheiro Parado (Poupança)', 'peso': 100, 'cor': '#757575', 'desc': 'DINHEIRO PARADO! Perdendo valor para inflação.'}]
    else:
        retorno_cart = 0
        risco_pond = 0
        ativos_usados = []
        for nome, peso in pesos_dict.items():
            if peso > 0:
                info = ATIVOS[nome]
                peso_real = peso / total
                retorno_cart += info['retorno'] * peso_real
                risco_pond += info['risco'] * peso_real
                ativos_usados.append({'nome': nome, 'peso': peso_real*100, 'cor': info['cor'], 'desc': info['desc']})
    
    meses = anos * 12
    tx_cart = (1 + retorno_cart/100)**(1/12) - 1
    tx_cdi = (1 + cdi_aa/100)**(1/12) - 1
    tx_poup = (1 + taxa_poupanca/100)**(1/12) - 1
    tx_inf = (1 + inflacao_aa/100)**(1/12) - 1
    
    y_cart, y_real, y_cdi, y_poup, y_inf = [v_inicial], [v_inicial], [v_inicial], [v_inicial], [v_inicial]
    investido = v_inicial
    
    for _ in range(meses):
        y_cart.append(y_cart[-1] * (1 + tx_cart) + v_mensal)
        y_cdi.append(y_cdi[-1] * (1 + tx_cdi) + v_mensal)
        y_poup.append(y_poup[-1] * (1 + tx_poup) + v_mensal)
        y_inf.append(y_inf[-1] * (1 + tx_inf) + v_mensal)
        fator_real = (1 + tx_cart) / (1 + tx_inf)
        y_real.append(y_real[-1] * fator_real + v_mensal)
        investido += v_mensal
        
    return {
        'x': np.arange(meses + 1),
        'y_cart': y_cart, 'y_real': y_real, 'y_cdi': y_cdi, 'y_poup': y_poup, 'y_inf': y_inf,
        'final_nom': y_cart[-1], 'final_real': y_real[-1], 'investido': investido, 
        'retorno_aa': retorno_cart, 'risco': risco_pond, 'ativos': ativos_usados, 'is_poup': usar_poupanca
    }

# --- 5. GERENCIAMENTO DE ESTADO INTELIGENTE (REATIVO) ---

# Inicializa chaves de sessão
for k in ATIVOS.keys():
    if f"sl_{k}" not in st.session_state: st.session_state[f"sl_{k}"] = 0

# Esta função é a mágica: ela roda toda vez que você muda o Dropdown
def atualizar_carteira_reativa():
    """Atualiza os pesos imediatamente baseado no modo e seleção atual"""
    modo_atual = st.session_state.get("modo_op")
    
    pesos_novos = {}
    if modo_atual == "Automático":
        perfil = st.session_state.get("sel_perfil")
        if perfil: pesos_novos = PERFIS[perfil]
    elif modo_atual == "Assistido":
        tese = st.session_state.get("sel_tese")
        if tese: pesos_novos = TESES[tese]['pesos']
    
    # Se for manual, não faz nada (preserva o que o usuário mexeu)
    if modo_atual == "Manual":
        return

    # Aplica os pesos nos sliders (memória)
    for k in ATIVOS.keys():
        st.session_state[f"sl_{k}"] = pesos_novos.get(k, 0)

# --- 6. INTERFACE ---

# Carregamento de Logo
try:
    if os.path.exists('SIOEI LOGO.jpg'): logo_image = Image.open('SIOEI LOGO.jpg')
    else:
        url = "https://raw.githubusercontent.com/Open0Bit/SIOEI/main/SIOEI%20LOGO.jpg"
        logo_image = Image.open(BytesIO(requests.get(url).content))
    logo_ok = True
except: logo_ok = False

# Cabeçalho
c_h1, c_h2 = st.columns([2, 1])
with c_h1:
    # O on_change no radio garante que ao trocar de aba, ele atualize
    modo = st.radio("Modo de Operação:", ["Manual", "Automático", "Assistido"], 
                    horizontal=True, label_visibility="collapsed", key="modo_op", 
                    on_change=atualizar_carteira_reativa)
with c_h2:
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown("<h2 style='text-align: right; color: #00E676; margin:0;'>SIOEI</h2>", unsafe_allow_html=True)
    with c2: 
        if logo_ok: st.image(logo_image, width=60)
        else: st.markdown("💰")

st.divider()

# Inputs
c1, c2, c3 = st.columns(3)
v_inicial = c1.number_input("Aporte Inicial (R$)", value=10000.0, step=100.0)
v_mensal = c2.number_input("Aporte Mensal (R$)", value=1000.0, step=100.0)
anos = c3.slider("Prazo (Anos)", 1, 40, 15)

# Lógica de Exibição
if modo == "Automático":
    # O on_change aqui faz a mágica de eliminar o botão "Aplicar"
    st.selectbox("Selecione seu Perfil:", list(PERFIS.keys()), key="sel_perfil", on_change=atualizar_carteira_reativa)
    st.info("Perfil clássico baseado em tolerância a risco.")
    
    # Check de segurança para carregar na primeira vez que abre o modo
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0:
        atualizar_carteira_reativa()

elif modo == "Assistido":
    st.selectbox("Selecione a Estratégia:", list(TESES.keys()), key="sel_tese", on_change=atualizar_carteira_reativa)
    st.info(TESES[st.session_state.sel_tese]['desc'])
    
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0:
        atualizar_carteira_reativa()

else:
    st.caption("Modo Manual: Abra o 'Ajuste Fino' abaixo para configurar.")

# SLIDERS (Expander sempre FECHADO por padrão: expanded=False)
with st.expander("🎛️ AJUSTE FINO DA CARTEIRA (Clique para Abrir/Fechar)", expanded=False):
    t1, t2 = st.tabs(["🛡️ RENDA FIXA", "📈 RENDA VARIÁVEL"])
    
    with t1:
        cols = st.columns(3)
        rf_items = [k for k, v in ATIVOS.items() if v['tipo'] == 'RF']
        for i, k in enumerate(rf_items):
            with cols[i%3]:
                st.slider(k, 0, 100, key=f"sl_{k}")
    with t2:
        cols = st.columns(3)
        rv_items = [k for k, v in ATIVOS.items() if v['tipo'] == 'RV']
        for i, k in enumerate(rv_items):
            with cols[i%3]:
                st.slider(k, 0, 100, key=f"sl_{k}")

# --- CÁLCULO E PLOTAGEM ---
# Pega os valores direto da memória atualizada
pesos_atuais = {k: st.session_state[f"sl_{k}"] for k in ATIVOS.keys()}
d = calcular(pesos_atuais, v_inicial, v_mensal, anos)

# KPI
k1, k2, k3, k4 = st.columns(4)
c_nom = "#00BCD4" if not d['is_poup'] else "#757575"
c_risco = "#4CAF50" if d['risco'] < 4 else "#FFC107" if d['risco'] < 7 else "#F44336"
l_risco = "Baixo" if d['risco'] < 4 else "Médio" if d['risco'] < 7 else "Alto"

k1.markdown(f"""<div class="metric-card"><div class="metric-label">TOTAL INVESTIDO</div><div class="metric-value">R$ {d['investido']:,.2f}</div></div>""", unsafe_allow_html=True)
k2.markdown(f"""<div class="metric-card" style="border-bottom: 3px solid {c_nom};"><div class="metric-label" style="color:{c_nom}">NOMINAL (BRUTO)</div><div class="metric-value">R$ {d['final_nom']:,.2f}</div></div>""", unsafe_allow_html=True)
k3.markdown(f"""<div class="metric-card" style="border-bottom: 3px solid #00E676;"><div class="metric-label" style="color:#00E676">REAL (PODER COMPRA)</div><div class="metric-value">R$ {d['final_real']:,.2f}</div></div>""", unsafe_allow_html=True)
k4.markdown(f"""<div class="metric-card"><div class="metric-label">RISCO ({l_risco})</div><div class="metric-value" style="color:{c_risco}">{d['risco']:.1f}/10</div></div>""", unsafe_allow_html=True)

if d['is_poup']:
    st.warning("⚠️ MODO POUPANÇA (CARTEIRA VAZIA). Adicione ativos ou escolha uma estratégia.")

# GRÁFICOS
g1, g2 = st.columns([2, 1])

with g1:
    fig, ax = plt.subplots(figsize=(10, 5))
    c_line = '#00BCD4' if not d['is_poup'] else '#9E9E9E'
    ax.plot(d['x'], d['y_cart'], color=c_line, linewidth=2, label='Nominal')
    ax.plot(d['x'], d['y_real'], color='#00E676', linewidth=2, label='Real')
    ax.plot(d['x'], d['y_inf'], color='#FF9800', linestyle=':', alpha=0.5, label='Inflação')
    ax.plot(d['x'], d['y_cdi'], color='white', linestyle='--', alpha=0.3, label='CDI')
    if d['is_poup']: ax.plot(d['x'], d['y_poup'], color='#F44336', linestyle='--', label='Poupança')
    
    ax.fill_between(d['x'], d['y_cart'], d['y_real'], color=c_line, alpha=0.1)
    ax.set_title(f"Projeção ({anos} Anos)", color='white', loc='left')
    ax.legend(loc='upper left', frameon=False, ncol=2, fontsize='small')
    ax.grid(True, alpha=0.1)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False); ax.spines['bottom'].set_color('#444'); ax.spines['left'].set_color('#444'); ax.tick_params(colors='#aaa')
    st.pyplot(fig)

with g2:
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    vals = [i['peso'] for i in d['ativos']]
    labs = [f"{i['nome']}\n{i['peso']:.0f}%" for i in d['ativos']]
    colors = [i['cor'] for i in d['ativos']]
    if not vals: vals=[1]; labs=[""]; colors=["#333"]
    
    ax2.pie(vals, labels=labs, colors=colors, startangle=90, textprops={'color':"white", 'fontsize': 8}, wedgeprops=dict(width=0.45, edgecolor='#222'))
    ax2.set_title("Alocação", color='white')
    st.pyplot(fig2)

st.markdown("### 🧠 Raio-X da Carteira")
for item in d['ativos']:
    c1, c2 = st.columns([1, 4])
    c1.markdown(f"<span style='color:{item['cor']}; font-weight:bold;'>● {item['nome']}</span>", unsafe_allow_html=True)
    c2.caption(item['desc'])
    st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", unsafe_allow_html=True)