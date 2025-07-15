import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import pdfkit
from datetime import datetime

st.set_page_config(page_title="Steel Facility", layout="wide", page_icon="🏗️")

# === LOGIN ===
users = {"admin": "senha123", "marcelo": "condominiojosef"}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if users.get(u) == p:
            st.session_state.logged_in = True
            st.success(f"Bem-vindo, {u}!")
        else:
            st.error("Credenciais inválidas.")
    st.stop()

# === FUNÇÕES ===
def calcular_fases(valor):
    etapas = {'Mobilização': 0.25, 'Painéis': 0.25, 'Cobertura': 0.2, 'Chap. Externo': 0.2, 'Chap. Interno': 0.1}
    return pd.DataFrame({
        'Fase da Obra': etapas.keys(),
        'Proporção': etapas.values(),
        'Custo Estimado': [valor * p for p in etapas.values()]
    })

def gerar_cronograma(fases, inicio="2025-07-15"):
    fases['Duração'] = [20, 20, 15, 15, 10]
    fases['Início'] = pd.date_range(start=inicio, periods=5, freq='B')
    fases['Término'] = fases['Início'] + pd.to_timedelta(fases['Duração'], unit='D')
    fig = px.timeline(fases, x_start="Início", x_end="Término", y="Fase da Obra", color="Fase da Obra")
    fig.update_layout(title="📆 Cronograma", xaxis_title="Data")
    return fig

def export_excel(df, nome):
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return out.getvalue()

def gerar_proposta(sim, fases):
    hoje = datetime.today().strftime("%d/%m/%Y")
    corpo = "".join([f"<tr><td>{f}</td><td>R$ {c:,.2f}</td></tr>" for f, c in zip(fases['Fase da Obra'], fases['Custo Estimado'])])
    html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial; padding: 40px; }}
        .cabecalho {{ text-align: center; }}
        .rodape {{ font-size: 11px; color: #444; text-align: center; margin-top: 40px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #aaa; padding: 6px; }}
    </style>
    </head>
    <body>
    <div class="cabecalho">
        <img src="logo_facility.png" width="120"/><br>
        <h2>Steel Facility</h2>
        <h3>Proposta Comercial — {sim['Nome']}</h3>
        <p>{hoje}</p>
    </div>
    <p><b>Área:</b> {sim['Área (m²)']} m²<br>
       <b>Preço Unitário:</b> R$ {sim['Preço Unitário']:,.2f}<br>
       <b>BDI MDO:</b> {sim['BDI MDO (%)']}%<br>
       <b>BDI MAT:</b> {sim['BDI MAT (%)']}%<br>
       <b>Custo Final:</b> <b>R$ {sim['Custo Final']:,.2f}</b></p>
    <h4>Fases da Obra</h4>
    <table><tr><th>Fase</th><th>Custo Estimado</th></tr>{corpo}</table>
    <p><b>Condições:</b> validade de 30 dias, pagamento a combinar. Não inclui fundações nem taxas municipais.</p>
    <div class="rodape">
        Steel Facility · Rua Ubá, 15 – Itaquaquecetuba · steelfacility@gmail.com · @steelfacilitybr<br>
        Assinatura: Marcelo Barbosa – CEO
    </div>
    </body>
    </html>
    """
    with open("temp_proposta.html", "w", encoding="utf-8") as f:
        f.write(html)
    pdfkit.from_file("temp_proposta.html", "proposta.pdf")
    return "proposta.pdf"

# === DADOS DAS CASAS ===
file = st.file_uploader("📁 Planilha de casas (.xlsx)", type=["xlsx"])
if file:
    df = pd.read_excel(file)
else:
    df = pd.DataFrame([
        {'Casa': f'Casa {i+1}', 'Área (m²)': a, 'Preço Unitário': 836.47}
        for i, a in enumerate([140.42, 140.39, 134.12, 141.43, 141.30, 139.13])
    ])

df['Custo Total'] = df['Área (m²)'] * df['Preço Unitário']
df['Custo Final'] = df['Custo Total'] * 1.025 * 1.013
df['Eficiência'] = 1000 / df['Custo Final']
st.subheader("🏠 Tabela Geral")
st.dataframe(df)

# === SIMULAÇÃO DE NOVOS ORÇAMENTOS ===
st.subheader("➕ Nova Simulação")
if "simulacoes" not in st.session_state:
    st.session_state.simulacoes = []

with st.form("form_sim"):
    nome = st.text_input("Nome da simulação", value=f"Simulação {len(st.session_state.simulacoes)+1}")
    area = st.number_input("Área (m²)", value=140.0)
    preco = st.number_input("Preço Unitário", value=836.47)
    bdi1 = st.number_input("BDI MDO (%)", value=2.5)
    bdi2 = st.number_input("BDI MAT (%)", value=1.3)
    gerar = st.form_submit_button("Gerar")

if gerar:
    custo = area * preco
    total = custo * (1 + bdi1 / 100) * (1 + bdi2 / 100)
    eficiencia = 1000 / total
    sim = {
        "Nome": nome, "Área (m²)": area, "Preço Unitário": preco,
        "BDI MDO (%)": bdi1, "BDI MAT (%)": bdi2,
        "Custo Final": total, "Eficiência": eficiencia
    }
    st.session_state.simulacoes.append(sim)
    st.success(f"Simulação '{nome}' criada!")

# === VISUALIZAÇÃO E COMPARATIVO ===
if st.session_state.simulacoes:
    st.subheader("📚 Histórico de Simulações")
    df_sim = pd.DataFrame(st.session_state.simulacoes)
    st.dataframe(df_sim)

    st.subheader("📊 Comparativo Visual")
    df_comp = pd.DataFrame(
        [{"Nome": r["Casa"], "Custo Final": r["Custo Final"]} for _, r in df.iterrows()] +
        [{"Nome": s["Nome"], "Custo Final": s["Custo Final"]} for s in st.session_state.simulacoes]
    )
    fig = px.bar(df_comp, x="Nome", y="Custo Final", text="Custo Final")
    fig.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
    st.plotly_chart(fig)

    # === EXPORTAÇÃO DAS SIMULAÇÕES EM EXCEL ===
df_sim = pd.DataFrame(st.session_state.simulacoes)
excel_simulacoes = export_excel(df_sim, "simulacoes_steel.xlsx")
st.download_button(
    label="📥 Baixar Simulações",
    data=excel_simulacoes,
    file_name="simulacoes_steel.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# === GERADOR DE PROPOSTA EM PDF ===
st.subheader("📝 Gerar Proposta Comercial em PDF")

sim_nome = st.selectbox("Selecione uma simulação para gerar proposta", df_sim["Nome"])
sim_selecionada = df_sim[df_sim["Nome"] == sim_nome].iloc[0].to_dict()
fases_sim = calcular_fases(sim_selecionada["Área (m²)"] * sim_selecionada["Preço Unitário"])

# Gerar e salvar PDF
pdf_path = gerar_proposta(sim_selecionada, fases_sim)
with open(pdf_path, "rb") as pdf_file:
    st.download_button(
        label="📄 Baixar Proposta PDF",
        data=pdf_file.read(),
        file_name=f"proposta_{sim_nome.lower().replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
