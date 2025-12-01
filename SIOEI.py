import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SIOEI - Wealth Management", layout="wide", page_icon="💰")

# Estilo CSS para deixar com cara de App Profissional (Dark Mode forçado e ajustes)
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .metric-card {
        background-color: #262730;
        border: 1px solid #444;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    .metric-label {
        font-size: 14px;
        color: #aaa;
    }
    /* Ajuste para mobile */
    [data-testid="stSidebar"] {
        background-color: #161a24;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. DADOS (Mantidos do projeto original) ---
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

# --- 2. CÁLCULO ---
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

# --- 3. LAYOUT DA PÁGINA ---

# HEADER: Logo + Titulo + Modos
col_header_1, col_header_2, col_header_3 = st.columns([2, 4, 1])

with col_header_1:
    modo_selecionado = st.radio("Modo:", ["Automático", "Assistido", "Manual"], horizontal=True, label_visibility="collapsed")

with col_header_2:
    st.markdown("<h1 style='text-align: right; color: #00E676; margin: 0; padding: 0;'>SIOEI</h1>", unsafe_allow_html=True)

with col_header_3:
    # Tenta carregar logo local, se não, usa placeholder
    if os.path.exists("logo.jpg"):
        image = Image.open("logo.jpg")
        st.image(image, width=70)
    else:
        st.markdown("🖼️") # Placeholder se não tiver logo

st.divider()

# INPUTS FINANCEIROS
col_in_1, col_in_2, col_in_3 = st.columns(3)
with col_in_1:
    v_inicial = st.number_input("Aporte Inicial (R$)", value=10000.0, step=100.0)
with col_in_2:
    v_mensal = st.number_input("Aporte Mensal (R$)", value=1000.0, step=100.0)
with col_in_3:
    anos = st.slider("Prazo (Anos)", 1, 40, 15)

# --- LÓGICA DE ESTADO (SESSION STATE) ---
if 'pesos' not in st.session_state:
    st.session_state['pesos'] = {k: 0 for k in ATIVOS.keys()}

# SELEÇÃO DE MODOS
if modo_selecionado == "Automático":
    perfil = st.selectbox("Selecione seu Perfil:", list(PERFIS.keys()))
    st.info("Perfil clássico baseado em tolerância a risco.")
    pesos_alvo = PERFIS[perfil]
    # Atualiza session state apenas se necessário
    st.session_state['pesos'] = {k: pesos_alvo.get(k, 0) for k in ATIVOS.keys()}
    
elif modo_selecionado == "Assistido":
    tese = st.selectbox("Selecione a Estratégia:", list(TESES.keys()))
    st.info(TESES[tese]['desc'])
    pesos_alvo = TESES[tese]['pesos']
    st.session_state['pesos'] = {k: pesos_alvo.get(k, 0) for k in ATIVOS.keys()}

else: # Manual
    st.warning("Modo Manual: Abra o 'Ajuste Fino' abaixo para configurar. (Inicia como Poupança se zerado).")

# AJUSTE FINO (EXPANDER)
with st.expander("🎛️ AJUSTE FINO DA CARTEIRA (Clique para Abrir/Fechar)", expanded=(modo_selecionado == "Manual")):
    tab_rf, tab_rv = st.tabs(["🛡️ RENDA FIXA", "📈 RENDA VARIÁVEL"])
    
    # Criar sliders dinamicamente baseados no session_state
    with tab_rf:
        cols_rf = st.columns(3)
        rf_ativos = [k for k, v in ATIVOS.items() if v['tipo'] == 'RF']
        for i, ativo in enumerate(rf_ativos):
            with cols_rf[i % 3]:
                st.session_state['pesos'][ativo] = st.slider(
                    ativo, 0, 100, int(st.session_state['pesos'][ativo]), step=5, key=f"s_{ativo}"
                )
    
    with tab_rv:
        cols_rv = st.columns(3)
        rv_ativos = [k for k, v in ATIVOS.items() if v['tipo'] == 'RV']
        for i, ativo in enumerate(rv_ativos):
            with cols_rv[i % 3]:
                st.session_state['pesos'][ativo] = st.slider(
                    ativo, 0, 100, int(st.session_state['pesos'][ativo]), step=5, key=f"s_{ativo}"
                )

# --- CÁLCULOS E DASHBOARD ---
d = calcular(st.session_state['pesos'], v_inicial, v_mensal, anos)

# KPI CARDS
col1, col2, col3, col4 = st.columns(4)
cor_nom = "#00BCD4" if not d['is_poup'] else "#757575"
cor_risco = "#4CAF50" if d['risco'] < 4 else "#FFC107" if d['risco'] < 7 else "#F44336"
risco_label = "Baixo" if d['risco'] < 4 else "Médio" if d['risco'] < 7 else "Alto"

with col1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">TOTAL INVESTIDO</div><div class="metric-value">R$ {d['investido']:,.2f}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card" style="border-bottom: 3px solid {cor_nom};"><div class="metric-label" style="color:{cor_nom}">NOMINAL (BRUTO)</div><div class="metric-value">R$ {d['final_nom']:,.2f}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card" style="border-bottom: 3px solid #00E676;"><div class="metric-label" style="color:#00E676">REAL (PODER COMPRA)</div><div class="metric-value">R$ {d['final_real']:,.2f}</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">RISCO ({risco_label})</div><div class="metric-value" style="color:{cor_risco}">{d['risco']:.1f}/10</div></div>""", unsafe_allow_html=True)

if d['is_poup']:
    st.error("⚠️ ALERTA: Dinheiro parado na Poupança! Configure a carteira para ver rendimentos reais.")

st.write("") # Espaçamento

# GRÁFICOS
col_graph, col_pie = st.columns([7, 4])

with col_graph:
    fig_line, ax1 = plt.subplots(figsize=(10, 5))
    color_line = '#00BCD4' if not d['is_poup'] else '#9E9E9E'
    ax1.plot(d['x'], d['y_cart'], color=color_line, linewidth=2, label='Nominal (Bruto)')
    ax1.plot(d['x'], d['y_real'], color='#00E676', linewidth=2, label='Real (Poder Compra)')
    ax1.plot(d['x'], d['y_inf'], color='#FF9800', linestyle=':', alpha=0.6, label='Inflação')
    ax1.plot(d['x'], d['y_cdi'], color='#fff', linestyle='--', alpha=0.3, label='CDI')
    alpha_poup = 0.8 if d['is_poup'] else 0.3
    ax1.plot(d['x'], d['y_poup'], color='#F44336', linestyle='--', alpha=alpha_poup, label='Poupança')
    ax1.fill_between(d['x'], d['y_cart'], d['y_real'], color=color_line, alpha=0.1)
    
    ax1.set_title(f"Projeção Comparativa ({anos} anos)", color='white', loc='left')
    ax1.legend(loc='upper left', fontsize='small', frameon=False, ncol=2)
    ax1.grid(True, alpha=0.1)
    # Remover bordas
    ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_color('#444'); ax1.spines['left'].set_color('#444')
    ax1.tick_params(colors='#aaa')
    st.pyplot(fig_line)

with col_pie:
    fig_pie, ax2 = plt.subplots(figsize=(6, 6))
    vals = [i['peso'] for i in d['ativos']]
    labs = [f"{i['nome']}\n{i['peso']:.0f}%" for i in d['ativos']]
    colors = [i['cor'] for i in d['ativos']]
    
    font_size = 9 if len(vals) < 10 else 8
    wedges, texts = ax2.pie(vals, labels=labs, colors=colors, startangle=90,
                            labeldistance=1.1, textprops={'color':"white", 'fontsize': font_size},
                            wedgeprops=dict(width=0.45, edgecolor='#222'))
    ax2.set_title("Alocação Atual", color='white')
    st.pyplot(fig_pie)

# TABELA EDUCATIVA
st.subheader("🧠 Raio-X da Estratégia")
for item in d['ativos']:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.markdown(f"<span style='color:{item['cor']}; font-weight:bold;'>● {item['nome']}</span>", unsafe_allow_html=True)
    with col_b:
        st.caption(item['desc'])
    st.divider()