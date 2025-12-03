"""
=============================================================================
PROJETO: SIOEI (Sistema Inteligente de Otimização e Execução de Investimentos)
VERSÃO: 4.2 (Michelangelo Edition 🎨) - REATOR UI
CODENAME: Sprout 🌱 - Edição "Raio-X ANBIMA/B3" + UI Premium
DESCRIÇÃO: Calibração baseada no comportamento real do investidor brasileiro (2024/25).
           Foco em Rentismo (CDI), Paixão por FIIs e Alta Adoção de Cripto.
           *Nova Interface Gráfica Reativa*
AUTOR: Aegra Code Guild (Refinado por Gemini, Depurado por Claude)
DATA: Dezembro/2025
=============================================================================
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import base64
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="SIOEI - Realidade Brasil", 
    layout="wide", 
    page_icon="🇧🇷"
)

# ==============================================================================
# 2. ESTILIZAÇÃO (DESIGN SYSTEM MICHELANGELO 🎨)
# ==============================================================================
st.markdown("""
<style>
    /* RESET BÁSICO E TRANSIÇÃO SUAVE DE FUNDO */
    .stApp { 
        transition: background 0.5s ease; 
        background-color: #0E1117; /* Fallback */
    }
    
    /* CARDS DE MÉTRICAS */
    .metric-card {
        background-color: rgba(38, 39, 48, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1); 
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
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.3); }

    .metric-main { font-size: 24px; font-weight: bold; color: white; margin: 5px 0; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
    .metric-detail { font-size: 11px; margin-top: 8px; opacity: 0.8; font-family: monospace; color: #E0E0E0; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px; width: 100%; line-height: 1.2; white-space: normal; }
    .metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 700; }
    
    /* BADGES DE STATUS */
    .status-badge { font-size: 12px; padding: 4px 8px; border-radius: 4px; font-weight: bold; display: inline-block; margin-right: 10px; }
    .status-live { background-color: #1B5E20; color: #A5D6A7; border: 1px solid #2E7D32; }
    .status-warning { background-color: #F57F17; color: #FFF9C4; border: 1px solid #FBC02D; }
    .status-static { background-color: #B71C1C; color: #FFCDD2; border: 1px solid #C62828; }
    
    div.stButton > button { width: 100%; }

    /* --- ESTILIZAÇÃO AVANÇADA DOS BOTÕES DE MODO (RADIO) --- */
    
    /* Esconde as bolinhas originais e labels padrão */
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* Container dos botões */
    div.row-widget.stRadio > div[role="radiogroup"] {
        background-color: rgba(0,0,0,0.2);
        padding: 10px;
        border-radius: 15px;
        display: flex;
        justify-content: center;
        gap: 15px;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* O estilo do botão em si (Label) */
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 20px 10px !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        text-align: center !important;
        flex: 1 !important; /* Faz ocuparem espaço igual */
        margin: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 120px;
    }

    /* Texto dentro do botão */
    div.row-widget.stRadio > div[role="radiogroup"] > label p {
        font-size: 16px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        color: #B0B0B0 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Hover Effect */
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
        border-color: rgba(255,255,255,0.3) !important;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover p {
        color: white !important;
    }

    /* --- ESTADO ATIVO (SELECIONADO) --- */
    /* Focando no atributo aria-checked para estilizar o item ativo */
    div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)) !important;
        border: 2px solid !important; /* A cor da borda virá do CSS injetado dinamicamente */
        box-shadow: 0 0 20px rgba(0,0,0,0.4), inset 0 0 10px rgba(255,255,255,0.05) !important;
        transform: scale(1.02) !important;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] p {
        color: white !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.5);
    }

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
    """Obtém dados macroeconômicos do Banco Central do Brasil"""
    macro = {'selic': 10.75, 'ipca': 4.50, 'status': False}
    try:
        # Timeout aumentado para maior confiabilidade
        url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        r_selic = requests.get(url_selic, timeout=10)
        r_selic.raise_for_status()
        macro['selic'] = float(r_selic.json()[0]['valor'])
        
        url_ipca = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1?formato=json"
        r_ipca = requests.get(url_ipca, timeout=10)
        r_ipca.raise_for_status()
        macro['ipca'] = float(r_ipca.json()[0]['valor'])
        
        macro['status'] = True
        logger.info("Dados do BCB obtidos com sucesso")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Erro ao obter dados do BCB: {e}")
    except (KeyError, IndexError, ValueError) as e:
        logger.warning(f"Erro ao processar dados do BCB: {e}")
    
    return macro

# --- 3.2 CONEXÃO YAHOO FINANCE ---
TICKERS_MAP = {
    'ETF Ibovespa (BOVA11)': 'BOVA11.SA', 
    'Ações EUA (S&P500)': 'IVVB11.SA', 
    'Tech Stocks (Nasdaq)': 'NASD11.SA', 
    'Bitcoin (BTC)': 'BTC-USD',
    'Ethereum/Altcoins': 'ETH-USD', 
    'Ouro / Dólar': 'GOLD11.SA',
    'FIIs (Tijolo)': 'IFIX', 
    'Ações (Dividendos)': 'IDIV' 
}

@st.cache_data(ttl=43200, show_spinner=False)
def obter_retornos_live():
    """
    Obtém retornos reais dos ativos via Yahoo Finance (1 ano)
    """
    dados_live = {}
    valid_tickers = [t for t in TICKERS_MAP.values() if t not in ['IFIX', 'IDIV']]
    
    try:
        data = yf.download(
            valid_tickers, 
            period="1y", 
            interval="1d", 
            progress=False,
            show_errors=False
        )['Adj Close']
        
        for nome, ticker in TICKERS_MAP.items():
            if ticker in valid_tickers:
                try:
                    if ticker in data.columns:
                        series = data[ticker].dropna()
                        
                        if len(series) < 30:
                            logger.debug(f"{ticker}: Dados insuficientes ({len(series)} dias)")
                            continue
                        
                        p_ini = series.iloc[0]
                        p_fim = series.iloc[-1]
                        
                        if p_ini <= 0:
                            logger.warning(f"{ticker}: Preço inicial inválido ({p_ini})")
                            continue
                        
                        ret = ((p_fim / p_ini) - 1) * 100
                        
                        if np.isnan(ret) or np.isinf(ret):
                            logger.warning(f"{ticker}: Retorno inválido (NaN/Inf)")
                            continue
                        
                        dados_live[nome] = ret
                        logger.debug(f"{ticker}: Retorno de {ret:.2f}% (válido)")
                        
                except Exception as e:
                    logger.debug(f"Erro ao processar {ticker}: {e}")
                    continue
                    
        logger.info(f"✓ Obtidos {len(dados_live)} retornos live do mercado")
    except Exception as e:
        logger.warning(f"Erro ao obter dados do Yahoo Finance: {e}")
    
    return dados_live

# --- EXECUÇÃO DAS CONEXÕES ---
with st.spinner('🔍 Analisando mercado brasileiro (B3/ANBIMA)...'):
    MACRO_DATA = obter_dados_bcb()
    LIVE_RETURNS = obter_retornos_live()

# Cálculo de Derivados
SELIC_ATUAL = MACRO_DATA['selic']
IPCA_ATUAL = MACRO_DATA['ipca']
CDI_ATUAL = max(SELIC_ATUAL - 0.10, 0)

# Cálculo correto da poupança
if SELIC_ATUAL > 8.5:
    POUPANCA_ATUAL = ((1 + 0.005 + 0.0015)**12 - 1) * 100 
else:
    POUPANCA_ATUAL = SELIC_ATUAL * 0.70

# STATUS COM DIAGNÓSTICO MELHORADO
STATUS_BCB = "ONLINE ✓" if MACRO_DATA['status'] else "OFFLINE ✗"
total_ativos_live = len(LIVE_RETURNS)

if total_ativos_live > 0:
    STATUS_MERCADO = f"ONLINE ✓ ({total_ativos_live} ativos)"
    COR_STATUS_MERCADO = "status-live"
else:
    STATUS_MERCADO = "OFFLINE ✗ (0 ativos)"
    COR_STATUS_MERCADO = "status-static"
    
logger.info(f"Status BCB: {STATUS_BCB}")
logger.info(f"Status Mercado: {STATUS_MERCADO}")

# --- LÓGICA DE SUAVIZAÇÃO (ALGORITMO HÍBRIDO) ---
def suavizar_retorno(nome_ativo, base_historica):
    """Combina dados históricos com dados live quando disponíveis"""
    if nome_ativo in LIVE_RETURNS:
        retorno_live = LIVE_RETURNS[nome_ativo]
        return (retorno_live * 0.5) + (base_historica * 0.5)
    return base_historica

# --- 3.3 CONSTRUÇÃO DA BASE DE ATIVOS ---
ATIVOS = {
    # RENDA FIXA
    'Tesouro Selic': {
        'retorno': SELIC_ATUAL, 'risco': 1, 'taxa': 1.65, 
        'tipo': 'RF', 'mercado': '🏦 Soberano', 'cor': '#4CAF50', 
        'desc': f'Porto seguro do brasileiro. {SELIC_ATUAL:.2f}% a.a.'
    },
    'CDB Liquidez Diária': {
        'retorno': CDI_ATUAL * 0.99, 'risco': 1, 'taxa': 1.60, 
        'tipo': 'RF', 'mercado': '🏦 Bancário', 'cor': '#03A9F4', 
        'desc': 'Reserva de emergência padrão.'
    },
    'Tesouro Prefixado': {
        'retorno': SELIC_ATUAL + 2.0, 'risco': 4, 'taxa': 1.70, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#CDDC39', 
        'desc': 'Aposta na queda dos juros.'
    },
    'Tesouro IPCA+ (Curto)': {
        'retorno': IPCA_ATUAL + 6.0, 'risco': 2, 'taxa': 1.60, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FFEB3B', 
        'desc': 'Proteção inflacionária de curto prazo.'
    },
    'Tesouro IPCA+ (Longo)': {
        'retorno': IPCA_ATUAL + 6.4, 'risco': 5, 'taxa': 1.65, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF9800', 
        'desc': 'Aposentadoria clássica.'
    },
    'Tesouro Renda+': {
        'retorno': IPCA_ATUAL + 6.5, 'risco': 3, 'taxa': 0.50, 
        'tipo': 'RF', 'mercado': '🏛️ Títulos Públicos', 'cor': '#FF5722', 
        'desc': 'Foco previdenciário.'
    },
    'LCI/LCA (Isento)': {
        'retorno': CDI_ATUAL * 0.94, 'risco': 2, 'taxa': 0.00, 
        'tipo': 'RF', 'mercado': '💳 Crédito Isento', 'cor': '#0288D1', 
        'desc': 'Queridinho da Classe Média (Isento IR).'
    },
    'CDB Banco Médio': {
        'retorno': CDI_ATUAL * 1.20, 'risco': 3, 'taxa': 1.90, 
        'tipo': 'RF', 'mercado': '💳 Crédito Privado', 'cor': '#01579B', 
        'desc': 'Caça ao rendimento (120% CDI).'
    },
    'Debêntures Incent.': {
        'retorno': IPCA_ATUAL + 7.5, 'risco': 5, 'taxa': 0.30, 
        'tipo': 'RF', 'mercado': '🏗️ Infraestrutura', 'cor': '#E91E63', 
        'desc': 'Crédito Privado Isento (Risco Corp).'
    },
    'CRI/CRA (High Yield)': {
        'retorno': IPCA_ATUAL + 9.5, 'risco': 8, 'taxa': 2.00, 
        'tipo': 'RF', 'mercado': '🏗️ Crédito High Yield', 'cor': '#C2185B', 
        'desc': 'Risco alto, retorno alto (Agro/Imob).'
    },
    'Fundo Multimercado': {
        'retorno': CDI_ATUAL * 1.15, 'risco': 5, 'taxa': 3.50, 
        'tipo': 'RF', 'mercado': '📊 Hedge Funds', 'cor': '#9C27B0', 
        'desc': 'Gestores macro (Volátil recentemente).'
    },
    
    # RENDA VARIÁVEL
    'Ações (Dividendos)': {
        'retorno': suavizar_retorno('Ações (Dividendos)', 14.50), 
        'risco': 6, 'taxa': 0.10, 
        'tipo': 'RV', 'mercado': '🏢 Bolsa BR', 'cor': '#00BCD4', 
        'desc': 'Vacas Leiteiras (BB, Taesa, Vale).'
    },
    'Ações (Small Caps)': {
        'retorno': 18.00, 'risco': 9, 'taxa': 2.50, 
        'tipo': 'RV', 'mercado': '🏢 Bolsa BR', 'cor': '#0097A7', 
        'desc': 'Pimentinhas com alto potencial.'
    },
    'ETF Ibovespa (BOVA11)': {
        'retorno': suavizar_retorno('ETF Ibovespa (BOVA11)', 14.00), 
        'risco': 7, 'taxa': 2.10, 
        'tipo': 'RV', 'mercado': '🏢 Bolsa BR', 'cor': '#006064', 
        'desc': 'Média do mercado brasileiro.'
    },
    'FIIs (Tijolo)': {
        'retorno': 12.50, 'risco': 4, 'taxa': 0.00, 
        'tipo': 'RV', 'mercado': '🧱 Imobiliário', 'cor': '#BA68C8', 
        'desc': 'Aluguel mensal isento (Shoppings/Galpões).'
    },
    'FIIs (Papel)': {
        'retorno': CDI_ATUAL * 1.05, 'risco': 5, 'taxa': 0.20, 
        'tipo': 'RV', 'mercado': '📜 Imobiliário', 'cor': '#8E24AA', 
        'desc': 'Juros compostos mensais (Indexados).'
    },
    'Fiagro (Agronegócio)': {
        'retorno': CDI_ATUAL * 1.10, 'risco': 6, 'taxa': 0.50, 
        'tipo': 'RV', 'mercado': '🚜 Agro', 'cor': '#4A148C', 
        'desc': 'Crédito do Agronegócio na Bolsa.'
    },
    'Ações EUA (S&P500)': {
        'retorno': suavizar_retorno('Ações EUA (S&P500)', 16.00), 
        'risco': 6, 'taxa': 2.75, 
        'tipo': 'RV', 'mercado': '🌎 Exterior', 'cor': '#3F51B5', 
        'desc': 'Dolarização via B3 (IVVB11).'
    },
    'Tech Stocks (Nasdaq)': {
        'retorno': suavizar_retorno('Tech Stocks (Nasdaq)', 18.00), 
        'risco': 8, 'taxa': 2.80, 
        'tipo': 'RV', 'mercado': '🌎 Exterior', 'cor': '#304FFE', 
        'desc': 'Tecnologia Global.'
    },
    'REITs (Imóveis EUA)': {
        'retorno': 15.00, 'risco': 6, 'taxa': 3.30, 
        'tipo': 'RV', 'mercado': '🌎 Exterior', 'cor': '#1A237E', 
        'desc': 'Imóveis em Dólar.'
    },
    'Ouro / Dólar': {
        'retorno': suavizar_retorno('Ouro / Dólar', 8.50), 
        'risco': 4, 'taxa': 1.00, 
        'tipo': 'RV', 'mercado': '🛡️ Proteção', 'cor': '#FFD700', 
        'desc': 'Hedge cambial clássico.'
    },
    'Bitcoin (BTC)': {
        'retorno': suavizar_retorno('Bitcoin (BTC)', 30.00), 
        'risco': 9, 'taxa': 4.50, 
        'tipo': 'RV', 'mercado': '⚡ Cripto', 'cor': '#F44336', 
        'desc': 'Ouro Digital.'
    },
    'Ethereum/Altcoins': {
        'retorno': suavizar_retorno('Ethereum/Altcoins', 35.00), 
        'risco': 10, 'taxa': 5.00, 
        'tipo': 'RV', 'mercado': '⚡ Cripto', 'cor': '#B71C1C', 
        'desc': 'Alto risco/recompensa.'
    }
}

# ==============================================================================
# 4. PERFIS E ESTRATÉGIAS
# ==============================================================================
PERFIS = {
    'Conservador (Rentista) 🛡️': {
        'LCI/LCA (Isento)': 35, 
        'Tesouro Selic': 30, 
        'CDB Banco Médio': 20,
        'Debêntures Incent.': 15 
    },
    'Moderado (Dividendeiro) ⚖️': {
        'FIIs (Tijolo)': 20, 
        'FIIs (Papel)': 15,
        'Debêntures Incent.': 20, 
        'Tesouro IPCA+ (Longo)': 15, 
        'Ações (Dividendos)': 15,
        'Fundo Multimercado': 15
    },
    'Agressivo (Arrojado BR) 🚀': {
        'Ações (Small Caps)': 20, 
        'Bitcoin (BTC)': 20,
        'FIIs (Tijolo)': 15, 
        'CRI/CRA (High Yield)': 20,
        'ETF Ibovespa (BOVA11)': 15,
        'Ações EUA (S&P500)': 10
    }
}

DESCRICOES_PERFIS = {
    'Conservador (Rentista) 🛡️': 'O clássico brasileiro pós-crises. Foco total em GANHO REAL acima da inflação com zero sustos. Muita LCI/LCA (Isenção) e Tesouro. Foge da Bolsa.',
    'Moderado (Dividendeiro) ⚖️': 'Perfil "Viver de Renda". Forte exposição a Fundos Imobiliários (FIIs) e Ações de Dividendos. Gosta de ver o dinheiro cair na conta todo mês.',
    'Agressivo (Arrojado BR) 🚀': 'Apetite ao risco tropical. Mistura Small Caps, High Yield (CRI/CRA) e uma dose de Cripto bem maior que a média global. Pouca exposição internacional (Home Bias).'
}

TESES = {
    '👑 Rei dos Dividendos (Barsi)': {
        'desc': 'Foco em renda passiva recorrente e isenta.', 
        'pesos': {
            'Ações (Dividendos)': 40, 
            'FIIs (Tijolo)': 25, 
            'FIIs (Papel)': 15, 
            'Debêntures Incent.': 20
        }
    },
    '🌍 All Weather (Ray Dalio)': {
        'desc': 'Blindada para qualquer cenário.', 
        'pesos': {
            'Ações EUA (S&P500)': 30, 
            'Tesouro IPCA+ (Longo)': 40, 
            'Tesouro Selic': 15, 
            'Ouro / Dólar': 7.5, 
            'CDB Liquidez Diária': 7.5
        }
    },
    '🚜 Agro é Pop (Fiagro)': {
        'desc': 'Foco no motor do PIB brasileiro.', 
        'pesos': {
            'Fiagro (Agronegócio)': 40, 
            'LCI/LCA (Isento)': 30, 
            'CRI/CRA (High Yield)': 30
        }
    },
    '🎓 Yale Model (David Swensen)': {
        'desc': 'Diversificação global.', 
        'pesos': {
            'Ações EUA (S&P500)': 30, 
            'Ações (Dividendos)': 15, 
            'FIIs (Tijolo)': 20, 
            'Tesouro IPCA+ (Curto)': 15, 
            'Tesouro IPCA+ (Longo)': 20
        }
    },
    '💰 Aposentadoria Renda+': {
        'desc': 'Acumulação longo prazo.', 
        'pesos': {
            'Tesouro Renda+': 40, 
            'FIIs (Tijolo)': 20, 
            'Ações (Dividendos)': 20, 
            'Tesouro IPCA+ (Longo)': 20
        }
    },
    '🔥 Pimenta Crypto': {
        'desc': 'Alto risco digitais.', 
        'pesos': {
            'Bitcoin (BTC)': 40, 
            'Ethereum/Altcoins': 20, 
            'Tech Stocks (Nasdaq)': 20, 
            'CDB Banco Médio': 20
        }
    }
}

# ==============================================================================
# 5. MOTOR MATEMÁTICO
# ==============================================================================
def calcular(pesos_dict, v_inicial, v_mensal, anos, renda_desejada=0, 
             anos_inicio_retirada=99, usar_retirada=False):
    """
    Calcula a evolução patrimonial considerando aportes e possíveis retiradas
    """
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
        # Modo poupança quando carteira está vazia
        usar_poupanca = True
        total = 1
        retorno_bruto_ponderado = taxa_poupanca
        custo_ponderado = 0
        risco_pond = 0.5
        ativos_usados = [{
            'nome': 'Dinheiro Parado (Poupança)', 
            'peso': 100, 
            'cor': '#757575', 
            'desc': 'DINHEIRO PARADO! Perdendo valor para inflação.', 
            'mercado': '⚠️ Alerta', 
            'retorno_real': taxa_poupanca, 
            'tipo': 'RF'
        }]
    else:
        # Cálculo da carteira real
        for nome, peso in pesos_dict.items():
            if peso > 0:
                info = ATIVOS[nome]
                peso_real = peso / total
                retorno_bruto_ponderado += info['retorno'] * peso_real
                custo_ponderado += info['taxa'] * peso_real
                risco_pond += info['risco'] * peso_real
                ativos_usados.append({
                    'nome': nome, 
                    'peso': peso_real * 100, 
                    'cor': info['cor'], 
                    'desc': info['desc'], 
                    'mercado': info['mercado'], 
                    'retorno_real': info['retorno'], 
                    'tipo': info['tipo']
                })
    
    retorno_liquido_aa = retorno_bruto_ponderado - custo_ponderado
    
    meses = anos * 12
    mes_inicio_retirada = anos_inicio_retirada * 12
    
    # Taxas mensais
    tx_cart_bruto = (1 + retorno_bruto_ponderado/100)**(1/12) - 1 
    tx_cart = (1 + retorno_liquido_aa/100)**(1/12) - 1            
    tx_cdi = (1 + cdi_aa/100)**(1/12) - 1
    tx_poup = (1 + taxa_poupanca/100)**(1/12) - 1
    tx_inf = (1 + inflacao_aa/100)**(1/12) - 1
    
    # Inicialização das listas
    y_cart_nom = [v_inicial]
    y_cart_real = [v_inicial]
    y_cart_bruto = [v_inicial]
    y_cdi_nom = [v_inicial]
    y_cdi_real = [v_inicial]
    y_poup_nom = [v_inicial]
    y_poup_real = [v_inicial]
    
    investido = v_inicial
    
    # Simulação mês a mês
    for m in range(meses):
        fluxo = v_mensal
        
        # Aplicar retiradas se configurado
        if usar_retirada and m >= mes_inicio_retirada:
            fluxo = v_mensal - renda_desejada
        
        # Evolução da carteira
        y_cart_nom.append(y_cart_nom[-1] * (1 + tx_cart) + fluxo)
        y_cart_bruto.append(y_cart_bruto[-1] * (1 + tx_cart_bruto) + fluxo) 
        
        fator_real_cart = (1 + tx_cart) / (1 + tx_inf)
        y_cart_real.append(y_cart_real[-1] * fator_real_cart + fluxo)
        
        # Evolução CDI
        y_cdi_nom.append(y_cdi_nom[-1] * (1 + tx_cdi) + fluxo)
        fator_real_cdi = (1 + tx_cdi) / (1 + tx_inf)
        y_cdi_real.append(y_cdi_real[-1] * fator_real_cdi + fluxo)
        
        # Evolução Poupança
        y_poup_nom.append(y_poup_nom[-1] * (1 + tx_poup) + fluxo)
        fator_real_poup = (1 + tx_poup) / (1 + tx_inf)
        y_poup_real.append(y_poup_real[-1] * fator_real_poup + fluxo)
        
        # Contabilizar apenas aportes (não retiradas)
        if not (usar_retirada and m >= mes_inicio_retirada):
            investido += v_mensal
    
    # Cálculo da renda passiva sustentável
    taxa_real_mensal = (1 + tx_cart) / (1 + tx_inf) - 1
    if taxa_real_mensal <= 0: 
        taxa_real_mensal = 0.0001
    
    renda_passiva_possivel = y_cart_real[-1] * taxa_real_mensal
    
    return {
        'x': np.arange(meses + 1),
        'y_cart_nom': y_cart_nom, 
        'y_cart_real': y_cart_real, 
        'y_cart_bruto': y_cart_bruto,
        'y_cdi_nom': y_cdi_nom, 
        'y_cdi_real': y_cdi_real,
        'y_poup_nom': y_poup_nom, 
        'y_poup_real': y_poup_real,
        'final_nom': y_cart_nom[-1], 
        'final_real': y_cart_real[-1], 
        'investido': investido, 
        'retorno_aa': retorno_liquido_aa, 
        'risco': risco_pond, 
        'ativos': ativos_usados, 
        'is_poup': usar_poupanca,
        'taxa_real_mensal': taxa_real_mensal, 
        'renda_passiva_possivel': renda_passiva_possivel
    }

# ==============================================================================
# 6. GERENCIAMENTO DE ESTADO
# ==============================================================================
# Inicializar sliders no session_state
for k in ATIVOS.keys():
    if f"sl_{k}" not in st.session_state: 
        st.session_state[f"sl_{k}"] = 0

def atualizar_reativo():
    """Atualiza os sliders baseado no modo selecionado"""
    mode_raw = st.session_state.get("modo_op")
    # Mapear de volta se necessário, mas aqui usaremos strings diretas
    pesos = {}
    
    if mode_raw == "🤖 AUTOMÁTICO":
        p = st.session_state.get("sel_perfil")
        if p: pesos = PERFIS[p]
    elif mode_raw == "🤝 ASSISTIDO":
        t = st.session_state.get("sel_tese")
        if t: pesos = TESES[t]['pesos']
    
    if mode_raw == "🛠️ MANUAL": 
        return

    # Atualizar todos os sliders
    for k in ATIVOS.keys():
        st.session_state[f"sl_{k}"] = pesos.get(k, 0)

# ==============================================================================
# 7. FUNÇÕES AUXILIARES
# ==============================================================================
def image_to_base64(img):
    """Converte imagem PIL para base64"""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def calc_percent(numer, denom):
    """Calcula percentual com proteção contra divisão por zero"""
    denom_safe = max(abs(denom), 0.01)
    if numer > 0 and denom <= 0: 
        return (numer / 0.01) * 100 
    return (numer / denom_safe) * 100

def fmt_pct(val): 
    """Formata percentual com separador brasileiro"""
    return f"{val:,.0f}".replace(",", ".")

def fmt_currency(val):
    """Formata valor monetário"""
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==============================================================================
# 8. INTERFACE DE USUÁRIO (UI)
# ==============================================================================

# --- LOGO ---
try:
    import os
    if os.path.exists('SIOEI LOGO.jpg'): 
        logo_image = Image.open('SIOEI LOGO.jpg')
        logo_ok = True
    else:
        url = "https://raw.githubusercontent.com/Open0Bit/SIOEI/main/SIOEI%20LOGO.jpg"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        logo_image = Image.open(BytesIO(response.content))
        logo_ok = True
except Exception as e:
    logger.warning(f"Erro ao carregar logo: {e}")
    logo_ok = False

if logo_ok:
    img_base64 = image_to_base64(logo_image)
    st.markdown(
        f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{img_base64}" width="130" alt="SIOEI Logo">
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="logo-container" style="font-size: 50px;">🇧🇷</div>', 
                unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- CONTROLES PRINCIPAIS (DESIGN ATUALIZADO) ---
st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2 style='font-weight: 800; letter-spacing: 1px; margin-bottom: 5px;'>
            🎛️ PAINEL DE CONTROLE
        </h2>
        <p style='color: #888; font-size: 14px;'>Selecione o nível de autonomia do sistema</p>
    </div>
""", unsafe_allow_html=True)

# --- BOTÕES DE MODO COM EMOJIS E UX MELHORADA ---
modo_options = ["🤖 AUTOMÁTICO", "🤝 ASSISTIDO", "🛠️ MANUAL"]
modo_raw = st.radio(
    "Modo de Operação:", 
    modo_options, 
    horizontal=True, 
    label_visibility="collapsed", 
    key="modo_op", 
    on_change=atualizar_reativo,
    index=2 
)

# Mapear de volta para a string simples para uso no código lógico
modo_map = {
    "🤖 AUTOMÁTICO": "Automático",
    "🤝 ASSISTIDO": "Assistido",
    "🛠️ MANUAL": "Manual"
}
modo = modo_map[modo_raw]

# --- LÓGICA DE FUNDO DINÂMICO (AMBIENT LIGHTING) ---
# Injeta CSS específico dependendo da escolha para pintar o fundo suavemente
bg_css = ""

if modo == "Automático":
    # Verde/Teal Futurista (Confiança, Crescimento)
    bg_css = """
    <style>
        .stApp {
            background: linear-gradient(180deg, #051a14 0%, #0E1117 40%, #0E1117 100%) !important;
        }
        /* Cor da borda e brilho do botão ativo */
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
            border-color: #00E676 !important;
            box-shadow: 0 0 15px rgba(0, 230, 118, 0.3) !important;
        }
    </style>
    """
elif modo == "Assistido":
    # Roxo/Indigo Deep (Sabedoria, Estratégia)
    bg_css = """
    <style>
        .stApp {
            background: linear-gradient(180deg, #120a2e 0%, #0E1117 40%, #0E1117 100%) !important;
        }
        /* Cor da borda e brilho do botão ativo */
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
            border-color: #7C4DFF !important;
            box-shadow: 0 0 15px rgba(124, 77, 255, 0.3) !important;
        }
    </style>
    """
else: # Manual
    # Laranja/Cinza Carvão (Construção, Controle, B3)
    bg_css = """
    <style>
        .stApp {
            background: linear-gradient(180deg, #1f1505 0%, #0E1117 40%, #0E1117 100%) !important;
        }
        /* Cor da borda e brilho do botão ativo */
        div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
            border-color: #FF9800 !important;
            box-shadow: 0 0 15px rgba(255, 152, 0, 0.3) !important;
        }
    </style>
    """
# Injetar o CSS do fundo dinâmico
st.markdown(bg_css, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SELEÇÃO DE PERFIL / ESTRATÉGIA (MOVIDA PARA CIMA) ---
if modo == "Automático":
    perfil_sel = st.selectbox(
        "Selecione seu Perfil (Realidade Brasil 🇧🇷):", 
        list(PERFIS.keys()), 
        key="sel_perfil", 
        on_change=atualizar_reativo
    )
    desc_texto = DESCRICOES_PERFIS.get(perfil_sel, "Perfil personalizado.")
    st.info(f"💡 **{perfil_sel}**: {desc_texto}")
    
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0: 
        atualizar_reativo()
        
elif modo == "Assistido":
    tese_sel = st.selectbox(
        "Selecione a Estratégia:", 
        list(TESES.keys()), 
        key="sel_tese", 
        on_change=atualizar_reativo
    )
    st.info(f"💡 {TESES[tese_sel]['desc']}")
    
    if sum([st.session_state[f"sl_{k}"] for k in ATIVOS]) == 0: 
        atualizar_reativo()
else:
    st.caption("💡 Modo Manual: Abra o 'Ajuste Fino' abaixo para configurar sua carteira.")

st.divider()

# --- INPUTS DE INVESTIMENTO ---
c1, c2, c3 = st.columns(3)
v_inicial = c1.number_input(
    "Aporte Inicial (R$)", 
    value=10000.0, 
    step=100.0, 
    min_value=0.0
)
v_mensal = c2.number_input(
    "Aporte Mensal (R$)", 
    value=0.0,  # Retornado para 0
    step=100.0, 
    min_value=0.0
)
anos = c3.slider("Prazo (Anos)", 1, 40, 10)

# --- AJUSTE FINO DA CARTEIRA ---
with st.expander("🎛️ AJUSTE FINO DA CARTEIRA (Clique para Abrir/Fechar)", expanded=False):
    t1, t2 = st.tabs(["🛡️ RENDA FIXA", "📈 RENDA VARIÁVEL"])
    
    def gerar_sliders_educativos(tipo_alvo, coluna_alvo):
        """Gera sliders agrupados por mercado"""
        mercados = sorted(list(set([
            v['mercado'] for k, v in ATIVOS.items() if v['tipo'] == tipo_alvo
        ])))
        
        for merc in mercados:
            with coluna_alvo.expander(merc, expanded=False):
                ativos_mercado = [k for k, v in ATIVOS.items() if v['mercado'] == merc]
                cols = st.columns(min(3, len(ativos_mercado)))
                
                for i, k in enumerate(ativos_mercado):
                    with cols[i % 3]: 
                        valor_atual = ATIVOS[k]['retorno']
                        is_live = k in LIVE_RETURNS
                        
                        # Emoji indicador de fonte
                        label_emoji = "🟢" if is_live else "🏦" if ATIVOS[k]['tipo'] == 'RF' else "🔧"
                        
                        st.slider(
                            f"{k} ({label_emoji} {valor_atual:.2f}%)", 
                            0, 100, 
                            key=f"sl_{k}",
                            help=ATIVOS[k]['desc']
                        )
                    
    with t1: 
        gerar_sliders_educativos('RF', st)
    with t2: 
        gerar_sliders_educativos('RV', st)

# Containers para organização
dashboard_container = st.container()
raiox_container = st.container()

# --- PLANEJAMENTO DE APOSENTADORIA ---
st.markdown("<br>", unsafe_allow_html=True)
with st.container(border=True): 
    st.markdown("### 🏖️ Planejamento de Aposentadoria (FIRE)")
    check_aposentadoria = st.checkbox("ATIVAR SIMULAÇÃO DE RENDA PASSIVA", value=False)
    
    renda_desejada = 0
    anos_retirada = 99
    
    if check_aposentadoria:
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            renda_desejada = st.number_input(
                "Renda Mensal Desejada (R$)", 
                value=100.0,  # Retornado para 100
                step=100.0, 
                min_value=0.0
            ) 
        with c_m2:
            anos_retirada = st.slider(
                "Começar a receber em (Anos):", 
                0, anos, 
                min(5, anos)
            )

# ==============================================================================
# 9. EXECUÇÃO E DASHBOARD
# ==============================================================================

pesos_atuais = {k: st.session_state[f"sl_{k}"] for k in ATIVOS.keys()}
d = calcular(
    pesos_atuais, 
    v_inicial, 
    v_mensal, 
    anos, 
    renda_desejada, 
    anos_retirada, 
    check_aposentadoria
)

with dashboard_container:
    # --- MÉTRICAS PRINCIPAIS ---
    k1, k2, k3, k4 = st.columns(4)

    COLORS = {
        "neutral": "#E0E0E0", 
        "success": "#00CC96", 
        "warning": "#FDD835",
        "danger": "#FF4B4B", 
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

    # Lógica de comparação com CDI
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

    # Lógica de comparação com Poupança
    if lucro_nominal < 0: 
        cor_poup_header = COLORS["danger"]
        txt_poup_header = "📉 Prejuízo"
    elif abs(lucro_nominal - lucro_poup) < 0.01: 
        cor_poup_header = COLORS["warning"]
        txt_poup_header = "⚠️ = Poupança"
    else: 
        cor_poup_header = COLORS["success"]
        pct_p = calc_percent(lucro_nominal, lucro_poup)
        txt_poup_header = f"📈 {fmt_pct(pct_p)}% da Poupança"

    sinal_nominal = "-" if lucro_nominal < 0 else "+"
    sinal_real = "-" if lucro_real < 0 else "+"
    
    # Classificação de risco
    c_risco = (COLORS["success"] if d['risco'] < 4 else 
               COLORS["warning"] if d['risco'] < 7 else 
               COLORS["danger"])
    l_risco = ("Baixo" if d['risco'] < 4 else 
               "Médio" if d['risco'] < 7 else 
               "Alto")

    # Cards de métricas
    k1.markdown(f"""
    <div class="metric-card">
        <div class="metric-label" style="color:{COLORS['neutral']}">TOTAL INVESTIDO</div>
        <div class="metric-main">{fmt_currency(d['investido'])}</div>
        <div class="metric-detail"> </div>
    </div>""", unsafe_allow_html=True)
    
    k2.markdown(f"""
    <div class="metric-card" style="border-bottom: 3px solid {cor_geral_card};">
        <div class="metric-label" style="color:{cor_geral_card}">SALDO BRUTO (NOMINAL)</div>
        <div class="metric-main" style="color:white;">{fmt_currency(d['final_nom'])}</div>
        <div class="metric-detail">Líquido Real (Ajustado): <span style="color:{cor_geral_card};">{fmt_currency(d['final_real'])}</span></div>
    </div>""", unsafe_allow_html=True)
    
    k3.markdown(f"""
    <div class="metric-card" style="border-bottom: 3px solid {cor_geral_card};">
        <div class="metric-label" style="color:{cor_geral_card}">LUCRO BRUTO (NOMINAL)</div>
        <div class="metric-main" style="color:white;">{sinal_nominal} {fmt_currency(abs(lucro_nominal))}</div>
        <div class="metric-detail">Líquido Real (Ajustado): <span style="color:{cor_geral_card}">{sinal_real} {fmt_currency(abs(lucro_real))}</span></div>
    </div>""", unsafe_allow_html=True)
    
    k4.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">RISCO ({l_risco})</div>
        <div class="metric-main" style="color:{c_risco}">{d['risco']:.1f}/10</div>
        <div class="metric-detail">Retorno: {d['retorno_aa']:.2f}% a.a.</div>
    </div>""", unsafe_allow_html=True)

    # Alerta para modo poupança
    if d['is_poup']:
        st.warning("⚠️ **MODO POUPANÇA ATIVO** (Carteira vazia). Adicione ativos ou escolha uma estratégia para otimizar seus investimentos.")

    # Cabeçalho de comparação
    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 10px; background-color: #262730; padding: 12px; border-radius: 5px; border: 1px solid #444; width: 100%;">
        <div style="font-size: 16px; font-weight: bold; color: #E0E0E0; margin-right: 10px;">📊 Raio-X: Nominal vs Real ({anos} Anos)</div>
        <div style="font-size: 13px; font-family: sans-serif; font-weight: bold; white-space: nowrap;">
            <span style="color: {cor_cdi_header}; margin-right: 15px;">{txt_cdi_header}</span>
            <span style="color: {cor_poup_header};">{txt_poup_header}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- GRÁFICOS ---
    g1, g2 = st.columns([3, 1.2])

    with g1:
        fig, ax = plt.subplots(figsize=(10, 4))
        COR_CART = cor_geral_card
        COR_CDI = '#FF9800'
        COR_POUP = '#FF5722'
        COR_BRUTO = '#29B6F6'

        # Plotar carteira
        if not d['is_poup']:
            ax.plot(d['x'], d['y_cart_bruto'], color=COR_BRUTO, linewidth=1, 
                   linestyle='--', label='Bruto (Sem taxas)', alpha=0.8)
            ax.plot(d['x'], d['y_cart_nom'], color=COR_CART, linewidth=2, 
                   label='Carteira (Líquida)')
            ax.plot(d['x'], d['y_cart_real'], color=COR_CART, linewidth=1, 
                   linestyle=':', alpha=0.5, label='_nolegend_')
            
            ax.fill_between(d['x'], d['y_cart_nom'], d['y_cart_bruto'], 
                          color=COR_BRUTO, alpha=0.10, label='Impacto Tributário')
            ax.fill_between(d['x'], d['y_cart_nom'], d['y_cart_real'], 
                          color=COR_CART, alpha=0.15, label='Perda Inflação')
        
        # Plotar CDI
        ax.plot(d['x'], d['y_cdi_nom'], color=COR_CDI, linewidth=1.5, 
               linestyle='--', alpha=0.7, label='CDI (Nominal)')
        ax.plot(d['x'], d['y_cdi_real'], color=COR_CDI, linewidth=0.5, 
               linestyle=':', alpha=0.3, label='_nolegend_')
        ax.fill_between(d['x'], d['y_cdi_nom'], d['y_cdi_real'], 
                       color=COR_CDI, alpha=0.08)
        
        # Plotar Poupança
        style_poup = '-' if d['is_poup'] else ':'
        alpha_line = 0.9 if d['is_poup'] else 0.5
        ax.plot(d['x'], d['y_poup_nom'], color=COR_POUP, linewidth=1.5, 
               linestyle=style_poup, alpha=alpha_line, label='Poupança (Nominal)')
        ax.plot(d['x'], d['y_poup_real'], color=COR_POUP, linewidth=0.5, 
               linestyle=':', alpha=0.3, label='_nolegend_')
        ax.fill_between(d['x'], d['y_poup_nom'], d['y_poup_real'], 
                       color=COR_POUP, alpha=0.08)
        
        ax.legend(loc='upper left', frameon=False, ncol=2, fontsize='x-small')
        ax.grid(True, alpha=0.1)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#444')
        ax.spines['left'].set_color('#444')
        ax.tick_params(colors='#aaa')
        ax.set_xlabel('Meses', color='#aaa', fontsize=9)
        ax.set_ylabel('Patrimônio (R$)', color='#aaa', fontsize=9)
        
        st.pyplot(fig)
        plt.close(fig)

    with g2:
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        vals = [i['peso'] for i in d['ativos']]
        labs = [f"{i['nome']}\n{i['peso']:.0f}%" for i in d['ativos']]
        colors = [i['cor'] for i in d['ativos']]
        
        if not vals: 
            vals = [1]
            labs = ["Vazio"]
            colors = ["#333"]
            
        ax2.pie(vals, labels=labs, colors=colors, startangle=90, 
               textprops={'color': "white", 'fontsize': 7}, 
               wedgeprops=dict(width=0.45, edgecolor='#222'))
        ax2.set_title("Alocação", color='white', fontsize=10)
        
        st.pyplot(fig2)
        plt.close(fig2)

# --- RAIO-X DA ESTRATÉGIA ---
with raiox_container:
    st.markdown("### 🧠 Raio-X da Estratégia (Live Check)")
    
    for item in d['ativos']:
        is_live = item['nome'] in LIVE_RETURNS
        is_bcb = item['tipo'] == 'RF' and MACRO_DATA['status']
        
        # Lógica de Tag Inteligente
        if is_live: 
            tag = "<span style='color:#BB86FC; font-size:10px; border:1px solid #BB86FC; padding:1px 4px; border-radius:3px;'>HÍBRIDO (50/50)</span>"
        elif is_bcb: 
            tag = "<span style='color:#29B6F6; font-size:10px; border:1px solid #29B6F6; padding:1px 4px; border-radius:3px;'>BCB OFICIAL</span>"
        else: 
            tag = "<span style='color:#757575; font-size:10px; border:1px solid #757575; padding:1px 4px; border-radius:3px;'>ESTIMADO</span>"
        
        c1, c2 = st.columns([1.2, 3.8])
        c1.markdown(
            f"<span style='color:{item['cor']}; font-weight:bold;'>● {item['nome']}</span><br>{tag}", 
            unsafe_allow_html=True
        )
        c2.caption(
            f"**{item['mercado']}** • Retorno Base: **{item['retorno_real']:.2f}%** a.a. • {item['desc']}"
        )
        st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", 
                   unsafe_allow_html=True)

