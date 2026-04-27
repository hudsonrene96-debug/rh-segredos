import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configuração da página
st.set_page_config(page_title="BI de Recursos Humanos - Bem Leve", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    for enc in ['latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Tratamento do Valor
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Tratamento da Data (DTNEG) - IMPORTANTE
            if 'DTNEG' in df.columns:
                # Converte o número do Excel para data real do Python
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except:
            continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # --- MAPEAMENTO DE COLUNAS ---
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_nat = 'NATUREZA' if 'NATUREZA' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Consulta")
    
    # 1. NOVO: Filtro de Data (DTNEG)
    if 'DATA_REF' in df.columns:
        min_data = df['DATA_REF'].min().date()
        max_data = df['DATA_REF'].max().date()
        
        st.sidebar.subheader("Período (DTNEG)")
        periodo = st.sidebar.date_input(
            "Selecionar Intervalo:",
            value=(min_data, max_data),
            min_value=min_data,
            max_value=max_data
        )
    
    # 2. Filtro Empresa
    sel_emp = st.sidebar.multiselect("Empresa (CODEMP):", options=sorted(df[col_emp].unique().astype(str)))
    
    # 3. Filtro Natureza
    if col_nat:
        sel_nat = st.sidebar.multiselect("Natureza:", options=sorted(df[col_nat].dropna().unique().astype(str)))
    else:
        sel_nat = []

    # 4. Filtro Histórico
    if col_hist:
        sel_hist = st.sidebar.multiselect("Histórico:", options=sorted(df[col_hist].dropna().unique().astype(str)))
    else:
        sel_hist = []

    # 5. Filtro Funcionário
    sel_func = st.sidebar.multiselect("Funcionário:", options=sorted(df[col_func].unique().astype(str)))

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    
    # Aplicar filtro de data se o intervalo for selecionado corretamente
    if 'DATA_REF' in df.columns and len(periodo) == 2:
        start_date, end_date = periodo
        df_f = df_f[(df_f['DATA_REF'].dt.date >= start_date) & (df_f['DATA_REF'].dt.date <= end_date)]
    
    if sel_emp:  df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_nat:  df_f = df_f[df_f[col_nat].astype(str).isin(sel_nat)]
    if sel_hist: df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]
    if sel_func: df_f = df_f[df_f[col_func].astype(str).isin(sel_func)]

    # --- INDICADORES ---
    st.markdown("### 📈 Indicadores do Período Selecionado")
    c1, c2, c3, c4 = st.columns(4)
    
    total = df_f['VALOR_PAGO'].sum()
    c1.metric("💰 Total no Período", f"R$ {total:,.2f}")
    c2.metric("👥 Funcionários", len(df_f[col_func].unique()))
    
    maior = df_f['VALOR_PAGO'].max() if not df_f.empty else 0
    menor = df_f[df_f['VALOR_PAGO'] > 0]['VALOR_PAGO'].min() if not df_f.empty else 0
    
    c3.metric("📈 Maior Valor", f"R$ {maior:,.2f}")
    c4.metric("📉 Menor Valor", f"R$ {menor:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🏆 Maiores Gastos")
        rank = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_bar = px.bar(rank, x='VALOR_PAGO', y=col_func, orientation='h', color='VALOR_PAGO', color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with g2:
        st.subheader("🍕 Divisão por Histórico")
        if col_hist and not df_f.empty:
            df_p = df_f.groupby(col_hist)['VALOR_PAGO'].sum().reset_index()
            fig_pie = px.pie(df_p, values='VALOR_PAGO', names=col_hist, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABELA ---
    st.subheader("📑 Detalhamento")
    df_tab = df_f.copy()
    if 'DATA_REF' in df_tab.columns:
        df_tab['DATA_REF'] = df_tab['DATA_REF'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_tab, use_container_width=True)

else:
    st.error("Erro crítico ao carregar dados.")
