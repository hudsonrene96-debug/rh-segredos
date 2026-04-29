import pandas as pd
import plotly.express as px
import streamlit as st
import os

st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    if not os.path.exists(file_path):
        return None

    for enc in ['latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Tratamento de Valor
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = (
                    df[col_vlr].astype(str)
                    .str.replace('R$', '', regex=False)
                    .str.replace('.', '', regex=False)
                    .str.replace(',', '.', regex=False)
                    .str.strip()
                )
                df['VALOR_PAGO'] = pd.to_numeric(df['VALOR_PAGO'], errors='coerce').fillna(0)
            
            # Tratamento de Data
            if 'DTNEG' in df.columns:
                df['DATA_REF'] = pd.to_datetime(df['DTNEG'], errors='coerce')
                if df['DATA_REF'].isnull().all():
                    df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), 
                                                   unit='D', origin='1899-12-30', errors='coerce')
                df['DATA_REF'] = df['DATA_REF'].dt.normalize()
            
            return df
        except:
            continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # Mapeamento
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Filtros")
    periodo = None
    if 'DATA_REF' in df.columns and not df['DATA_REF'].isnull().all():
        df_datas = df.dropna(subset=['DATA_REF'])
        min_d, max_d = df_datas['DATA_REF'].min().date(), df_datas['DATA_REF'].max().date()
        periodo = st.sidebar.date_input("Filtrar Período:", value=(min_d, max_d))

    sel_emp = st.sidebar.multiselect(f"Empresa ({col_emp}):", options=sorted(df[col_emp].unique().astype(str)))
    opcoes_hist = sorted(df[col_hist].dropna().unique().astype(str)) if col_hist else []
    sel_hist = st.sidebar.multiselect("Histórico/Natureza:", options=opcoes_hist)

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    if periodo and isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        df_f = df_f[(df_f['DATA_REF'].dt.date >= periodo[0]) & (df_f['DATA_REF'].dt.date <= periodo[1])]
    if sel_emp:
        df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_hist:
        df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]

    # --- NOVOS INDICADORES (MÉDIA INCLUÍDA) ---
    c1, c2, c3, c4 = st.columns(4)
    
    total_gasto = float(df_f['VALOR_PAGO'].sum())
    qtd_func = len(df_f[col_func].unique())
    media_por_func = total_gasto / qtd_func if qtd_func > 0 else 0
    maior_valor = df_f['VALOR_PAGO'].max() if not df_f.empty else 0
    
    c1.metric("💰 Gasto Total", f"R$ {total_gasto:,.2f}")
    c2.metric("👥 Funcionários", qtd_func)
    c3.metric("⚖️ Média por Pessoa", f"R$ {media_por_func:,.2f}")
    c4.metric("📈 Maior Valor", f"R$ {maior_valor:,.2f}")

    st.divider()
    
    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🏆 Soma Total por Funcionário")
        # Mostra quem acumulou o maior valor no período
        df_soma = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_bar = px.bar(df_soma, x='VALOR_PAGO', y=col_func, orientation='h', 
                         text_auto=',.2f', color='VALOR_PAGO', color_continuous_scale='Viridis')
        st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🍕 Distribuição por Histórico")
        if col_hist and not df_f.empty:
            df_pizza = df_f.groupby(col_hist)['VALOR_PAGO'].sum().reset_index()
            fig_pizza = px.pie(df_pizza, values='VALOR_PAGO', names=col_hist, hole=0.4)
            st.plotly_chart(fig_pizza, use_container_width=True)

    st.subheader("📑 Detalhamento")
    st.dataframe(df_f, use_container_width=True)

else:
    st.error("Erro ao carregar dados.")
