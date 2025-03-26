import streamlit as st
import pandas as pd
import numpy as np

# ==============================
# 🔐 AUTENTICAÇÃO BÁSICA (CGX / x)
# ==============================
def autenticar_usuario():
    st.sidebar.title("🔐 Login - COGEX")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")

    usuarios_validos = {
        "CGX": "x"
    }

    if st.sidebar.button("Entrar"):
        if usuario in usuarios_validos and senha == usuarios_validos[usuario]:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.experimental_rerun()
        else:
            st.sidebar.error("Usuário ou senha incorretos.")

if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
    autenticar_usuario()
    st.stop()

# -------------------- CONFIGURAÇÕES INICIAIS --------------------
st.set_page_config(page_title="COGEX Almoxarifado", layout="wide")

st.title("📦 COGEX ALMOXARIFADO")
st.markdown("**Sistema Web - Controle Matemático de Estoque - Pedido Automatizado com Critérios Reais**")

# -------------------- CONFIGURAÇÕES --------------------
DICIONARIO_LOGICO = {
    'dias_cobertura': [7, 15, 30, 45],
    'critico_limite': 0,
    'alerta_limite': 1
}

# -------------------- CARREGAMENTO DE DADOS --------------------
@st.cache_data(show_spinner="Carregando dados do Google Sheets...")
def load_data():
    url_inventory = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSeWsxmLFzuWsa2oggpQb6p5SFapxXHcWaIl0Jjf2wAezvMgAV9XCc1r7fSSzRWTCgjk9eqREgWlrzp/pub?gid=1710164548&single=true&output=csv'
    url_items = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSeWsxmLFzuWsa2oggpQb6p5SFapxXHcWaIl0Jjf2wAezvMgAV9XCc1r7fSSzRWTCgjk9eqREgWlrzp/pub?gid=1011017078&single=true&output=csv'

    inventory = pd.read_csv(url_inventory)
    inventory['DateTime'] = pd.to_datetime(inventory['DateTime'], errors='coerce')
    inventory.dropna(subset=['Item ID', 'Amount'], inplace=True)

    items = pd.read_csv(url_items)
    items.dropna(subset=['Item ID', 'Name'], inplace=True)

    return items, inventory

items_df, inventory_df = load_data()

# -------------------- FUNÇÕES MATEMÁTICAS --------------------
def calcular_consumo_medio(inventory):
    consumo = inventory[inventory['Amount'] < 0].groupby('Item ID')['Amount'].sum().abs()
    dias = (inventory['DateTime'].max() - inventory['DateTime'].min()).days
    consumo_medio = consumo / dias
    return consumo_medio

def calcular_saldo_atual(inventory):
    saldo = inventory.groupby('Item ID')['Amount'].sum()
    return saldo

def gerar_pedido(dias_cobertura):
    consumo_medio = calcular_consumo_medio(inventory_df)
    saldo = calcular_saldo_atual(inventory_df)

    pedido_df = pd.merge(items_df[['Item ID', 'Name', 'Description']], saldo.reset_index(), on='Item ID', how='left')
    pedido_df = pd.merge(pedido_df, consumo_medio.reset_index(), on='Item ID', how='left', suffixes=('_Estoque', '_Consumo'))
    pedido_df = pedido_df.fillna({'Amount_Estoque': 0, 'Amount_Consumo': 0})

    pedido_df['Consumo Médio Diário'] = pedido_df['Amount_Consumo']
    pedido_df['Estoque Atual'] = pedido_df['Amount_Estoque']

    for dias in dias_cobertura:
        pedido_df[f'Necessidade {dias} dias'] = (pedido_df['Consumo Médio Diário'] * dias).round