# --- ANÁLISE DE VIABILIDADE DE APOSENTADORIA ---
if check_aposentadoria:
    st.markdown("### 🏖️ Análise de Viabilidade (Resultados)")
    
    if d['taxa_real_mensal'] > 0 and renda_desejada > 0: 
        patrimonio_necessario = renda_desejada / d['taxa_real_mensal']
    else: 
        patrimonio_necessario = 0
        
    saldo_final_real = d['final_real']
    atingiu = saldo_final_real >= patrimonio_necessario and patrimonio_necessario > 0
    prog = (min(1.0, max(0.0, saldo_final_real / patrimonio_necessario)) 
            if patrimonio_necessario > 0 else 0.0)
        
    if atingiu:
        st.success("🚀 **META ATINGIDA!** Sua carteira suporta a retirada e ainda cresce.")
        st.progress(prog, text=f"Sustentabilidade: {prog*100:.1f}%")
    else:
        if saldo_final_real < d['investido']: 
            st.error("📉 **ALERTA CRÍTICO:** As retiradas estão consumindo seu patrimônio principal.")
        else: 
            st.warning("⚠️ **Atenção:** Você tem saldo, mas não o suficiente para viver apenas de renda passiva perpétua.")
        
        st.progress(prog, text=f"Cobertura da Meta de Independência: {prog*100:.1f}%")
        st.caption(
            f"Para uma renda perpétua de {fmt_currency(renda_desejada)}, "
            f"você precisaria de {fmt_currency(patrimonio_necessario)} acumulados."
        )

