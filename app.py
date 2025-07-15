# === IMPORTAÇÕES NECESSÁRIAS ===
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import timedelta

# === CONFIGURAÇÃO DE LOGIN ===
users = {
    "admin": "senha123",
    "marcelo": "condominiojosef"
}

st.set_page_config(page_title="Dashboard - Condomínio Josef", layout="wide", page_icon="🏗️")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Acesso Restrito")
    username = st.text_input("Usuário", placeholder="Digite seu usuário")
    password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
    if st.button("Entrar"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.success(f"✅ Bem-vindo, {username}!")
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# === FUNÇÕES AUXILIARES ===
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
    df_fases['Duração (dias)'] = [20, 20, 15, 15, 10]
    df_fases['Início'] = pd.date_range(start=data_inicio, periods=len(df_fases), freq='B')
    df_fases['Término'] = df_fases['Início'] + pd.to_timedelta(df_fases['Duração (dias)'], unit='D')
    fig = px.timeline(df_fases, x_start="Início", x_end="Término", y="Fase da Obra", color="Fase da Obra")
    fig.update_layout(title="🗓️ Cronograma da Obra", xaxis_title="Data", yaxis_title="Fase")
    return fig

def exportar_excel(df1, df2):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, index=False, sheet_name="Resumo Casas")
        df2.to_excel(writer, index=False, sheet_name="Fases da Obra")
    return output.getvalue()

def exportar_simulacoes(df_sim):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_sim.to_excel(writer, index=False, sheet_name="Simulações")
    return output.getvalue()

# === INTERFACE PRINCIPAL ===
st.title("📊 Dashboard do Orçamento - Condomínio Josef")

file = st.file_uploader("📁 Envie uma planilha (.xlsx) com os dados das casas", type=["xlsx"])
if file:
    df_casas = pd.read_excel(file)
else:
    df_casas = pd.DataFrame([
        {'Casa': f'Casa {i+1}', 'Área (m²)': area, 'Preço Unitário': 836.47}
        for i, area in enumerate([140.42, 140.39, 134.12, 141.43, 141.30, 139.13])
    ])

df_casas['Custo Total'] = df_casas['Área (m²)'] * df_casas['Preço Unitário']
df_casas['Custo MDO + BDI'] = df_casas['Custo Total'] * 1.025
df_casas['Custo Final'] = df_casas['Custo MDO + BDI'] * 1.013
df_casas['Eficiência'] = 1000 / df_casas['Custo Final']
df_casas['Melhor Custo-Benefício'] = df_casas['Eficiência'] == df_casas['Eficiência'].max()

# === ANÁLISE INDIVIDUAL ===
casa_selecionada = st.selectbox("🏠 Selecione uma casa", df_casas['Casa'])
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

st.subheader("🗓️ Cronograma da Obra")
fig = gerar_cronograma(df_fases)
st.plotly_chart(fig)

# === EXPORTAÇÃO PRINCIPAL ===
st.subheader("📥 Exportar Orçamento Original")
excel_principal = exportar_excel(df_casas, df_fases)
st.download_button("Baixar Excel", data=excel_principal, file_name="orcamento_principal.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === SIMULAÇÕES DE NOVOS ORÇAMENTOS ===
st.header("🧮 Criar Novo Orçamento Baseado no Original")

if "simulacoes" not in st.session_state:
    st.session_state.simulacoes = []

with st.form("simulador"):
    nome = st.text_input("Nome do orçamento", value=f"Simulação {len(st.session_state.simulacoes)+1}")
    area = st.number_input("Área (m²)", value=140.00)
    preco = st.number_input("Preço Unitário (R$/m²)", value=836.47)
    bdi_mdo = st.number_input("BDI Mão de Obra (%)", value=2.5)
    bdi_mat = st.number_input("BDI Materiais (%)", value=1.3)
    gerar = st.form_submit_button("Gerar Orçamento")

if gerar:
    custo = area * preco
    custo_mdo = custo * (1 + bdi_mdo / 100)
    custo_final = custo_mdo * (1 + bdi_mat / 100)
    eficiencia = 1000 / custo_final
    nova_sim = {
        "Nome": nome,
        "Área (m²)": area,
        "Preço Unitário": preco,
        "Custo Final": custo_final,
        "Eficiência": eficiencia,
        "BDI MDO (%)": bdi_mdo,
        "BDI MAT (%)": bdi_mat
    }
    st.session_state.simulacoes.append(nova_sim)
    st.success(f"✅ Simulação criada: R$ {custo_final:,.2f}")

# === HISTÓRICO DE SIMULAÇÕES ===
if st.session_state.simulacoes:
    st.subheader("📚 Orçamentos Simulados")
    df_sim = pd.DataFrame(st.session_state.simulacoes)
    st.dataframe(df_sim)

    st.subheader("📊 Comparativo Visual")
    df_comp = pd.DataFrame(
        [{"Nome": row["Casa"], "Custo Final": row["Custo Final"]} for _, row in df_casas.iterrows()] +
        [{"Nome": sim["Nome"], "Custo Final": sim["Custo Final"]} for sim in st.session_state.simulacoes]
    )
    fig_comp = px.bar(df_comp, x="Nome", y="Custo Final", text="Custo Final", title="Comparativo entre Orçamentos")
    fig_comp.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
    st.plotly_chart(fig_comp)

    st.subheader("📥 Exportar Simulações")
    excel_sim = exportar_simulacoes(df_sim)
    st.download_button("Baixar Simulações", data=excel_sim, file_name="orcamentos_simulados.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Opcional: botão para limpar simulações
    if st.button("🗑️ Limpar Simulações"):
        st.session
