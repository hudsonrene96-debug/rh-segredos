import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página
st.set_page_config(page_title="RH Estratégico | Bem Leve", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    # Tenta várias codificações para evitar o erro de decoding
    for enc in ['latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Limpeza Financeira
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Limpeza de Data (DTNEG) - Proteção contra erros de calendário
            if 'DTNEG' in df.columns:
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
                df = df.dropna(subset=['DATA_REF']) 
            
            return df
        except:
            continue
    return None

df = carregar_dados()

if df is not None and not df.empty:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # Mapeamento dinâmico de colunas
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_nat = 'NATUREZA' if 'NATUREZA' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Consulta")
    
    # Inicializa período para evitar NameError
    periodo = None
    if 'DATA_REF' in df.columns:
        min_d, max_d = df['DATA_REF'].min().date(), df['DATA_REF'].max().date()
        periodo = st.sidebar.date_input("Período (DTNEG):", value=(min_d, max_d), min_value=min_d, max_value=max_d)

    # Filtros com proteção contra valores vazios
    sel_emp = st.sidebar.multiselect(f"Empresa ({col_emp}):", options=sorted(df[col_emp].unique().astype(str)))
    sel_nat = st.sidebar.multiselect("Natureza:", options=sorted(df[col_nat].dropna().unique().astype(str))) if col_nat else []
    sel_hist = st.sidebar.multiselect("Histórico:", options=sorted(df[col_hist].dropna().unique().astype(str))) if col_hist else []
    sel_func = st.sidebar.multiselect("Funcionário:", options=sorted(df[col_func].unique().astype(str)))

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    if periodo and isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        df_f = df_f[(df_f['DATA_REF'].dt.date >= periodo[0]) & (df_f['DATA_REF'].dt.date <= periodo[1])]
    
    if sel_emp:  df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_nat:  df_f = df_f[df_f[col_nat].astype(str).isin(sel_nat)]
    if sel_hist: df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]
    if sel_func: df_f = df_f[df_f[col_func].astype(str).isin(sel_func)]

    # --- INDICADORES ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Gasto", f"R$ {df_f['VALOR_PAGO'].sum():,.2f}")
    c2.metric("👥 Funcionários", len(df_f[col_func].unique()))
    
    maior = df_f['VALOR_PAGO'].max() if not df_f.empty else 0
    menor = df_f[df_f['VALOR_PAGO'] > 0]['VALOR_PAGO'].min() if not df_f.empty else 0
    c3.metric("📈 Maior Salário", f"R$ {maior:,.2f}")
    c4.metric("📉 Menor Salário", f"R$ {menor:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("🏆 Maiores Custos")
        rank = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        st.plotly_chart(px.bar(rank, x='VALOR_PAGO', y=col_func, orientation='h', color='VALOR_PAGO', color_continuous_scale='Blues'), use_container_width=True)
        
    with g2:
        st.subheader("🍕 Distribuição por Histórico")
        if col_hist and not df_f.empty:
            df_p = df_f.groupby(col_hist)['VALOR_PAGO'].sum().reset_index()
            st.plotly_chart(px.pie(df_p, values='VALOR_PAGO', names=col_hist, hole=0.4), use_container_width=True)

    st.subheader("📑 Detalhamento")
    df_tab = df_f.copy()
    if 'DATA_REF' in df_tab.columns: df_tab['DATA_REF'] = df_tab['DATA_REF'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_tab, use_container_width=True)

else:
    st.error("Erro ao carregar os dados. Verifique o arquivo 'FUNCIONARIOS.csv' no GitHub.")
