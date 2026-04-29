import pandas as pd
import plotly.express as px
import streamlit as st
import os

# 1. A configuração deve ser sempre a primeira linha de comando do Streamlit
st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    
    # Verifica se o arquivo existe fisicamente
    if not os.path.exists(file_path):
        return None

    # Tenta várias codificações para resolver o erro 'utf-8' (byte 0xcd)
    # Geralmente arquivos de sistemas brasileiros usam 'latin1' ou 'cp1252'
    for enc in ['latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']:
        try:
            # O sep=None faz o pandas detectar se é vírgula ou ponto-e-vírgula sozinho
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            
            # Padroniza nomes das colunas
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Tratamento Financeiro
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Tratamento de Data (DTNEG)
            if 'DTNEG' in df.columns:
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except:
            continue
    return None

# Início da lógica do App
df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # Mapeamento de Colunas
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de Data (protegido)
    periodo = None
    if 'DATA_REF' in df.columns and not df['DATA_REF'].isnull().all():
        min_d, max_d = df['DATA_REF'].min().date(), df['DATA_REF'].max().date()
        periodo = st.sidebar.date_input("Período (DTNEG):", value=(min_d, max_d))

    sel_emp = st.sidebar.multiselect("Empresa (CODEMP):", options=sorted(df[col_emp].unique().astype(str)))
    
    # Filtro de Histórico (protegido contra valores nulos/TypeError)
    opcoes_hist = []
    if col_hist:
        opcoes_hist = sorted(df[col_hist].dropna().unique().astype(str))
    sel_hist = st.sidebar.multiselect("Histórico/Natureza:", options=opcoes_hist)

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    
    if periodo and isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        df_f = df_f[(df_f['DATA_REF'].dt.date >= periodo[0]) & (df_f['DATA_REF'].dt.date <= periodo[1])]
    
    if sel_emp:
        df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_hist:
        df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]

    # --- DASHBOARD ---
    c1, c2, c3 = st.columns(3)
    total_gasto = df_f['VALOR_PAGO'].sum() if 'VALOR_PAGO' in df_f.columns else 0
    c1.metric("💰 Total Gasto", f"R$ {total_gasto:,.2f}")
    c2.metric("👥 Funcionários", len(df_f[col_func].unique()))
    c3.metric("📈 Maior Valor", f"R$ {df_f['VALOR_PAGO'].max():,.2f}" if not df_f.empty else "R$ 0,00")

    st.divider()
    
    # Tabela detalhada
    st.subheader("📑 Detalhamento")
    st.dataframe(df_f, use_container_width=True)

else:
    st.warning("⚠️ O arquivo 'FUNCIONARIOS.csv' não foi detectado ou está com formato inválido no GitHub.")
