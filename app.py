import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configuração da página
st.set_page_config(page_title="BI de Recursos Humanos - Bem Leve", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    # Testamos várias codificações para evitar erros de acento
    for enc in ['latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            # Limpeza: Remove espaços e padroniza nomes das colunas
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Tratamento do Valor Financeiro (VLRDESDOB)
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Tratamento da Data (DTNEG)
            col_dt = next((c for c in df.columns if 'DT' in c or 'DATA' in c), None)
            if col_dt:
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df[col_dt], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except:
            continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # --- MAPEAMENTO DE COLUNAS ---
    col_emp = next((c for c in df.columns if 'EMP' in c or 'COD' in c), df.columns[0])
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Consulta")
    
    # Filtro de Empresa
    lista_emp = sorted(df[col_emp].unique().astype(str))
    sel_emp = st.sidebar.multiselect("Filtrar por Empresa (CODEMP):", options=lista_emp)
    
    # Filtro de Natureza (Histórico)
    if col_hist:
        # Usamos dropna() e o map(str) para evitar erro no sorted
        lista_hist = sorted(df[col_hist].dropna().unique().astype(str))
        sel_hist = st.sidebar.multiselect("Filtrar por Natureza (Histórico):", options=lista_hist)
    else:
        sel_hist = []

    # Filtro de Funcionário
    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect("Filtrar por Funcionário:", options=lista_func)

    # --- APLICAR FILTROS ---
    df_f = df.copy()
    if sel_emp:  df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_hist: df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]
    if sel_func: df_f = df_f[df_f[col_func].astype(str).isin(sel_func)]

    # --- INDICADORES ---
    st.markdown("### 📈 Indicadores Principais")
    c1, c2, c3, c4 = st.columns(4)
    
    total_gasto = df_f['VALOR_PAGO'].sum()
    c1.metric("💰 Total Gasto", f"R$ {total_gasto:,.2f}")
    
    qtd_func = len(df_f[col_func].unique())
    c2.metric("👥 Qtd. Funcionários", qtd_func)
    
    # Maior e Menor Salário do filtro selecionado
    maior_sal = df_f['VALOR_PAGO'].max() if not df_f.empty else 0
    # Menor valor acima de zero
    menor_sal = df_f[df_f['VALOR_PAGO'] > 0]['VALOR_PAGO'].min() if not df_f.empty else 0
    
    c3.metric("🔝 Maior Valor", f"R$ {maior_sal:,.2f}")
    c4.metric("📉 Menor Valor", f"R$ {menor_sal:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🏆 Maiores Custos por Funcionário")
        rank = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_bar = px.bar(rank, x='VALOR_PAGO', y=col_func, orientation='h', 
                         color='VALOR_PAGO', color_continuous_scale='Blues',
                         labels={'VALOR_PAGO': 'Valor (R$)', col_func: 'Funcionário'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with g2:
        st.subheader("🍕 Gastos por Natureza")
        if col_hist and not df_f.empty:
            # Agrupa por histórico para a pizza
            df_pizza = df_f.groupby(col_hist)['VALOR_PAGO'].sum().reset_index()
            fig_pie = px.pie(df_pizza, values='VALOR_PAGO', names=col_hist, hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Selecione dados para ver o gráfico de pizza.")

    # --- TABELA DETALHADA ---
    st.subheader("📑 Detalhamento dos Lançamentos")
    # Mostrar apenas colunas interessantes
    colunas_view = [c for c in [col_emp, col_func, col_hist, 'VALOR_PAGO', 'DATA_REF'] if c in df_f.columns]
    df_display = df_f[colunas_view].copy()
    if 'DATA_REF' in df_display.columns:
        df_display['DATA_REF'] = df_display['DATA_REF'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_display.sort_values('VALOR_PAGO', ascending=False), use_container_width=True)

else:
    st.error("Erro ao processar arquivo. Verifique se 'FUNCIONARIOS.csv' está no GitHub.")
