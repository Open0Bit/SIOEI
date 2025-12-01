import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import os
import base64 # Adicionado para a nova forma de exibir o logo

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="SIOEI", layout="wide", page_icon="💰")

# --- 2. ESTILO CSS (DARK MODE) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .metric-card {
        background-color: #262730; border: 1px solid #444; padding: 15px;
        border-radius: 10px; text-align: center; margin-bottom: 10px;
    }
    .metric-main { font-size: 26px; font-weight: bold; color: white; }
    .metric-sub { font-size: 13px; margin-top: 2px; opacity: 0.8; font-family: monospace; }
    .metric-label { font-size: 11px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    div.stButton > button { width: 100%; }
    div.row-widget.stRadio > label { display: none; }
    .streamlit-expanderHeader { font-size: 14px; color: #90CAF9; }
    
    /* Box SIOEI 2.0 */
    .sioei-box {
        border: 1px solid #1b5e20;
        border-radius: 10px;
        padding: 20px;
        background-color: #0d1117;
        margin-top: 30px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DADOS ---
plt.style.use('dark_background')

ATIVOS = {
    # RENDA FIXA
    'Tesouro Selic':        {'retorno': 10.75, 'risco': 1, 'taxa': 0.20, 'tipo': 'RF', 'mercado': '🏦 Mercado Monetário', 'cor': '#4CAF50', 'desc': 'Risco Zero. Liquidez diária.'},
    'CDB Liquidez Diária':  {'retorno': 10.60, 'risco': 1, 'taxa': 0.00, 'tipo': 'RF', 'mercado': '🏦 Mercado Monetário', 'cor': '#03A9F4', 'desc': 'Reserva bancária.'},
    'Tesouro Prefixado':    {'retorno': 12.90, 'risco': 3, 'taxa': 0.20, 'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#CDDC39', 'desc': 'Taxa travada.'},
    'Tesouro IPCA+ (Curto)':{'retorno': 11.80, 'risco': 2, 'taxa': 0.20, 'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FFEB3B', 'desc': 'Proteção inflação.'},
    'Tesouro IPCA+ (Longo)':{'retorno': 12.30, 'risco': 4, 'taxa': 0.20, 'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF9800', 'desc': 'Aposentadoria.'},
    'Tesouro Renda+':       {'retorno': 12.60, 'risco': 3, 'taxa': 0.00, 'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF5722', 'desc': 'Renda mensal futura.'},
    'LCI/LCA (Isento)':     {'retorno': 11.20, 'risco': 2, 'taxa': 0.00, 'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#0288D1', 'desc': 'Isento de IR.'},
    'CDB Banco Médio':      {'retorno': 12.80, 'risco': 3, 'taxa': 0.00, 'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#01579B', 'desc': 'Maior retorno (FGC).'},
    'Debêntures Incent.':   {'retorno': 13.50, 'risco': 4, 'taxa': 0.00, 'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#E91E63', 'desc': 'Infraestrutura.'},
    'CRI/CRA (High Yield)': {'retorno': 15.80, 'risco': 7, 'taxa': 0.00, 'tipo': 'RF', 'mercado': '💳 Mercado de Crédito', 'cor': '#C2185B', 'desc': 'Dívida corporativa.'},
    'Fundo Multimercado':   {'retorno': 12.00, 'risco': 5, 'taxa': 2.00, 'tipo': 'RF', 'mercado': '📊 Fundos', 'cor': '#9C27B0', 'desc': 'Gestão ativa.'},

    # RENDA VARIÁVEL
    'Ações (Dividendos)':   {'retorno': 14.00, 'risco': 6, 'taxa': 0.00, 'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#00BCD4', 'desc': 'Empresas sólidas.'},
    'Ações (Small Caps)':   {'retorno': 18.00, 'risco': 8, 'taxa': 0.00, 'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#0097A7', 'desc': 'Crescimento.'},
    'ETF Ibovespa (BOVA11)':{'retorno': 14.50, 'risco': 7, 'taxa': 0.30, 'tipo': 'RV', 'mercado': '🏢 Mercado de Capitais', 'cor': '#006064', 'desc': 'Média de mercado.'},
    'FIIs (Tijolo)':        {'retorno': 12.50, 'risco': 4, 'taxa': 0.00, 'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#BA68C8', 'desc': 'Imóveis reais.'},
    'FIIs (Papel)':         {'retorno': 13.50, 'risco': 5, 'taxa': 0.00, 'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#8E24AA', 'desc': 'Dívida imobiliária.'},
    'Fiagro (Agronegócio)': {'retorno': 14.20, 'risco': 6, 'taxa': 0.00, 'tipo': 'RV', 'mercado': '🏗️ Imobiliário & Agro', 'cor': '#4A148C', 'desc': 'Cadeias agro.'},
    'Ações EUA (S&P500)':   {'retorno': 15.00, 'risco': 6, 'taxa': 0.25, 'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#3F51B5', 'desc': 'EUA Global.'},
    'Tech Stocks (Nasdaq)': {'retorno': 17.00, 'risco': 7, 'taxa': 0.30, 'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#304FFE', 'desc': 'Tecnologia.'},
    'REITs (Imóveis EUA)':  {'retorno': 14.00, 'risco': 6, 'taxa': 0.30, 'tipo': 'RV', 'mercado': '🌎 Internacional', 'cor': '#1A237E', 'desc': 'Dividendos Dólar.'},
    'Ouro / Dólar':         {'retorno': 8.50,  'risco': 4, 'taxa': 0.15, 'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#FFD700', 'desc': 'Hedge.'},
    'Bitcoin (BTC)':        {'retorno': 25.00, 'risco': 9, 'taxa': 0.50, 'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#F44336', 'desc': 'Cripto.'},
    'Ethereum/Altcoins':    {'retorno': 30.00, 'risco': 10,'taxa': 0.50, 'tipo': 'RV', 'mercado': '💱 Alternativos', 'cor': '#B71C1C', 'desc': 'Blockchain.'}
}

PERFIS = {
    'Conservador 🛡️': {'Tesouro Selic': 30, 'CDB Liquidez Diária': 30, 'LCI/LCA (Isento)': 20, 'Tesouro IPCA+ (Curto)': 20},
    'Moderado ⚖️':    {'Tesouro Selic': 20, 'LCI/LCA (Isento)': 20, 'Fundo Multimercado': 10, 'FIIs (Tijolo)': 20, 'Ações (Dividendos)': 15, 'Ações EUA (S&P500)': 15},
    'Agressivo 🚀':   {'Ações (Small Caps)': 20, 'Ações EUA (S&P500)': 20, 'Tech Stocks (Nasdaq)': 20, 'FIIs (Papel)': 20, 'Bitcoin (BTC)': 10, 'Tesouro IPCA+ (Longo)': 10}
}

TESES = {
    '👑 Rei dos Dividendos (Barsi)': {'desc': 'Foco em renda passiva recorrente e isenta.', 'pesos': {'Ações (Dividendos)': 40, 'FIIs (Tijolo)': 25, 'FIIs (Papel)': 15, 'Debêntures Incent.': 20}},
    '🌍 All Weather (Ray Dalio)': {'desc': 'Blindada para qualquer cenário.', 'pesos': {'Ações EUA (S&P500)': 30, 'Tesouro IPCA+ (Longo)': 40, 'Tesouro Selic': 15, 'Ouro / Dólar': 7.5, 'CDB Liquidez Diária': 7.5}},
    '🚜 Agro é Pop (Fiagro)': {'desc': 'Foco no motor do PIB brasileiro.', 'pesos': {'Fiagro (Agronegócio)': 40, 'LCI/LCA (Isento)': 30, 'CRI/CRA (High Yield)': 30}},
    '🏋️ Barbell (Nassim Taleb)': {'desc': 'Segurança extrema (90%) e Risco (10%).', 'pesos': {'Tesouro Selic': 85, 'Bitcoin (BTC)': 10, 'Ethereum/Altcoins': 5}},
    '🎓 Yale Model (David Swensen)': {'desc': 'Diversificação global.', 'pesos': {'Ações EUA (S&P500)': 30, 'Ações (Dividendos)': 15, 'FIIs (Tijolo)': 20, 'Tesouro IPCA+ (Curto)': 15, 'Tesouro IPCA+ (Longo)': 20}},
    '🛡️ Blindagem Total': {'desc': 'Proteção contra inflação.', 'pesos': {'Tesouro IPCA+ (Curto)': 25, 'Ações EUA (S&P500)': 25, 'Ouro / Dólar': 20, 'Tesouro Selic': 30}},
    '💰 Aposentadoria Renda+': {'desc': 'Acumulação longo prazo.', 'pesos': {'Tesouro Renda+': 40, 'FIIs (Tijolo)': 20, 'Ações (Dividendos)': 20, 'Tesouro IPCA+ (Longo)': 20}},
    '🇺🇸 Dolarização Tech': {'desc': 'Economia americana e Techs.', 'pesos': {'Ações EUA (S&P500)': 40, 'Tech Stocks (Nasdaq)': 30, 'REITs (Imóveis EUA)': 10, 'Tesouro Selic': 20}},
    '🔥 Pimenta Crypto': {'desc': 'Alto risco digitais.', 'pesos': {'Bitcoin (BTC)': 40, 'Ethereum/Altcoins': 20, 'Tech Stocks (Nasdaq)': 20, 'LC / RDB': 20}}
}

# --- 4. MOTOR MATEMÁTICO ---
def calcular(pesos_dict, v_inicial, v_mensal, anos, renda_desejada=0, anos_inicio_retirada=99, usar_retirada=False):
    inflacao_aa = 4.5; cdi_aa = 10.65; taxa_poupanca = 6.17
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
        
        # 1. Carteira
        y_cart_nom.append(y_cart_nom[-1] * (1 + tx_cart) + fluxo)
        fator_real_cart = (1 + tx_cart) / (1 + tx_inf)
        y_cart_real.append(y_cart_real[-1] * fator_real_cart + fluxo)
        
        # 2. CDI
        y_cdi_nom.append(y_cdi_nom[-1] * (1 + tx_cdi) + fluxo)
        fator_real_cdi = (1 + tx_cdi) / (1 + tx_inf)
        y_cdi_real.append(y_cdi_real[-1] * fator_real_cdi + fluxo)
        
        # 3. Poupança
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

# --- 5. ESTADO REATIVO ---
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

# --- 6. UI ---
# Função para preparar a imagem para o HTML
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

c_h1, c_h2 = st.columns([2, 1])
with c_h1:
    modo = st.radio("Modo de Operação:", ["Manual", "Automático", "Assistido"], 
                    horizontal=True, label_visibility="collapsed", key="modo_op", on_change=atualizar_reativo)
with c_h2:
    # ALTERADO: Uso de HTML/CSS direto para alinhamento robusto em todas as telas
    if logo_ok:
        img_base64 = image_to_base64(logo_image)
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; align-items: center;">
                <img src="data:image/png;base64,{img_base64}" width="130" style="max-width: 100%; height: auto;">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div style="display: flex; justify-content: flex-end; align-items: center; font-size: 50px;">💰</div>', unsafe_allow_html=True)

st.divider()

c1, c2, c3 = st.columns(3)
v_inicial = c1.number_input("Aporte Inicial (R$)", value=10000.0, step=100.0)
v_mensal = c2.number_input("Aporte Mensal (R$)", value=0.0, step=100.0)
anos = c3.slider("Prazo (Anos)", 1, 40, 10)

if modo == "Automático":
    st.selectbox("Selecione seu Perfil:", list(PERFIS.keys()), key="sel_perfil", on_change=atualizar_reativo)
    st.info("Perfil clássico baseado em tolerância a risco.")
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0: atualizar_reativo()
elif modo == "Assistido":
    st.selectbox("Selecione a Estratégia:", list(TESES.keys()), key="sel_tese", on_change=atualizar_reativo)
    st.info(TESES[st.session_state.sel_tese]['desc'])
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0: atualizar_reativo()
else:
    st.caption("Modo Manual: Abra o 'Ajuste Fino' abaixo para configurar.")

# --- SLIDERS ---
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

# --- CONTAINER DASHBOARD ---
dashboard_container = st.container()

# --- CONTAINER RAIO-X ---
raiox_container = st.container()

# --- SIOEI 2.0 (RODAPÉ) ---
st.markdown("<br><br>", unsafe_allow_html=True)
with st.container(border=True): # Caixa elegante com borda
    st.markdown("### 🏖️ Planejamento de Aposentadoria (SIOEI 2.0)")
    check_aposentadoria = st.checkbox("ATIVAR SIMULAÇÃO DE MESADA", value=False)
    
    renda_desejada = 0
    anos_retirada = 99
    
    if check_aposentadoria:
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            # FIX: min_value=0.0 mantido
            renda_desejada = st.number_input("Mesada / Renda Mensal (R$)", value=100.0, step=50.0, min_value=0.0) 
        with c_m2:
            anos_retirada = st.slider("Começar a receber em (Anos):", 0, anos, 5)

# --- CÁLCULO FINAL ---
pesos_atuais = {k: st.session_state[f"sl_{k}"] for k in ATIVOS.keys()}
d = calcular(pesos_atuais, v_inicial, v_mensal, anos, renda_desejada, anos_retirada, check_aposentadoria)

# --- POPULAR DASHBOARD ---
with dashboard_container:
    k1, k2, k3, k4 = st.columns(4)
    c_nom = "#29B6F6" if not d['is_poup'] else "#757575"
    c_risco = "#4CAF50" if d['risco'] < 4 else "#FFC107" if d['risco'] < 7 else "#F44336"
    l_risco = "Baixo" if d['risco'] < 4 else "Médio" if d['risco'] < 7 else "Alto"

    lucro_nom = d['final_nom'] - d['investido']
    lucro_real = d['final_real'] - d['investido']

    k1.markdown(f"""<div class="metric-card"><div class="metric-label">TOTAL INVESTIDO</div><div class="metric-main">R$ {d['investido']:,.2f}</div></div>""", unsafe_allow_html=True)
    
    # Card 2: Texto validado mantido
    k2.markdown(f"""<div class="metric-card" style="border-bottom: 3px solid {c_nom};"><div class="metric-label" style="color:{c_nom}">SALDO BRUTO (NOMINAL)</div><div class="metric-main">R$ {d['final_nom']:,.2f}</div><div class="metric-sub" style="color:{c_nom}">Desc. Inflação + Tx. e Custos: R$ {d['final_real']:,.2f}</div></div>""", unsafe_allow_html=True)
    
    # Card 3: Texto validado mantido
    k3.markdown(f"""<div class="metric-card" style="border-bottom: 3px solid #00E676;"><div class="metric-label" style="color:#00E676">LUCRO BRUTO (NOMINAL)</div><div class="metric-main">+ R$ {lucro_nom:,.2f}</div><div class="metric-sub">Desc. Inflação + Tx. e Custos: +R$ {lucro_real:,.2f}</div></div>""", unsafe_allow_html=True)
    
    k4.markdown(f"""<div class="metric-card"><div class="metric-label">RISCO ({l_risco})</div><div class="metric-main" style="color:{c_risco}">{d['risco']:.1f}/10</div></div>""", unsafe_allow_html=True)

    if d['is_poup']:
        st.warning("⚠️ MODO POUPANÇA (CARTEIRA VAZIA). Adicione ativos ou escolha uma estratégia.")

    g1, g2 = st.columns([2, 1])

    with g1:
        fig, ax = plt.subplots(figsize=(10, 5))
        COR_CART = '#29B6F6' # Azul Carteira
        COR_CDI = '#FFD700'  # Amarelo CDI
        COR_POUP = '#FF5722' # Laranja Poupança

        if not d['is_poup']:
            ax.plot(d['x'], d['y_cart_nom'], color=COR_CART, linewidth=2, label='Carteira (Nominal)')
            ax.plot(d['x'], d['y_cart_real'], color=COR_CART, linewidth=1, linestyle=':', alpha=0.5)
            label_fill = 'Perda Inflação' if not check_aposentadoria else 'Evolução Líquida (Com Retiradas)'
            ax.fill_between(d['x'], d['y_cart_nom'], d['y_cart_real'], color=COR_CART, alpha=0.15, label=label_fill)
        
        ax.plot(d['x'], d['y_cdi_nom'], color=COR_CDI, linewidth=1.5, linestyle='--', alpha=0.7, label='CDI (Nominal)')
        ax.plot(d['x'], d['y_cdi_real'], color=COR_CDI, linewidth=0.5, linestyle=':', alpha=0.3)
        ax.fill_between(d['x'], d['y_cdi_nom'], d['y_cdi_real'], color=COR_CDI, alpha=0.05)
        
        style_poup = '-' if d['is_poup'] else ':'
        alpha_line = 0.9 if d['is_poup'] else 0.5
        ax.plot(d['x'], d['y_poup_nom'], color=COR_POUP, linewidth=1.5, linestyle=style_poup, alpha=alpha_line, label='Poupança (Nominal)')
        ax.plot(d['x'], d['y_poup_real'], color=COR_POUP, linewidth=0.5, linestyle=':', alpha=0.3)
        ax.fill_between(d['x'], d['y_poup_nom'], d['y_poup_real'], color=COR_POUP, alpha=0.05)
        
        ax.set_title(f"Raio-X: Nominal vs Real ({anos} Anos)", color='white', loc='left')
        ax.legend(loc='upper left', frameon=False, ncol=2, fontsize='x-small')
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
        ax2.set_title("Alocação por Produto", color='white')
        st.pyplot(fig2)

# --- POPULAR RAIO-X ---
with raiox_container:
    st.markdown("### 🧠 Raio-X da Estratégia")
    for item in d['ativos']:
        c1, c2 = st.columns([1, 4])
        c1.markdown(f"<span style='color:{item['cor']}; font-weight:bold;'>● {item['nome']}</span>", unsafe_allow_html=True)
        c2.caption(f"**{item['mercado']}** • {item['desc']}")
        st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", unsafe_allow_html=True)

# --- POPULAR RESULTADOS SIOEI 2.0 (NO FINAL) ---
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
            st.error("📉 **ALERTA CRÍTICO:** As retiradas estão consumindo seu patrimônio principal. Você ficará sem dinheiro.")
        else:
            st.warning(f"⚠️ **Atenção:** Você tem saldo, mas não o suficiente para viver de renda perpétua (Sem tocar no principal).")
        
        st.progress(prog, text=f"Cobertura da Meta de Independência: {prog*100:.1f}%")
        st.caption(f"Para uma renda perpétua de R$ {renda_desejada}, você precisaria de R$ {patrimonio_necessario:,.2f} acumulados.")

# --- RODAPÉ (FOOTER) ---
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