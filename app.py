import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página
st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    try:
        # Lendo o arquivo que você já subiu no GitHub
        df = pd.read_csv('FUNCIONARIOS.csv', sep=',', encoding='utf-8')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Converter valores financeiros
        if 'VLRDESDOB' in df.columns:
            df['VLRDESDOB'] = pd.to_numeric(df['VLRDESDOB'], errors='coerce').fillna(0)
        
        # Converter datas (padrão Excel)
        if 'DTNEG' in df.columns:
            df['DATA'] = pd.to_datetime(df['DTNEG'], unit='D', origin='1899-12-30', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro: {e}")
        return None

df = carregar_dados()

if df is not None:
    st.title("👥 Gestão de RH - Bem Leve (Privado)")
    
    # Filtros na Barra Lateral
    st.sidebar.header("🔍 Filtros de Consulta")
    col_func = 'RAZAOSOCIAL'
    
    # Lista de funcionários para o filtro
    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect("Selecionar Funcionário(s):", options=lista_func)
    
    # Aplicar Filtro
    df_f = df[df[col_func].isin(sel_func)] if sel_func else df

    # Indicadores principais
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Total Desembolsado", f"R$ {df_f['VLRDESDOB'].sum():,.2f}")
    m2.metric("👥 Qtd. Funcionários", len(df_f[col_func].unique()))
    m3.metric("📑 Total Lançamentos", len(df_f))

    st.markdown("---")

    # Gráficos de Análise
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📊 Top 10 Maiores Custos")
        rank = df_f.groupby(col_func)['VLRDESDOB'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig1 = px.bar(rank, x='VLRDESDOB', y=col_func, orientation='h', color='VLRDESDOB', 
                          color_continuous_scale='Reds', labels={'VLRDESDOB': 'Valor (R$)', col_func: 'Funcionário'})
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        st.subheader("🍕 Distribuição por Histórico")
        if 'HISTORICO' in df_f.columns:
            # Agrupa os pequenos em 'Outros' para não poluir o gráfico
            hist_resumo = df_f.groupby('HISTORICO')['VLRDESDOB'].sum().sort_values(ascending=False).reset_index()
            fig2 = px.pie(hist_resumo.head(10), values='VLRDESDOB', names='HISTORICO', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

    # Tabela detalhada no final
    st.subheader("📑 Histórico Detalhado")
    df_tab = df_f[[col_func, 'VLRDESDOB', 'HISTORICO', 'DATA']].copy()
    df_tab['DATA'] = df_tab['DATA'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_tab.sort_values('VLRDESDOB', ascending=False), use_container_width=True)

else:
    st.error("Erro crítico: Verifique se o nome do arquivo CSV no GitHub é exatamente 'FUNCIONARIOS.xls - Sheet 1.csv'")
