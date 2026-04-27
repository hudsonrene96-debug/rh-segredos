import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página
st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    try:
        # Nome exato do ficheiro que está no seu GitHub
        df = pd.read_csv('FUNCIONARIOS.xls', sep=',', encoding='utf-8')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Converter valores financeiros
        if 'VLRDESDOB' in df.columns:
            df['VLRDESDOB'] = pd.to_numeric(df['VLRDESDOB'], errors='coerce').fillna(0)
        
        # Converter datas do Excel
        if 'DTNEG' in df.columns:
            df['DATA'] = pd.to_datetime(df['DTNEG'], unit='D', origin='1899-12-30', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro: {e}")
        return None

df = carregar_dados()

if df is not None:
    st.title("👥 Gestão de RH - Bem Leve (Privado)")
    
    # Filtros
    st.sidebar.header("Filtros")
    col_func = 'RAZAOSOCIAL'
    
    # Filtro de Unidade
    if 'CODEMP' in df.columns:
        unidades = sorted(df['CODEMP'].unique().astype(str))
        sel_unidade = st.sidebar.multiselect("Unidade (CODEMP):", unidades)
        if sel_unidade:
            df = df[df['CODEMP'].astype(str).isin(sel_unidade)]

    # Filtro de Funcionário
    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect("Funcionários:", options=lista_func)
    
    df_f = df[df[col_func].isin(sel_func)] if sel_func else df

    # Indicadores
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pago", f"R$ {df_f['VLRDESDOB'].sum():,.2f}")
    c2.metric("Nº de Colaboradores", len(df_f[col_func].unique()))
    c3.metric("Lançamentos", len(df_f))

    st.markdown("---")

    # Gráficos
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("Custos por Colaborador (Top 10)")
        rank = df_f.groupby(col_func)['VLRDESDOB'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig1 = px.bar(rank, x='VLRDESDOB', y=col_func, orientation='h', color='VLRDESDOB', color_continuous_scale='Reds')
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        st.subheader("Tipos de Pagamento (Histórico)")
        if 'HISTORICO' in df_f.columns:
            hist = df_f.groupby('HISTORICO')['VLRDESDOB'].sum().reset_index()
            fig2 = px.pie(hist, values='VLRDESDOB', names='HISTORICO', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

    # Tabela detalhada
    st.subheader("Lista de Pagamentos Detalhada")
    df_view = df_f[[col_func, 'VLRDESDOB', 'HISTORICO', 'DATA']].copy()
    df_view['DATA'] = df_view['DATA'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_view.sort_values('VLRDESDOB', ascending=False), use_container_width=True)
else:
    st.warning("Verifique se o ficheiro CSV foi carregado corretamente.")
