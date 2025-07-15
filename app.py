# === IMPORTAÇÕES ===
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import pdfkit
from datetime import datetime

# === CONFIGURAÇÃO DO APP ===
st.set_page_config(page_title="Dashboard - Steel Facility", layout="wide", page_icon="🏗️")

# === LOGIN ===
users = {"admin": "senha123", "marcelo": "condominiojosef"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Acesso Restrito")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.success(f"Bem-vindo, {username}!")
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# === FUNÇÕES ===
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

def gerar_cronograma(df_fases, inicio='2025-07-15'):
    df_fases['Duração'] = [20, 20, 15, 15, 10]
    df_fases['Início'] = pd.date_range(start=inicio, periods=len(df_fases), freq='B')
    df_fases['Término'] = df_fases['Início'] + pd.to_timedelta(df_fases['Duração'], unit='D')
    fig = px.timeline(df_fases, x_start="Início", x_end="Término", y="Fase da Obra", color="Fase da Obra")
    fig.update_layout(title="Cronograma da Obra", xaxis_title="Data", yaxis_title="Etapa")
    return fig

def exportar_excel(df1, df2, nome="orcamento.xlsx"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, index=False, sheet_name="Resumo Casas")
        df2.to_excel(writer, index=False, sheet_name="Fases da Obra")
    return output.getvalue()

def gerar_proposta_em_pdf(simulacao, fases_df):
    hoje = datetime.today().strftime("%d/%m/%Y")
    fases_html = "".join([
        f"<tr><td>{row['Fase da Obra']}</td><td>R$ {row['Custo Estimado']:,.2f}</td></tr>"
        for _, row in fases_df.iterrows()
    ])

    html = f"""
    <html>
    <head>
    <style>
    body {{ font-family: Arial; padding: 40px; }}
    .logo {{ text-align: center; margin-bottom: 30px; }}
    .rodape {{ text-align: center; font-size: 12px; color: #555; margin-top: 50px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    </style>
    </head>
    <body>
    <div class="logo">
    <img src="logo_facility.png" width="120">
    </div>
    <h2>Proposta Comercial – {simulacao['Nome']}</h2>
    <p><strong>Data:</strong> {hoje}</p>
    <p><strong>Área:</strong> {simulacao['Área (m²)']} m²<br>
       <strong>Preço Unitário:</strong> R$ {simulacao['Preço Unitário']:,.2f}<br>
       <strong>BDI Mão de Obra:</strong> {simulacao['BDI MDO (%)']}%<br>
       <strong>BDI Materiais:</strong> {simulacao['BDI MAT (%)']}%<br>
       <strong>Custo Final:</strong> <strong>R$ {simulacao['Custo Final']:,.2f}</strong>
    </p>
    <h4>Fases da Obra</h4>
    <table>
    <tr><th>Fase</th><th>Custo Estimado</th></tr>
    {fases_html}
    </table>
    <h4>Condições Comerciais</h4>
    <p>Validade: 30 dias<br>
       Forma de pagamento: A combinar<br>
       Incluso: Projeto executivo + execução<br>
       Não incluso: Fundações específicas, taxas municipais
    </p>
    <div class="rodape">
    Steel Facility · Rua Ubá, 15 – Vila Virginia – Itaquaquecetuba · steelfacility@gmail.com · @steelfacilitybr<br>
    Assinatura: Marcelo Barbosa – CEO
    </div>
    </body>
    </html>
    """

    with open("proposta_temp.html", "w", encoding="utf-8") as f:
        f.write(html)

    pdfkit.from_file("proposta_temp.html", "proposta_gerada.pdf")
    return "proposta_gerada.pdf"

# === DADOS INICIAIS ===
st.title("Dashboard Steel Facility")

uploaded = st.file_uploader("📁 Upload da planilha de casas (.xlsx)", type=["xlsx"])
if uploaded:
    df_casas = pd.read_excel(uploaded)
else:
    df_casas = pd.DataFrame([
        {'Casa': f'Casa {i+1}', 'Área (m²)': area, 'Preço Unitário': 836.47}
        for i, area in enumerate([140.42, 140.39, 134.12, 141.43, 141.30, 139.13])
    ])

df_casas['Custo Total'] = df_casas['Área (m²)'] * df_casas['Preço Unitário']
df_casas['Custo MDO + BDI'] = df_casas['Custo Total'] * 1.025
df_casas['Custo Final'] = df_casas['Custo MDO + BDI'] * 1.013
df_casas['Eficiência'] = 1000 / df_casas['Custo Final']
df_casas['Melhor'] = df_casas['Eficiência'] == df_casas['Eficiência'].max()

casa = st.selectbox("Selecione uma casa", df_casas['Casa'])
df_sel = df_casas[df_casas['Casa'] == casa]

st.metric("Área (m²)", f"{df_sel['Área (m²)'].values[0]:.2f}")
st.metric("Custo Final", f"R$ {df_sel['Custo Final'].values[0]:,.2f}")
st.dataframe(df_casas)

fases_df = calcular_fases(df_sel['Custo Total'].values[0])
st.subheader("Fases da Obra")
st.dataframe(fases_df)

fig = gerar_cronograma(fases_df)
st.plotly_chart(fig)

# === EXPORTAÇÃO PRINCIPAL ===
excel_bytes = exportar_excel(df_casas, fases_df)
st.download_button("📥 Exportar Orçamento Original", data=excel_bytes, file_name="orcamento_steel.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === NOVO ORÇAMENTO ===
st.header("Criar Novo Orçamento")

if "simulacoes" not in st.session_state:
    st.session_state.simulacoes = []

with st.form("nova_simulacao"):
    nome = st.text_input("Nome", value=f"Simulação {len(st.session_state.simulacoes)+1}")
    area = st.number_input("Área (m²)", value=140.0)
    preco = st.number_input("Preço Unitário", value=836.47)
    bdi_mdo = st.number_input("BDI Mão de Obra (%)", value=2.5)
    bdi_mat = st.number_input("BDI Materiais (%)
                              # === FINALIZAÇÃO DA SIMULAÇÃO ===
    bdi_mat = st.number_input("BDI Materiais (%)", value=1.3)
    gerar_simulacao = st.form_submit_button("Gerar Orçamento")

if gerar_simulacao:
    custo_total = area * preco
    custo_mdo_bdi = custo_total * (1 + bdi_mdo / 100)
    custo_final = custo_mdo_bdi * (1 + bdi_mat / 100)
    eficiencia = 1000 / custo_final

    nova_simulacao = {
        "Nome": nome,
        "Área (m²)": area,
        "Preço Unitário": preco,
        "Custo Final": custo_final,
        "Eficiência": eficiencia,
        "BDI MDO (%)": bdi_mdo,
        "BDI MAT (%)": bdi_mat
    }
    st.session_state.simulacoes.append(nova_simulacao)
    st.success(f"✅ Simulação '{nome}' criada com sucesso! Custo Final: R$ {custo_final:,.2f}")

# === VISUALIZAÇÃO E EXPORTAÇÃO DAS SIMULAÇÕES ===
if st.session_state.simulacoes:
    st.subheader("📚 Simulações Criadas")
    df_simulacoes = pd.DataFrame(st.session_state.simulacoes)
    st.dataframe(df_simulacoes)

    # Comparativo com casas originais
    df_comparativo = pd.DataFrame(
        [{"Nome": row["Casa"], "Custo Final": row["Custo Final"]} for _, row in df_casas.iterrows()] +
        [{"Nome": sim["Nome"], "Custo Final": sim["Custo Final"]} for sim in st.session_state.simulacoes]
    )
    fig_comp = px.bar(df_comparativo, x="Nome", y="Custo Final", title="Comparativo de Orçamentos", text="Custo Final")
    fig_comp.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
    st.plotly_chart(fig_comp)

    # Exportar simulações
    excel_simulacoes = exportar_excel(df_simulacoes, pd.DataFrame(), nome="simulacoes_steel.xlsx")
    st.download_button("📥 Baixar Simulações em Excel", data=excel_simulacoes,
                       file_name="simulacoes_steel.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === GERADOR DE PROPOSTA EM PDF ===
st.header("📝 Gerar Proposta em PDF")

if st.session_state.simulacoes:
    selecionada = st.selectbox("Selecione uma simulação", [sim["Nome"] for sim in st.session_state.simulacoes])
    sim = next(sim for sim in st.session_state.simulacoes if sim["Nome"] == selecionada)
    fases_df = calcular_fases(sim["Área (m²)"] * sim["Preço Unitário"])

    caminho_pdf = gerar_proposta_em_pdf(sim, fases_df)
    with open(caminho_pdf, "rb") as f:
        st.download_button("📄 Baixar Proposta PDF", data=f.read(),
                           file_name=f"proposta_{selecionada.lower().replace(' ', '_')}.pdf",
                           mime="application/pdf")
else:
    st.info("Você ainda não criou nenhuma simulação.")
