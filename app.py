# === IMPORTAÇÕES ===
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import timedelta

# === CONFIG LOGIN ===
users = {
    "admin": "senha123",
    "marcelo": "condominiojosef"
}

st.set_page_config(page_title="Dashboard Condomínio Josef", layout="wide", page_icon="🏗️")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Acesso Restrito ao Dashboard")
    username = st.text_input("Usuário", placeholder="Digite seu nome de usuário")
    password = st.text_input("Senha", type="password", placeholder="Digite sua senha")

    if st.button("Entrar"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.success(f"✅ Bem-vindo, {username}!")
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# === FUNÇÕES DE APOIO ===
def calcular_fases(custo_total):
    fases = {
        'Mobilização': 0.25,
        'Painéis': 0.25,
        'Cobertura': 0.20,
        'Chap. Externo': 0.20,
        'Chap. Interno / Forro': 0.10
    }
    return pd.DataFrame({
        'Fase da Obra': list(fases.keys()),
        'Proporção': list(fases.values()),
        'Custo Estimado': [round(custo_total * p, 2) for p in fases.values()]
    })

def gerar_cronograma(df_fases, data_inicio='2025-07-15'):
    df_fases['Duração'] = [20, 20, 15, 15, 10]
    df_fases['Início'] = pd.date_range(start=data_inicio, periods=len(df_fases), freq='B')
    df_fases['Término'] = df_fases['Início'] + pd.to_timedelta(df_fases['Duração'], unit='D')
    fig = px.timeline(
        df_fases, x_start="Início", x_end="Término",
        y="Fase da Obra", color="Fase da Obra"
    )
    fig.update_layout(title="Cronograma da Obra", xaxis_title="Datas")
    return fig

def gerar_excel(df_resumo, df_fases):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_resumo.to_excel(writer, index=False, sheet_name="Resumo Casas")
        df_fases.to_excel(writer, index=False, sheet_name="Fases da Obra")
    return output.getvalue()

# === INTERFACE PRINCIPAL ===
st.title("📊 Dashboard do Orçamento - Condomínio Josef")

file = st.file_uploader("📁 Envie uma planilha (.xlsx) com os dados das casas", type=["xlsx"])
if file:
    df_casas = pd.read_excel(file)
else:
    # Dados simulados caso não haja planilha
    df_casas = pd.DataFrame([
        {'Casa': f'Casa {i+1}', 'Área (m²)': area, 'Preço Unitário': 836.47}
        for i, area in enumerate([140.42, 140.39, 134.12, 141.43, 141.30, 139.13])
    ])

# === CÁLCULOS ===
df_casas['Custo Total'] = df_casas['Área (m²)'] * df_casas['Preço Unitário']
df_casas['Custo MDO + BDI'] = df_casas['Custo Total'] * 1.025
df_casas['Custo Final'] = df_casas['Custo MDO + BDI'] * 1.013
df_casas['Eficiência'] = 1000 / df_casas['Custo Final']
df_casas['Melhor Custo-Benefício'] = df_casas['Eficiência'] == df_casas['Eficiência'].max()

# === EXIBIÇÃO ===
casa_selecionada = st.selectbox("🏠 Selecione uma casa para análise", df_casas['Casa'])
df_selecionada = df_casas[df_casas['Casa'] == casa_selecionada]

col1, col2 = st.columns(2)
with col1:
    st.metric("Área (m²)", f"{df_selecionada['Área (m²)'].values[0]:.2f}")
    st.metric("Preço Unitário", f"R$ {df_selecionada['Preço Unitário'].values[0]:,.2f}")
with col2:
    st.metric("Custo Final", f"R$ {df_selecionada['Custo Final'].values[0]:,.2f}")
    st.metric("Eficiência", f"{df_selecionada['Eficiência'].values[0]:.2f}")

st.subheader("📋 Tabela Geral das Casas")
st.dataframe(df_casas)

# === FASES E CRONOGRAMA ===
df_fases = calcular_fases(df_selecionada['Custo Total'].values[0])
st.subheader("🔧 Simulação das Fases da Obra")
st.dataframe(df_fases)

st.subheader("🗓️ Cronograma Interativo")
fig_cronograma = gerar_cronograma(df_fases)
st.plotly_chart(fig_cronograma)

# === EXPORTAÇÃO ===
st.subheader("📥 Exportar Dados")
excel_bytes = gerar_excel(df_casas, df_fases)
st.download_button("Baixar Excel", data=excel_bytes, file_name="dashboard_condominio_josef.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")