# ==============================================================================
# 10. MONITORES DE CONEXÃO (RODAPÉ)
# ==============================================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

with st.expander("🔍 MONITORES DE CONEXÃO E DIAGNÓSTICO", expanded=False):
    # Status visual resumido
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        cor_bcb = "status-live" if MACRO_DATA['status'] else "status-static"
        st.markdown(f"""
            <div style="text-align: center;">
                <span class="status-badge {cor_bcb}" style="font-size: 14px; padding: 8px 16px;">
                    🏛️ BCB: {MACRO_DATA['selic']:.2f}% (Selic)
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    with col_status2:
        st.markdown(f"""
            <div style="text-align: center;">
                <span class="status-badge {cor_bcb}" style="font-size: 14px; padding: 8px 16px;">
                    📈 IPCA: {MACRO_DATA['ipca']:.2f}%
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    with col_status3:
        st.markdown(f"""
            <div style="text-align: center;">
                <span class="status-badge {COR_STATUS_MERCADO}" style="font-size: 14px; padding: 8px 16px;">
                    🌍 {STATUS_MERCADO}
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Diagnóstico detalhado
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📡 Diagnóstico Banco Central:**")
        if MACRO_DATA['status']:
            st.success(f"✅ Conectado com sucesso")
            st.caption(f"Selic Meta: {SELIC_ATUAL:.2f}% a.a.")
            st.caption(f"IPCA (12 meses): {IPCA_ATUAL:.2f}%")
            st.caption(f"CDI Estimado: {CDI_ATUAL:.2f}% a.a.")
        else:
            st.error("❌ Falha na conexão com API do BCB")
            st.caption("Usando valores padrão de fallback")
            st.caption(f"Selic Padrão: {SELIC_ATUAL:.2f}%")
            st.caption(f"IPCA Padrão: {IPCA_ATUAL:.2f}%")
    
    with col2:
        st.markdown("**📊 Diagnóstico Yahoo Finance:**")
        if total_ativos_live > 0:
            st.success(f"✅ Conectado - {total_ativos_live} ativos atualizados")
            st.caption("**Ativos com dados live:**")
            for nome, retorno in list(LIVE_RETURNS.items())[:5]:
                emoji = "🟢" if retorno > 0 else "🔴"
                st.caption(f"{emoji} {nome}: {retorno:+.2f}%")
            if len(LIVE_RETURNS) > 5:
                st.caption(f"... e mais {len(LIVE_RETURNS)-5} ativos")
        else:
            st.warning("⚠️ Nenhum ativo obtido do mercado")
            st.caption("**Possíveis causas:**")
            st.caption("• Mercado fechado (B3: 10h-17h)")
            st.caption("• Problemas temporários na API")
            st.caption("• Cache expirado (TTL: 12h)")
            st.caption("• Rate limiting do Yahoo Finance")
            
            # Botão para forçar atualização
            if st.button("🔄 Forçar Atualização dos Dados", key="force_refresh"):
                st.cache_data.clear()
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Nota:** Os dados do BCB são atualizados diariamente. Os dados de mercado são atualizados a cada 12 horas durante o horário de funcionamento da B3.")

# ==============================================================================
# 11. RODAPÉ
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
    <p style='margin-top: 10px; font-size: 11px; color: #666;'>
        v4.0 (Depurado) | 
        <a href='https://github.com/Open0Bit/SIOEI' target='_blank' style='color: #00E676; text-decoration: none;'>GitHub</a>
    </p>
</div>
""", unsafe_allow_html=True)