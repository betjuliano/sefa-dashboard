
import os
import io
import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import statsmodels.api as sm
from scipy import stats
from scipy.stats import chi2_contingency, pearsonr, spearmanr

from dotenv import load_dotenv

# ===== NOVO SISTEMA DE PROCESSAMENTO =====
from app_integration import (
    app_integration,
    update_global_variables as new_update_global_variables,
    filter_by_question_set as new_filter_by_question_set,
    compute_metrics as new_compute_metrics,
    normalize_likert as new_normalize_likert,
    normalize_satisfaction as new_normalize_satisfaction,
    add_sidebar_enhancements
)
# ==========================================


# Supabase removido - usando apenas armazenamento local

load_dotenv()

st.set_page_config(
    page_title="Dashboard de Qualidade - MVP",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Utils
# Load configuration
@st.cache_resource
def load_mapping(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_mapping_for_question_set(question_set: str):
    """Get the appropriate mapping based on question set"""
    if question_set == "8 questões":
        return load_mapping(os.path.join("config", "items_mapping_8q.json"))
    else:
        return load_mapping(os.path.join("config", "items_mapping.json"))

def update_global_variables(question_set: str):
    """Atualiza as variáveis globais baseado no conjunto de questões selecionado - NOVO SISTEMA"""
    # Usar o novo sistema integrado
    new_update_global_variables(question_set)

# Initialize with default mapping (will be updated based on question set)
MAPPING = load_mapping(os.path.join("config", "items_mapping.json"))

DIMENSIONS = MAPPING["dimensions"]
LIKERT_ORDER = MAPPING["likert_order"]
LIKERT_MAP = {k: v for k, v in MAPPING["likert_map"].items()}
SAT_FIELD = MAPPING["satisfaction_field"]
SAT_MAP = MAPPING["satisfaction_map"]
PROFILE_FIELDS = MAPPING["profile_fields"]

DEFAULT_GOAL = float(os.getenv("DEFAULT_GOAL", "4.0"))

# Sistema usando apenas armazenamento local

# Session state
from core.data_manager import DataManager
# Remover import de UserPreferences
# from core.models import UserPreferences

if "auth" not in st.session_state:
    st.session_state.auth = {"email": None, "logged_in": False}
if "uploads" not in st.session_state:
    st.session_state.uploads = []  # fallback if Supabase is not used
if "dm" not in st.session_state:
    st.session_state.dm = DataManager()

# -----------------------------
# Auth (simplified; Supabase optional)
# -----------------------------
def login_ui():
    st.sidebar.subheader("Login / Registro")
    email = st.sidebar.text_input("E-mail")
    password = st.sidebar.text_input("Senha", type="password")

    col1, col2 = st.sidebar.columns(2)
    if col1.button("Entrar"):
        try:
            ok = st.session_state.dm.authenticate_user(email, password)
            if ok:
                st.session_state.auth = {"email": email, "logged_in": True}
                st.sidebar.success("Login realizado")
                st.rerun()
            else:
                st.sidebar.error("Credenciais inválidas.")
        except Exception as e:
            st.sidebar.error(f"Falha no login: {e}")

    if col2.button("Registrar"):
        st.sidebar.info("Registro indisponível no modo demo. Use qualquer email/senha em 'Entrar'.")

def logout_btn():
    if st.sidebar.button("🚪 Logout"):
        st.session_state.auth = {"email": None, "logged_in": False}
        st.rerun()

# -----------------------------
# Data processing
# -----------------------------
def normalize_likert(series: pd.Series) -> pd.Series:
    """Normaliza escala Likert - NOVO SISTEMA"""
    # Usar o novo ScaleConverter
    return new_normalize_likert(series)

def normalize_satisfaction(series: pd.Series) -> pd.Series:
    """Normaliza escala de satisfação - NOVO SISTEMA"""
    # Usar o novo ScaleConverter
    return new_normalize_satisfaction(series)

def show_preprocessed_stats(df: pd.DataFrame):
    """Exibe estatísticas dos dados pré-processados se disponíveis"""
    if 'Media_Respostas' in df.columns and 'Num_Respostas_Validas' in df.columns:
        st.subheader("📊 Estatísticas dos Dados Pré-processados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Média Geral", f"{df['Media_Respostas'].mean():.2f}")
            st.metric("Mediana", f"{df['Media_Respostas'].median():.2f}")
        
        with col2:
            st.metric("Desvio Padrão", f"{df['Media_Respostas'].std():.2f}")
            st.metric("Amplitude", f"{df['Media_Respostas'].max() - df['Media_Respostas'].min():.2f}")
        
        with col3:
            st.metric("Valor Mínimo", f"{df['Media_Respostas'].min():.2f}")
            st.metric("Valor Máximo", f"{df['Media_Respostas'].max():.2f}")
        
        # Distribuição de respostas válidas
        st.subheader("📈 Distribuição de Respostas Válidas por Linha")
        valid_counts = df['Num_Respostas_Validas'].value_counts().sort_index()
        
        col1, col2 = st.columns(2)
        with col1:
            for count, freq in valid_counts.items():
                st.write(f"**{count} respostas:** {freq} linhas ({freq/len(df)*100:.1f}%)")
        
        with col2:
            # Gráfico de barras da distribuição
            import plotly.express as px
            fig = px.bar(
                x=valid_counts.index, 
                y=valid_counts.values,
                labels={'x': 'Número de Respostas Válidas', 'y': 'Frequência'},
                title="Distribuição de Respostas Válidas"
            )
            st.plotly_chart(fig, use_container_width=True)

def compute_metrics(df: pd.DataFrame, goal: float):
    """Calcula métricas do questionário - NOVO SISTEMA"""
    # Usar o novo sistema integrado
    return new_compute_metrics(df, goal)


def prepare_data_for_analysis(df: pd.DataFrame):
    """Prepare data for statistical analysis"""
    df_analysis = df.copy()
    
    # Convert Likert scales to numeric
    for dim_name, items in DIMENSIONS.items():
        for item in items:
            if item in df_analysis.columns:
                df_analysis[item] = normalize_likert(df_analysis[item])
    
    # Convert satisfaction to numeric
    if SAT_FIELD in df_analysis.columns:
        df_analysis[SAT_FIELD] = normalize_satisfaction(df_analysis[SAT_FIELD])
    
    # Create dimension scores (mean of items in each dimension)
    print(f"DEBUG: DIMENSIONS = {DIMENSIONS}")
    print(f"DEBUG: df_analysis.columns = {list(df_analysis.columns)}")
    
    for dim_name, items in DIMENSIONS.items():
        available_items = [item for item in items if item in df_analysis.columns]
        print(f"DEBUG: For dimension '{dim_name}', items = {items}")
        print(f"DEBUG: Available items = {available_items}")
        if available_items:
            df_analysis[f'{dim_name}_score'] = df_analysis[available_items].mean(axis=1)
            print(f"DEBUG: Created score column '{dim_name}_score'")
        else:
            print(f"DEBUG: No available items for dimension '{dim_name}'")
    
    print(f"DEBUG: Final columns after score creation = {list(df_analysis.columns)}")
    
    # Encode categorical variables
    le_sexo = LabelEncoder()
    le_escolaridade = LabelEncoder()
    le_servidor = LabelEncoder()
    
    if PROFILE_FIELDS["Sexo"] in df_analysis.columns:
        df_analysis['sexo_encoded'] = le_sexo.fit_transform(df_analysis[PROFILE_FIELDS["Sexo"]].fillna('Não informado'))
    
    if PROFILE_FIELDS["Escolaridade"] in df_analysis.columns:
        df_analysis['escolaridade_encoded'] = le_escolaridade.fit_transform(df_analysis[PROFILE_FIELDS["Escolaridade"]].fillna('Não informado'))
    
    # Handle different field names for public servant field
    servidor_field = PROFILE_FIELDS.get("Servidor Público") or PROFILE_FIELDS.get("Funcionario_Publico")
    if servidor_field and servidor_field in df_analysis.columns:
        df_analysis['servidor_encoded'] = le_servidor.fit_transform(df_analysis[servidor_field].fillna('Não informado'))
    
    return df_analysis

def regression_analysis(df: pd.DataFrame, target_dimension: str):
    """Perform regression analysis for a dimension"""
    df_clean = df.dropna(subset=[f'{target_dimension}_score'])
    
    # Prepare features
    features = []
    feature_names = []
    
    if 'idade_encoded' in df_clean.columns:
        features.append(df_clean[PROFILE_FIELDS["Idade"]].fillna(df_clean[PROFILE_FIELDS["Idade"]].median()))
        feature_names.append('Idade')
    
    if 'sexo_encoded' in df_clean.columns:
        features.append(df_clean['sexo_encoded'])
        feature_names.append('Sexo')
    
    if 'escolaridade_encoded' in df_clean.columns:
        features.append(df_clean['escolaridade_encoded'])
        feature_names.append('Escolaridade')
    
    if 'servidor_encoded' in df_clean.columns:
        features.append(df_clean['servidor_encoded'])
        feature_names.append('Servidor Público')
    
    if SAT_FIELD in df_clean.columns:
        features.append(df_clean[SAT_FIELD].fillna(df_clean[SAT_FIELD].median()))
        feature_names.append('Satisfação Geral')
    
    if not features:
        return None, None
    
    X = np.column_stack(features)
    y = df_clean[f'{target_dimension}_score']
    
    # Remove rows with NaN
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[mask]
    y = y[mask]
    
    if len(X) < 10:  # Need minimum samples
        return None, None
    
    # OLS Regression
    X_with_const = sm.add_constant(X)
    model = sm.OLS(y, X_with_const).fit()
    
    return model, feature_names

def multivariate_analysis(df: pd.DataFrame):
    """Perform multivariate analysis"""
    # Prepare data
    dimension_scores = []
    dimension_names = []
    
    for dim_name in DIMENSIONS.keys():
        if f'{dim_name}_score' in df.columns:
            dimension_scores.append(df[f'{dim_name}_score'].fillna(df[f'{dim_name}_score'].median()))
            dimension_names.append(dim_name)
    
    if len(dimension_scores) < 2:
        return None
    
    X = np.column_stack(dimension_scores)
    
    # Remove rows with NaN
    mask = ~np.isnan(X).any(axis=1)
    X = X[mask]
    
    if len(X) < 10:
        return None
    
    # Standardize data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # PCA Analysis
    pca = PCA()
    pca_result = pca.fit_transform(X_scaled)
    
    # Determine optimal number of clusters
    silhouette_scores = []
    K_range = range(2, min(8, len(X)//10 + 1))
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        silhouette_avg = silhouette_score(X_scaled, cluster_labels)
        silhouette_scores.append(silhouette_avg)
    
    optimal_k = K_range[np.argmax(silhouette_scores)] if silhouette_scores else 2
    
    # Final clustering
    kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    cluster_labels = kmeans_final.fit_predict(X_scaled)
    
    return {
        'pca': pca,
        'pca_result': pca_result,
        'scaler': scaler,
        'kmeans': kmeans_final,
        'cluster_labels': cluster_labels,
        'dimension_names': dimension_names,
        'optimal_k': optimal_k,
        'silhouette_scores': silhouette_scores,
        'X_scaled': X_scaled
    }

def filters_ui(df: pd.DataFrame):
    st.sidebar.markdown("### Filtros")
    df_filtered = df.copy()

    # carregar filtros salvos, se houver
    saved = {}
    if st.session_state.auth["logged_in"]:
        try:
            p = st.session_state.dm.get_user_preferences(st.session_state.auth["email"]) 
            saved = p.get("saved_filters", {}) if isinstance(p, dict) else {}
        except Exception:
            saved = {}

    # Idade
    if PROFILE_FIELDS["Idade"] in df.columns:
        # Verificar se há dados válidos na coluna de idade
        idade_col = df[PROFILE_FIELDS["Idade"]]
        idade_valida = idade_col.dropna()
        
        if len(idade_valida) > 0:
            # Tentar converter valores para numérico se possível
            try:
                # Se os valores são strings como "25-34 anos", extrair o primeiro número
                idade_numerica = []
                for val in idade_valida:
                    if isinstance(val, str):
                        # Extrair números da string (ex: "25-34 anos" -> 25)
                        import re
                        numeros = re.findall(r'\d+', str(val))
                        if numeros:
                            idade_numerica.append(int(numeros[0]))
                    elif pd.notna(val):
                        try:
                            idade_numerica.append(int(float(val)))
                        except:
                            pass
                
                if idade_numerica:
                    min_age = min(idade_numerica)
                    max_age = max(idade_numerica)
                    default_age = tuple(saved.get("idade", (min_age, max_age)))
                    age_min, age_max = st.sidebar.slider("Idade", min_value=min_age, max_value=max_age, value=default_age)
                    
                    # Filtrar baseado nos valores originais
                    mask_idade = pd.Series([True] * len(df_filtered))
                    for idx, val in enumerate(df_filtered[PROFILE_FIELDS["Idade"]]):
                        if pd.notna(val):
                            if isinstance(val, str):
                                numeros = re.findall(r'\d+', str(val))
                                if numeros:
                                    idade_num = int(numeros[0])
                                    mask_idade.iloc[idx] = age_min <= idade_num <= age_max
                            else:
                                try:
                                    idade_num = int(float(val))
                                    mask_idade.iloc[idx] = age_min <= idade_num <= age_max
                                except:
                                    pass
                    
                    df_filtered = df_filtered[mask_idade]
                else:
                    st.sidebar.info("⚠️ Dados de idade não disponíveis para filtro")
            except Exception as e:
                st.sidebar.warning(f"⚠️ Erro ao processar dados de idade: {str(e)}")
        else:
            st.sidebar.info("⚠️ Dados de idade não disponíveis para filtro")

    # Sexo
    if PROFILE_FIELDS["Sexo"] in df.columns:
        sex_opts = ["Todos"] + sorted([x for x in df[PROFILE_FIELDS["Sexo"]].dropna().unique().tolist()])
        default_sex = saved.get("sexo", "Todos")
        sex_sel = st.sidebar.selectbox("Sexo", options=sex_opts, index=sex_opts.index(default_sex) if default_sex in sex_opts else 0)
        if sex_sel != "Todos":
            df_filtered = df_filtered[df_filtered[PROFILE_FIELDS["Sexo"]] == sex_sel]

    # Escolaridade
    if PROFILE_FIELDS["Escolaridade"] in df.columns:
        esc_opts = ["Todos"] + sorted([x for x in df[PROFILE_FIELDS["Escolaridade"]].dropna().unique().tolist()])
        default_esc = saved.get("escolaridade", "Todos")
        esc_sel = st.sidebar.selectbox("Escolaridade", options=esc_opts, index=esc_opts.index(default_esc) if default_esc in esc_opts else 0)
        if esc_sel != "Todos":
            df_filtered = df_filtered[df_filtered[PROFILE_FIELDS["Escolaridade"]] == esc_sel]

    # Servidor Público
    servidor_field = PROFILE_FIELDS.get("Servidor Público") or PROFILE_FIELDS.get("Funcionario_Publico")
    if servidor_field and servidor_field in df.columns:
        sp_opts = ["Todos"] + sorted([x for x in df[servidor_field].dropna().unique().tolist()])
        default_sp = saved.get("servidor_publico", "Todos")
        sp_sel = st.sidebar.selectbox("Servidor Público", options=sp_opts, index=sp_opts.index(default_sp) if default_sp in sp_opts else 0)
        if sp_sel != "Todos":
            df_filtered = df_filtered[df_filtered[servidor_field] == sp_sel]

    # salvar filtros atualizados, se logado
    if st.session_state.auth["logged_in"]:
        try:
            current = st.session_state.dm.get_user_preferences(st.session_state.auth["email"]) 
            new_saved = {
                "idade": (age_min, age_max) if PROFILE_FIELDS["Idade"] in df.columns else saved.get("idade"),
                "sexo": sex_sel if PROFILE_FIELDS["Sexo"] in df.columns else saved.get("sexo"),
                "escolaridade": esc_sel if PROFILE_FIELDS["Escolaridade"] in df.columns else saved.get("escolaridade"),
                "servidor_publico": sp_sel if servidor_field and servidor_field in df.columns else saved.get("servidor_publico"),
            }
            updated = dict(current or {}) if isinstance(current, dict) else {}
            updated["saved_filters"] = new_saved
            st.session_state.dm.save_user_preferences(st.session_state.auth["email"], updated)
        except Exception:
            pass

    return df_filtered

# -----------------------------
# UI: Sidebar
# -----------------------------
st.sidebar.title("📊 Dashboard de Qualidade")
if not st.session_state.auth["logged_in"]:
    login_ui()
else:
    st.sidebar.success(f"Logado como: {st.session_state.auth['email']}")
    logout_btn()

# goal persistente por usuário (se logado)
if st.session_state.auth["logged_in"]:
    prefs = st.session_state.dm.get_user_preferences(st.session_state.auth["email"])  # dict
    goal_default = float(prefs.get("goal", prefs.get("goal_global", DEFAULT_GOAL)))
else:
    prefs = None
    goal_default = DEFAULT_GOAL

goal = st.sidebar.number_input("Meta (1 a 5)", min_value=1.0, max_value=5.0, value=goal_default, step=0.1)
# Se usuário alterar a meta e estiver logado, salvar
if st.session_state.auth["logged_in"] and abs(goal - goal_default) > 1e-9:
    new_prefs = dict(prefs or {})
    new_prefs["goal"] = float(goal)
    st.session_state.dm.save_user_preferences(st.session_state.auth["email"], new_prefs)

st.sidebar.markdown("---")

# Seletor de conjunto de questões
if "question_set" not in st.session_state:
    st.session_state.question_set = "Completo (26 questões)"

question_set = st.sidebar.radio(
    "Conjunto de Questões",
    options=["Completo (26 questões)", "20 questões", "8 questões"],
    index=["Completo (26 questões)", "20 questões", "8 questões"].index(st.session_state.question_set)
)

# Atualizar variáveis globais se o conjunto mudou
if question_set != st.session_state.question_set:
    update_global_variables(question_set)
    
st.session_state.question_set = question_set

# Adicionar melhorias do novo sistema
add_sidebar_enhancements()

# Upload específico para 8 questões
if question_set == "8 questões":
    uploaded_8q = st.sidebar.file_uploader(
        "Upload base 8 questões (opcional)",
        type=["csv"],
        key="upload_8q"
    )
    if uploaded_8q:
        st.session_state.uploaded_8q = uploaded_8q
        st.session_state.data_8q_source = uploaded_8q.name
    else:
        st.session_state.uploaded_8q = None
        st.session_state.data_8q_source = "basetransp.csv (padrão)"

st.sidebar.markdown("---")
st.sidebar.caption("CSV padrão: separador `;` e codificação `latin-1`.")

# -----------------------------
# Main Pages
# -----------------------------
pages = {
    "Dashboard": "dashboard",
    "Portal Transparência": "portal_transparencia",
    "Upload de Arquivo": "upload",
    "Análise Detalhada": "analysis",
    "Perfil": "profile",
    "Configurações": "settings",
}
page = st.sidebar.radio("Navegação", options=list(pages.keys()))

# -----------------------------
# Question Set Filtering
# -----------------------------
def filter_by_question_set(df: pd.DataFrame, question_set: str):
    """Filtra o dataframe baseado no conjunto de questões selecionado - NOVO SISTEMA"""
    # Usar o novo sistema integrado
    return new_filter_by_question_set(df, question_set)


def read_csv(uploaded_file, delimiter=";", encoding="latin-1"):
    return pd.read_csv(uploaded_file, sep=delimiter, encoding=encoding)

def data_source_ui():
    st.markdown("#### Fonte de Dados")
    
    # Mostrar fonte atual
    if st.session_state.data is not None:
        st.info(f"📊 **Dados atuais:** {st.session_state.data_source}")
        st.caption(f"Linhas: {len(st.session_state.data)}, Colunas: {len(st.session_state.data.columns)}")
    
    st.markdown("#### Upload de Novo Arquivo")
    uploaded = st.file_uploader("Carregue um arquivo .csv para substituir os dados atuais", type=["csv"])
    col_delim, col_enc = st.columns(2)
    delimiter = col_delim.selectbox("Delimitador", options=[";", ",", "\\t"], index=0)
    enc = col_enc.selectbox("Codificação", options=["latin-1", "utf-8"], index=0)

    if uploaded is not None:
        try:
            df = read_csv(uploaded, delimiter=delimiter.replace("\\t", "\t"), encoding=enc)
            return df, uploaded.name
        except Exception as e:
            st.error(f"Erro ao ler CSV: {e}")

    # Botões para restaurar dados padrão
    st.markdown("#### Restaurar Dados Padrão")
    st.caption("Escolha qual conjunto de dados padrão deseja carregar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Restaurar baseKelm.csv\n(Completo - 20 questões)", use_container_width=True):
            try:
                df = read_csv(os.path.join("sample_data", "baseKelm.csv"))
                # Automaticamente definir para "20 questões" para aplicar filtro
                st.session_state.question_set = "20 questões"
                return df, "baseKelm.csv (restaurado)"
            except Exception as e:
                st.error(f"Erro ao carregar baseKelm.csv: {e}")
    
    with col2:
        if st.button("🔄 Restaurar basetransp.csv\n(8 questões)", use_container_width=True):
            try:
                df = read_csv(os.path.join("data", "basetransp.csv"))
                # Automaticamente definir para "8 questões"
                st.session_state.question_set = "8 questões"
                return df, "basetransp.csv (restaurado)"
            except Exception as e:
                st.error(f"Erro ao carregar basetransp.csv: {e}")
    return None, None

# -----------------------------
# Page: Upload
# -----------------------------
if page == "Upload de Arquivo":
    st.header("📤 Upload de Arquivo")
    df, fname = data_source_ui()
    if df is not None:
        st.success(f"Arquivo carregado: **{fname}** — linhas: {len(df)}, colunas: {len(df.columns)}")
        st.dataframe(df.head(10))

        # Save to session
        st.session_state.data = df
        st.session_state.data_source = fname

        # Log upload via DataManager (local storage, substitui anteriores)
        if st.session_state.auth["logged_in"]:
            try:
                rec = st.session_state.dm.save_upload(st.session_state.auth["email"], df, fname)
                # manter um pequeno resumo na sessão para UI rápida
                st.session_state.uploads = [{
                    "user_email": rec.user_email,
                    "filename": rec.filename,
                    "n_rows": rec.n_rows,
                    "n_cols": rec.n_cols,
                    "uploaded_at": rec.uploaded_at.isoformat()
                }]
            except Exception as e:
                st.warning(f"Não foi possível registrar upload localmente: {e}")
        
        # Forçar rerun para atualizar a interface
        st.rerun()

# -----------------------------
# Page: Dashboard
# -----------------------------
if page == "Dashboard":
    st.header("🏠 Visão Geral")
    if st.session_state.data is None:
        st.info("Carregue um CSV na página **Upload de Arquivo** ou use o dado de exemplo.")
    else:
        # Mostrar fonte dos dados no dashboard
        st.info(f"📊 **Analisando dados de:** {st.session_state.data_source} | Conjunto: {st.session_state.question_set}")
        df = st.session_state.data.copy()
        # Aplicar filtro de conjunto de questões
        df = filter_by_question_set(df, st.session_state.question_set)
        
        # Exibir estatísticas dos dados pré-processados se disponíveis
        if st.session_state.question_set == "8 questões":
            show_preprocessed_stats(df)
        
        df_f = filters_ui(df)

        metrics = compute_metrics(df_f, goal)

        cols = st.columns(4)
        cols[0].metric("N respostas (filtrado)", len(df_f))
        cols[1].metric("Meta (goal)", f"{goal:.1f}")
        if metrics["satisfaction"] is not None:
            cols[2].metric("Satisfação média", f"{metrics['satisfaction']:.2f}")
        cols[3].metric("Dimensões", len(DIMENSIONS))

        # Radar chart of dimensions
        st.subheader("Radar por Dimensão")
        r_vals = [metrics["dimensions"][d]["mean"] if metrics["dimensions"][d]["mean"] is not None else 0 for d in DIMENSIONS.keys()]
        radar_cat = list(DIMENSIONS.keys())
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=r_vals, theta=radar_cat, fill="toself", name="Média"))
        fig.update_layout(
            polar=dict(radialaxis=dict(
                visible=True, 
                range=[1, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1', '2', '3', '4', '5']
            )),
            showlegend=False,
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ===== Novo layout de Insights =====
        # CSS moderno para badges e cards
        st.markdown(
            """
            <style>
            /* Variáveis CSS para tema moderno */
            :root {
                --primary-blue: #2563eb;
                --primary-blue-light: #3b82f6;
                --success-green: #10b981;
                --warning-orange: #f59e0b;
                --danger-red: #ef4444;
                --neutral-50: #f8fafc;
                --neutral-100: #f1f5f9;
                --neutral-200: #e2e8f0;
                --neutral-300: #cbd5e1;
                --neutral-400: #94a3b8;
                --neutral-500: #64748b;
                --neutral-600: #475569;
                --neutral-700: #334155;
                --neutral-800: #1e293b;
                --neutral-900: #0f172a;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
                --border-radius: 12px;
                --border-radius-sm: 8px;
            }
            
            .badge { 
                display: inline-block; 
                padding: 4px 12px; 
                border-radius: 20px; 
                font-size: 12px; 
                font-weight: 600;
                color: #ffffff; 
                margin-left: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: var(--shadow-sm);
            }
            .badge-green { 
                background: linear-gradient(135deg, var(--success-green), #059669);
                border: 1px solid rgba(16, 185, 129, 0.2);
            }
            .badge-orange { 
                background: linear-gradient(135deg, var(--warning-orange), #d97706);
                border: 1px solid rgba(245, 158, 11, 0.2);
            }
            .badge-red { 
                background: linear-gradient(135deg, var(--danger-red), #dc2626);
                border: 1px solid rgba(239, 68, 68, 0.2);
            }
            
            .card { 
                border: 1px solid var(--neutral-200); 
                border-radius: var(--border-radius); 
                padding: 20px 24px; 
                background: linear-gradient(135deg, #ffffff, var(--neutral-50));
                margin-bottom: 16px;
                box-shadow: var(--shadow-md);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
                border-color: var(--primary-blue-light);
            }
            .card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, var(--primary-blue), var(--primary-blue-light));
                border-radius: var(--border-radius) var(--border-radius) 0 0;
            }
            
            .item-row { 
                display: flex; 
                align-items: center; 
                justify-content: space-between; 
                gap: 12px;
                margin-bottom: 8px;
            }
            .item-name { 
                font-size: 0.95rem; 
                font-weight: 500;
                color: var(--neutral-700);
                line-height: 1.4;
            }
            .item-mean { 
                font-weight: 700; 
                font-size: 1.1rem;
                color: var(--neutral-800);
                background: var(--neutral-100);
                padding: 4px 8px;
                border-radius: var(--border-radius-sm);
                min-width: 50px;
                text-align: center;
            }
            .small { 
                font-size: 0.875rem; 
                color: var(--neutral-500);
                font-weight: 500;
                margin-bottom: 12px;
            }
            
            .dot { 
                display: inline-block; 
                width: 12px; 
                height: 12px; 
                border-radius: 50%; 
                margin-left: 8px; 
                vertical-align: middle;
                box-shadow: var(--shadow-sm);
                border: 2px solid #ffffff;
            }
            
            .progress-bar {
                height: 8px;
                background: var(--neutral-200);
                border-radius: 4px;
                overflow: hidden;
                margin: 8px 0;
                box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
            }
            .progress-fill {
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s ease;
                background: linear-gradient(90deg, var(--primary-blue), var(--primary-blue-light));
            }
            .progress-fill.green {
                background: linear-gradient(90deg, var(--success-green), #059669);
            }
            .progress-fill.orange {
                background: linear-gradient(90deg, var(--warning-orange), #d97706);
            }
            .progress-fill.red {
                background: linear-gradient(90deg, var(--danger-red), #dc2626);
            }
            
            .sugg { 
                color: var(--neutral-600); 
                font-size: 0.875rem; 
                margin-top: 8px;
                line-height: 1.5;
                background: var(--neutral-50);
                padding: 8px 12px;
                border-radius: var(--border-radius-sm);
                border-left: 3px solid var(--primary-blue-light);
            }
            .sugg i { 
                color: var(--warning-orange);
                margin-right: 6px;
            }
            
            /* Status indicators */
            .status-excellent { color: var(--success-green); }
            .status-good { color: var(--warning-orange); }
            .status-poor { color: var(--danger-red); }
            
            /* Alert styling */
            .alert-warning {
                background: linear-gradient(135deg, #fef3c7, #fde68a);
                border: 1px solid #f59e0b;
                border-radius: var(--border-radius);
                padding: 16px 20px;
                margin: 16px 0;
                color: var(--neutral-800);
                font-weight: 500;
            }
            
            /* Tab styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
            }
            .stTabs [data-baseweb="tab"] {
                background: var(--neutral-100);
                border-radius: var(--border-radius-sm);
                padding: 8px 16px;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .stTabs [aria-selected="true"] {
                background: var(--primary-blue);
                color: white;
                box-shadow: var(--shadow-sm);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        # Linha de atenção
        pri, aco, bons = metrics["insights"]["criticos"], metrics["insights"]["acoes"], metrics["insights"]["bons"]
        all_items_stats = []
        for dim_name, its in DIMENSIONS.items():
            for it in its:
                if it in metrics["items"]:
                    all_items_stats.append((it, dim_name, metrics["items"][it]["mean"]))
        if all_items_stats:
            worst_item, worst_dim, worst_mean = min(all_items_stats, key=lambda x: x[2])
            gap = float(goal) - float(worst_mean)
            gap_txt = f"(gap {gap:.2f})" if gap > 0 else ""
            st.markdown(
                f"""
                <div class="alert-warning">
                    <strong>⚠️ Atenção:</strong> {len(pri)+len(aco)} itens abaixo da meta — {len(pri)} críticos. 
                    <br><strong>Pior desempenho:</strong> [{worst_dim}] {worst_item} com média {worst_mean:.2f} {gap_txt}.
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.subheader("Insights Automáticos")
        
        tab_overview, tab_list, tab_corr = st.tabs(["Visão geral", "Lista completa", "Ações coordenadas"]) 
        
        # --- Aba: Visão Geral (cartões por dimensão com 2 itens de menor média) ---
        with tab_overview:
            cols_dim = st.columns(3)
            for idx, dim_name in enumerate(DIMENSIONS.keys()):
                with cols_dim[idx % 3]:
                    dim_mean = metrics["dimensions"][dim_name]["mean"] if dim_name in metrics["dimensions"] else None
                    # meta por dimensão (se existir)
                    try:
                        dim_goal = float((prefs or {}).get("goal_by_dimension", {}).get(dim_name, goal)) if isinstance(prefs, dict) else float(goal)
                    except Exception:
                        dim_goal = float(goal)
                    # farol
                    color = "#10b981" if (dim_mean is not None and dim_mean >= dim_goal) else ("#f59e0b" if (dim_mean is not None and dim_goal - dim_mean <= 0.5) else "#ef4444")
                    status_class = "status-excellent" if (dim_mean is not None and dim_mean >= dim_goal) else ("status-good" if (dim_mean is not None and dim_goal - dim_mean <= 0.5) else "status-poor")
                    st.markdown(
                        f"<div class='card'>"
                        f"<div class='item-row'><strong>{dim_name}</strong>"
                        f"<span class='dot' style='background:{color}'></span></div>"
                        f"<div class='small'>Média <span class='{status_class}'>{(dim_mean if dim_mean is not None else 0):.2f}</span> / Meta {dim_goal:.1f}</div>",
                        unsafe_allow_html=True,
                    )
                    # 2 itens com menor média da dimensão
                    it_means = [(it, metrics["items"][it]["mean"]) for it in DIMENSIONS[dim_name] if it in metrics["items"]]
                    it_means.sort(key=lambda x: (x[1] is None, x[1]))
                    lows = it_means[:2] if len(it_means) >= 2 else it_means
                    for it, mean in lows:
                        pct = 0.0
                        try:
                            pct = max(0.0, min(1.0, float(mean) / 5.0))
                        except Exception:
                            pct = 0.0
                        
                        # Determinar classe da barra de progresso
                        progress_class = "green" if (mean is not None and mean >= dim_goal) else ("orange" if (mean is not None and dim_goal - mean <= 0.5) else "red")
                        
                        bar_html = f"""
                        <div class='progress-bar'>
                            <div class='progress-fill {progress_class}' style='width:{int(pct*100)}%;'></div>
                        </div>
                        """
                        st.markdown(
                            f"<div class='item-row'><span class='item-name'>{it}</span><span class='item-mean'>{(mean if mean is not None else 0):.2f}</span></div>"
                            + bar_html,
                            unsafe_allow_html=True,
                        )
                        # micro-sugestões
                        gap = None
                        try:
                            gap = (dim_goal - float(mean)) if (mean is not None) else None
                        except Exception:
                            gap = None
                        suggs = []
                        low_gap = (gap is not None and gap >= 0.2)
                        it_lower = it.lower()
                        if "tempo" in it_lower or "agilidade" in it_lower:
                            suggs.append("Ajustar SLAs ou priorização de atendimentos")
                        if "instru" in it_lower or "guia" in it_lower or "manual" in it_lower:
                            suggs.append("Melhorar instruções de uso com exemplos passo a passo")
                        if "sistema" in it_lower or "plataforma" in it_lower or "portal" in it_lower:
                            suggs.append("Revisar UX e reduzir cliques para concluir tarefas")
                        if "chatbot" in it_lower or "ia" in it_lower:
                            suggs.append("Aprimorar respostas do chatbot com base em dúvidas frequentes")
                        if not suggs:
                            suggs = [
                                "Treinamento rápido para equipe e usuários",
                                "Padronizar mensagens e fluxos",
                                "Revisar gargalos e otimizar etapas críticas",
                            ]
                        if low_gap:
                            st.markdown("<div class='sugg'>" + "<br>".join([f"• {s}" for s in suggs[:2]]) + "</div>", unsafe_allow_html=True)
                        # micro-sugestões por item
                        try:
                            goal_dim = float((prefs or {}).get("goal_by_dimension", {}).get(dim_name, goal)) if isinstance(prefs, dict) else float(goal)
                        except Exception:
                            goal_dim = float(goal)
                        sugs = []
                        it_lower = it.lower()
                        if any(k in it_lower for k in ["tempo", "agilidade", "prazo", "resposta"]):
                            sugs.extend(["Ajustar tempos de resposta", "Automatizar etapas críticas"])
                        if any(k in it_lower for k in ["instru", "guia", "manual", "orienta", "informac"]):
                            sugs.extend(["Melhorar instruções e material de apoio", "Revisar textos da interface"])
                        if any(k in it_lower for k in ["sistema", "servi", "acesso", "localizar", "encontrar", "navega"]):
                            sugs.extend(["Revisar arquitetura de informação", "Treinamento de uso do sistema"])
                        if any(k in it_lower for k in ["real", "chatbot", "ia", "intera", "atendimento"]):
                            sugs.extend(["Expandir canais em tempo real", "Treinar chatbot"])
                        # base gap
                        try:
                            gap = max(0.0, float(goal_dim) - float(mean))
                        except Exception:
                            gap = 0.0
                        if gap >= 1.0:
                            sugs.insert(0, "Plano de ação com responsáveis e prazos")
                            sugs.append("Treinamento com simulações práticas")
                        elif gap > 0:
                            sugs.append("Ajustes de processo e comunicação")
                        if not sugs:
                            sugs = ["Entrevistar usuários", "Definir melhoria incremental e medir impacto"]
                        for s in sugs[:3]:
                            st.markdown(f"<div class='sugg'><i>💡 {s}</i></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # --- Aba: Lista completa (mantém agrupamento em 3 colunas com filtro) ---
        with tab_list:
            insight_options = {"Críticos": "criticos", "Abaixo da meta": "acoes", "Bons (≥ meta)": "bons"}
            sel = st.multiselect("Filtrar tipos de insight", list(insight_options.keys()), default=list(insight_options.keys()))
            only_pri = st.checkbox("Mostrar apenas críticos", value=False, key="only_pri_list")
            if only_pri:
                sel = ["Críticos"]
            selected_keys = [insight_options[k] for k in sel]
        
            c1, c2, c3 = st.columns(3)
        
            def render_list(container, items, title, color):
                container.markdown(f"**{title}**")
                if not items:
                    container.write("—")
                    return
                for item, dim, mean in items:
                    container.write(f"- **[{dim}]** {item} → média **{mean:.2f}**")
        
            if "criticos" in selected_keys:
                render_list(c1, pri, "🔴 Críticos (muito abaixo da meta)", "red")
            else:
                c1.write("—")
            if "acoes" in selected_keys:
                render_list(c2, aco, "🟠 Ações necessárias (abaixo da meta)", "orange")
            else:
                c2.write("—")
            if "bons" in selected_keys:
                render_list(c3, bons, "🟢 Itens com bom desempenho (≥ meta)", "green")
            else:
                c3.write("—")
        
        # --- Aba: Ações coordenadas (correlação por dimensão) ---
        with tab_corr:
            st.caption("Sugestões de sequências de ação com base em correlações entre itens de uma mesma dimensão.")
            with st.expander("Ver correlações e sequências sugeridas", expanded=False):
                threshold = st.slider("Correlação mínima (ρ)", 0.3, 0.9, 0.5, 0.05, key="corr_thr_tabs")
                max_pairs = st.number_input("Máximo de pares por dimensão", min_value=1, max_value=10, value=3, step=1, key="corr_max_pairs_tabs")
                for dim_name, its in DIMENSIONS.items():
                    available = [it for it in its if it in df_f.columns]
                    if len(available) < 2:
                        continue
                    num_df = pd.DataFrame({it: normalize_likert(df_f[it]) for it in available})
                    if num_df.dropna(how="all").shape[1] < 2:
                        continue
                    corr = num_df.corr(method="spearman")
                    pairs = []
                    for i, it1 in enumerate(available):
                        for it2 in available[i+1:]:
                            try:
                                rho = float(corr.loc[it1, it2])
                            except Exception:
                                rho = np.nan
                            if pd.notna(rho) and rho >= threshold:
                                m1 = metrics["items"][it1]["mean"]
                                m2 = metrics["items"][it2]["mean"]
                                shortfall = max(0.0, float(goal) - float(m1)) + max(0.0, float(goal) - float(m2))
                                pairs.append((it1, it2, rho, shortfall))
                        if not pairs:
                            continue
                        pairs.sort(key=lambda x: (-x[3], -x[2]))
                        st.markdown(f"**{dim_name}**")
                        for it1, it2, rho, shortfall in pairs[:int(max_pairs)]:
                            st.write(f"- {it1} ↔ {it2} (ρ≈{rho:.2f}). Sequência sugerida: atuar em {it1} e, em seguida, reforçar {it2}. Déficit conjunto: {shortfall:.2f}.")
        # ===== Fim do novo layout =====
        # Bloco de frequências por item removido (poderá voltar futuramente, agora substituído pela Análise Detalhada).

# -----------------------------
# Page: Análise Detalhada
# -----------------------------
if page == "Análise Detalhada":
    st.header("🔬 Análise Estatística Detalhada")
    
    if st.session_state.data is None:
        st.info("Carregue dados na página **Upload de Arquivo** primeiro.")
    else:
        df = st.session_state.data.copy()
        # Aplicar filtro de conjunto de questões
        df = filter_by_question_set(df, st.session_state.question_set)
        df_f = filters_ui(df)
        
        # Ensure global variables are updated for current question set
        update_global_variables(st.session_state.question_set)
        
        # Prepare data for analysis
        df_analysis = prepare_data_for_analysis(df_f)
        
        st.info(f"📊 **Analisando:** {len(df_analysis)} respostas válidas | Dimensões: {list(DIMENSIONS.keys())}")
        
        # Tabs for different analyses
        tab1, tab2 = st.tabs([ 
            "🎯 Regressões vs Satisfação", 
            "📊 Correlações e Associações"
        ])
        
        # Tab 1: Regressions by Dimension
        # Tab 1: Satisfaction Regression
        with tab1:
            st.subheader("Regressões das Dimensões vs Satisfação Geral")
            st.caption("Análise de como cada dimensão influencia a satisfação geral")
            
            if SAT_FIELD in df_analysis.columns:
                if st.button("🎯 Executar Análise de Satisfação", key="run_satisfaction"):
                    st.success("✅ Análise de satisfação executada")
                    
                    # Prepare data - only use score columns that exist in the DataFrame
                    available_score_cols = [f'{dim}_score' for dim in DIMENSIONS.keys() if f'{dim}_score' in df_analysis.columns]
                    if not available_score_cols:
                        st.warning("Nenhuma coluna de score encontrada. Verifique se os dados foram processados corretamente.")
                        st.stop()
                    
                    satisfaction_data = df_analysis[[SAT_FIELD] + available_score_cols].dropna()
                    
                    if len(satisfaction_data) > 10:
                        # Multiple regression
                        X = satisfaction_data[available_score_cols]
                        y = satisfaction_data[SAT_FIELD]
                        
                        X_with_const = sm.add_constant(X)
                        model = sm.OLS(y, X_with_const).fit()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📊 Modelo de Satisfação")
                            st.write(f"**R² Ajustado:** {model.rsquared_adj:.3f}")
                            st.write(f"**F-statístico:** {model.fvalue:.2f}")
                            st.write(f"**p-valor (F):** {model.f_pvalue:.4f}")
                            st.write(f"**Observações:** {int(model.nobs)}")
                        
                        with col2:
                            st.markdown("#### 📈 Influência das Dimensões")
                            coef_df = pd.DataFrame({
                                'Dimensão': ['Intercepto'] + list(DIMENSIONS.keys()),
                                'Coeficiente': model.params.values,
                                'p-valor': model.pvalues.values
                            })
                            
                            # Sort by coefficient (excluding intercept)
                            coef_df_sorted = coef_df.iloc[1:].sort_values('Coeficiente', ascending=False)
                            
                            for _, row in coef_df_sorted.iterrows():
                                significance = "✅" if row['p-valor'] < 0.05 else "❌"
                                st.write(f"{significance} **{row['Dimensão']}**: β = {row['Coeficiente']:.3f}")
                        
                        # Visualization
                        fig = px.bar(
                            coef_df_sorted, 
                            x='Coeficiente', 
                            y='Dimensão',
                            title="Influência das Dimensões na Satisfação Geral",
                            color='p-valor',
                            color_continuous_scale='RdYlGn_r'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Interpretation
                        st.markdown("#### 💡 Interpretação")
                        most_important = coef_df_sorted.iloc[0]
                        least_important = coef_df_sorted.iloc[-1]
                        
                        st.write(f"**Dimensão mais importante:** {most_important['Dimensão']} (β = {most_important['Coeficiente']:.3f})")
                        st.write(f"**Dimensão menos importante:** {least_important['Dimensão']} (β = {least_important['Coeficiente']:.3f})")
                    
                    else:
                        st.error("❌ Dados insuficientes para análise de satisfação.")
            else:
                st.warning("⚠️ Campo de satisfação não encontrado nos dados.")
        
        # Tab 2: Correlations and Associations
        with tab2:
            st.subheader("Correlações e Associações")
            st.caption("Análise de correlações entre variáveis e testes de associação")
            
            if st.button("📊 Executar Análise de Correlações", key="run_correlations"):
                st.success("✅ Análise de correlações executada")
                
                # Prepare correlation data - only use score columns that exist
                available_score_cols = [f'{dim}_score' for dim in DIMENSIONS.keys() if f'{dim}_score' in df_analysis.columns]
                if not available_score_cols:
                    st.warning("Nenhuma coluna de score encontrada para análise de correlações.")
                    st.stop()
                
                corr_data = df_analysis[available_score_cols].dropna()
                
                if len(corr_data) > 10:
                    # Correlation matrix
                    correlation_matrix = corr_data.corr()
                    
                    # Heatmap
                    fig = px.imshow(
                        correlation_matrix,
                        text_auto=True,
                        aspect="auto",
                        title="Matriz de Correlação entre Dimensões",
                        color_continuous_scale='RdBu_r'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Detailed correlations
                    st.markdown("#### 📈 Correlações Detalhadas")
                    
                    correlations = []
                    for i, dim1 in enumerate(DIMENSIONS.keys()):
                        for j, dim2 in enumerate(DIMENSIONS.keys()):
                            if i < j:  # Avoid duplicates
                                corr_val = correlation_matrix.loc[f'{dim1}_score', f'{dim2}_score']
                                correlations.append({
                                    'Dimensão 1': dim1,
                                    'Dimensão 2': dim2,
                                    'Correlação': corr_val,
                                    'Intensidade': 'Forte' if abs(corr_val) > 0.7 else 'Moderada' if abs(corr_val) > 0.3 else 'Fraca'
                                })
                    
                    corr_df = pd.DataFrame(correlations)
                    corr_df = corr_df.sort_values('Correlação', key=abs, ascending=False)
                    
                    st.dataframe(corr_df.style.format({'Correlação': '{:.3f}'}), use_container_width=True)
                    
                    # Categorical associations
                    st.markdown("#### 🔗 Associações com Variáveis Categóricas")
                    
                    # Sex vs Dimensions
                    if PROFILE_FIELDS["Sexo"] in df_analysis.columns:
                        st.markdown("##### Associação: Sexo vs Dimensões")
                        
                        available_score_cols = [f'{dim}_score' for dim in DIMENSIONS.keys() if f'{dim}_score' in df_analysis.columns]
                        if not available_score_cols:
                            st.warning("Nenhuma coluna de score encontrada para análise por sexo.")
                        else:
                            sex_dim_data = df_analysis[[PROFILE_FIELDS["Sexo"]] + available_score_cols].dropna()
                            
                            if len(sex_dim_data) > 10:
                                # ANOVA for each dimension
                                for dim in available_score_cols:
                                    dim_name = dim.replace('_score', '')
                                    groups = [group[dim].dropna() for name, group in sex_dim_data.groupby(PROFILE_FIELDS["Sexo"])]
                                    if len(groups) > 1 and all(len(g) > 0 for g in groups):
                                        f_stat, p_val = stats.f_oneway(*groups)
                                        significance = "✅" if p_val < 0.05 else "❌"
                                        st.write(f"{significance} **{dim_name}**: F = {f_stat:.3f}, p = {p_val:.4f}")
                    
                    # Servidor Público vs Dimensions
                    # Handle different field names for public servant field
                    servidor_field = PROFILE_FIELDS.get("Servidor Público") or PROFILE_FIELDS.get("Funcionario_Publico")
                    if servidor_field and servidor_field in df_analysis.columns:
                        st.markdown("##### Associação: Servidor Público vs Dimensões")
                        
                        available_score_cols = [f'{dim}_score' for dim in DIMENSIONS.keys() if f'{dim}_score' in df_analysis.columns]
                        if not available_score_cols:
                            st.warning("Nenhuma coluna de score encontrada para análise de servidor público.")
                        else:
                            serv_dim_data = df_analysis[[servidor_field] + available_score_cols].dropna()
                            
                            if len(serv_dim_data) > 10:
                                for dim in available_score_cols:
                                    dim_name = dim.replace('_score', '')
                                    groups = [group[dim].dropna() for name, group in serv_dim_data.groupby(servidor_field)]
                                    if len(groups) > 1 and all(len(g) > 0 for g in groups):
                                        f_stat, p_val = stats.f_oneway(*groups)
                                        significance = "✅" if p_val < 0.05 else "❌"
                                        st.write(f"{significance} **{dim_name}**: F = {f_stat:.3f}, p = {p_val:.4f}")
                
                else:
                    st.error("❌ Dados insuficientes para análise de correlações.")

# -----------------------------
# Page: Perfil
# -----------------------------
if page == "Perfil":
    st.header("👤 Perfil do Usuário")
    if st.session_state.auth["logged_in"]:
        st.write(f"**E-mail:** {st.session_state.auth['email']}")
    else:
        st.info("Modo demo: sem autenticação real.")

    st.subheader("Histórico de Uploads")
    if st.session_state.auth["logged_in"]:
        rec = st.session_state.dm.get_user_uploads(st.session_state.auth["email"])
        if rec:
            st.dataframe(pd.DataFrame([rec.model_dump()]))
        elif st.session_state.uploads:
            st.dataframe(pd.DataFrame(st.session_state.uploads))
        else:
            st.write("Nenhum upload registrado ainda.")
    else:
        st.write("Nenhum upload (modo demo).")

    st.subheader("Análise de Perfil")
    if "data" in st.session_state and st.session_state.data is not None:
        df = st.session_state.data.copy()
        # Aplicar filtro de conjunto de questões
        df = filter_by_question_set(df, st.session_state.question_set)
        df_filtered = filters_ui(df)
        df_analysis = prepare_data_for_analysis(df_filtered)

        if df_analysis.empty:
            st.warning("Nenhum dado disponível após a aplicação dos filtros.")
        else:
            st.info(f"📊 **Analisando:** {len(df_analysis)} respostas válidas (após filtros)")
            
            # Iterate over each profile question
            for profile_key, profile_question in PROFILE_FIELDS.items():
                if profile_question in df_analysis.columns:
                    st.markdown(f"---")
                    st.markdown(f"### {profile_question}")
                    
                    # --- Métricas de resumo ---
                    col1, col2, col3 = st.columns(3)
                    total_responses = df_analysis[profile_question].count()
                    unique_responses = df_analysis[profile_question].nunique()
                    
                    with col1:
                        st.metric("Total de Respostas", total_responses)
                    with col2:
                        st.metric("Opções Distintas", unique_responses)
                    with col3:
                        # Frequency table
                        freq_table = df_analysis[profile_question].value_counts().reset_index()
                        freq_table.columns = ['Opção', 'Contagem']
                        st.dataframe(freq_table, use_container_width=True, height=150)

                    # --- Histograma (largura total) ---
                    st.markdown("##### Distribuição das Respostas")
                    try:
                        # Tratamento especial para idade - categorização por quartis
                        if 'idade' in profile_question.lower() or 'age' in profile_question.lower():
                            # Criar categorias por quartis para idade
                            age_data = df_analysis[profile_question].dropna()
                            if len(age_data) > 0:
                                quartiles = age_data.quantile([0.25, 0.5, 0.75])
                                
                                def categorize_age(age):
                                    if pd.isna(age):
                                        return 'Não informado'
                                    elif age <= quartiles[0.25]:
                                        return f'Q1: ≤{quartiles[0.25]:.0f} anos'
                                    elif age <= quartiles[0.5]:
                                        return f'Q2: {quartiles[0.25]:.0f}-{quartiles[0.5]:.0f} anos'
                                    elif age <= quartiles[0.75]:
                                        return f'Q3: {quartiles[0.5]:.0f}-{quartiles[0.75]:.0f} anos'
                                    else:
                                        return f'Q4: >{quartiles[0.75]:.0f} anos'
                                
                                df_analysis_temp = df_analysis.copy()
                                df_analysis_temp[f'{profile_question}_quartil'] = df_analysis_temp[profile_question].apply(categorize_age)
                                
                                hist_fig = px.histogram(
                                    df_analysis_temp.dropna(subset=[f'{profile_question}_quartil']), 
                                    x=f'{profile_question}_quartil',
                                    title=f"Distribuição por Quartis - '{profile_question}'",
                                    text_auto=True
                                )
                                hist_fig.update_layout(bargap=0.2, xaxis_title="Quartis de Idade")
                                st.plotly_chart(hist_fig, use_container_width=True)
                        else:
                            hist_fig = px.histogram(
                                df_analysis.dropna(subset=[profile_question]), 
                                x=profile_question,
                                title=f"Distribuição de '{profile_question}'",
                                text_auto=True
                            )
                            hist_fig.update_layout(bargap=0.2)
                            st.plotly_chart(hist_fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Não foi possível gerar o histograma: {e}")

                    # --- Radar Chart (largura total) ---
                    st.markdown("##### Análise por Dimensão (Radar)")
                    
                    # Para idade, usar quartis; para outros, usar valores originais
                    if 'idade' in profile_question.lower() or 'age' in profile_question.lower():
                        age_data = df_analysis[profile_question].dropna()
                        if len(age_data) > 0:
                            quartiles = age_data.quantile([0.25, 0.5, 0.75])
                            
                            def categorize_age(age):
                                if pd.isna(age):
                                    return 'Não informado'
                                elif age <= quartiles[0.25]:
                                    return f'Q1: ≤{quartiles[0.25]:.0f} anos'
                                elif age <= quartiles[0.5]:
                                    return f'Q2: {quartiles[0.25]:.0f}-{quartiles[0.5]:.0f} anos'
                                elif age <= quartiles[0.75]:
                                    return f'Q3: {quartiles[0.5]:.0f}-{quartiles[0.75]:.0f} anos'
                                else:
                                    return f'Q4: >{quartiles[0.75]:.0f} anos'
                            
                            df_analysis_temp = df_analysis.copy()
                            df_analysis_temp[f'{profile_question}_quartil'] = df_analysis_temp[profile_question].apply(categorize_age)
                            options = df_analysis_temp[f'{profile_question}_quartil'].dropna().unique()
                            analysis_field = f'{profile_question}_quartil'
                            df_for_radar = df_analysis_temp
                        else:
                            options = []
                            analysis_field = profile_question
                            df_for_radar = df_analysis
                    else:
                        options = df_analysis[profile_question].dropna().unique()
                        analysis_field = profile_question
                        df_for_radar = df_analysis
                    
                    # Limitar para não poluir o gráfico
                    if len(options) > 1 and len(options) < 8:
                        
                        radar_fig = go.Figure()
                        
                        dimension_score_fields = [f'{dim}_score' for dim in DIMENSIONS.keys() if f'{dim}_score' in df_for_radar.columns]
                        dimension_names = [dim for dim in DIMENSIONS.keys() if f'{dim}_score' in df_for_radar.columns]

                        if dimension_score_fields:
                            for option in sorted(options):
                                df_option = df_for_radar[df_for_radar[analysis_field] == option]
                                
                                # Calculate mean for each dimension score for this group
                                # Keep Likert scale (1-5)
                                mean_scores_likert = df_option[dimension_score_fields].mean().values
                                mean_scores = [score if not np.isnan(score) else 1 for score in mean_scores_likert]
                                
                                radar_fig.add_trace(go.Scatterpolar(
                                    r=mean_scores,
                                    theta=dimension_names,
                                    fill='toself',
                                    name=str(option)
                                ))
                            
                            radar_fig.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[1, 5], # Escala de 1 a 5
                                        tickvals=[1, 2, 3, 4, 5],
                                        ticktext=['1', '2', '3', '4', '5']
                                    )
                                ),
                                showlegend=True,
                                title=f"Radar de Escala 1-5 - '{profile_question}'"
                            )
                            st.plotly_chart(radar_fig, use_container_width=True)
                        else:
                            st.warning(f"As pontuações das dimensões não foram calculadas. Impossível gerar o gráfico de radar.")

                    elif len(options) >= 8:
                        st.info(f"Muitas opções ({len(options)}) para exibir o gráfico de radar. O gráfico foi omitido para maior clareza.")
                    else:
                        st.info("Não há opções suficientes para uma comparação no gráfico de radar.")

    else:
        st.info("Faça o upload de um arquivo para ver a análise de perfil.")


# -----------------------------
# Page: Portal Transparência
# -----------------------------
if page == "Portal Transparência":
    st.header("🏛️ Portal Transparência - Dashboard de Qualidade")
    
    # Carregar dados específicos para Portal Transparência
    if st.session_state.question_set == "8 questões":
        if hasattr(st.session_state, 'uploaded_8q') and st.session_state.uploaded_8q is not None:
            try:
                df_transp = read_csv(st.session_state.uploaded_8q)
                data_source_name = st.session_state.uploaded_8q.name
            except Exception as e:
                st.error(f"Erro ao carregar arquivo: {e}")
                df_transp = None
        else:
            try:
                # Usar vírgula como separador para o arquivo basetransp.csv
                df_transp = pd.read_csv(os.path.join("sample_data", "basetransp.csv"), sep=",", encoding="utf-8")
                data_source_name = "basetransp.csv (padrão)"
            except Exception as e:
                st.error(f"Erro ao carregar basetransp.csv: {e}")
                df_transp = None
    else:
        df_transp = st.session_state.data
        data_source_name = st.session_state.data_source
    
    if df_transp is None:
        st.warning("⚠️ Nenhum dado disponível. Configure o conjunto de questões para '8 questões' ou faça upload de um arquivo.")
    else:
        st.info(f"📊 **Analisando dados de:** {data_source_name}")
        
        # Processar dados: remover linhas em branco e agrupar
        df_transp = df_transp.dropna(how='all')  # Remove linhas completamente vazias
        df_transp = df_transp.reset_index(drop=True)  # Reindexar após remoção
        
        # Definir as 8 questões específicas do Portal Transparência
        # Usar os textos reais das colunas do CSV
        questoes_portal = {
            "O Portal é fácil de usar.": "O Portal é fácil de usar",
            "É fácil localizar os dados e as informações no Portal.": "É fácil localizar os dados e as informações no Portal", 
            "A navegação pelo Portal é intuitiva.": "A navegação pelo Portal é intuitiva",
            "O Portal funciona sem falhas.": "O Portal funciona sem falhas",
            "As informações são fáceis de entender.": "As informações são fáceis de entender",
            "As informações são precisas.": "As informações são precisas",
            "As informações disponibilizadas estão atualizadas.": "As informações disponibilizadas estão atualizadas",
            "Consigo obter o que preciso no menor tempo possível.": "Consigo obter o que preciso no menor tempo possível",
            "Qual o seu nível de satisfação com o Portal da Transparência do RS?": "Nível de satisfação com o Portal da Transparência do RS"
        }
        
        # Mapeamento da escala Likert (1-5)
        likert_mapping = {
            "Discordo totalmente": 1,
            "Discordo": 2, 
            "Neutro": 3,
            "Concordo": 4,
            "Concordo totalmente": 5,
            # Para satisfação
            "Muito insatisfeito": 1,
            "Insatisfeito": 2,
            "Neutro": 3,
            "Satisfeito": 4,
            "Muito satisfeito": 5
        }
        
        # Aplicar mapeamento numérico
        for col in df_transp.columns:
            if col in questoes_portal.keys():
                df_transp[col] = df_transp[col].map(likert_mapping).fillna(df_transp[col])
        
        # Aplicar filtros
        df_filtered = filters_ui(df_transp)
        
        # Calcular médias para cada questão
        medias_questoes = {}
        for questao_col, questao_desc in questoes_portal.items():
            if questao_col in df_filtered.columns:
                media = df_filtered[questao_col].mean()
                medias_questoes[questao_desc] = media if not pd.isna(media) else 0
        
        # Header com métricas principais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total de Respostas", len(df_filtered))
        with col2:
            st.metric("🎯 Meta Estabelecida", f"{goal:.1f}")
        with col3:
            if "Nível de satisfação com o Portal da Transparência do RS" in medias_questoes:
                satisfacao_media = medias_questoes["Nível de satisfação com o Portal da Transparência do RS"]
                st.metric("😊 Satisfação Média", f"{satisfacao_media:.2f}")
            else:
                st.metric("📋 Questões Analisadas", "8")
        with col4:
            abaixo_meta = sum(1 for media in medias_questoes.values() if media < goal)
            st.metric("⚠️ Abaixo da Meta", f"{abaixo_meta}/{len(medias_questoes)}")
        
        st.markdown("---")
        
        # Dashboard principal com duas colunas
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📈 Visão Geral das 8 Questões")
            
            # Gráfico de radar
            if medias_questoes:
                questoes_sistema = [q for q in medias_questoes.keys() if "satisfação" not in q.lower()]
                r_vals = [medias_questoes[q] for q in questoes_sistema]
                
                if questoes_sistema and r_vals:
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=r_vals, 
                        theta=questoes_sistema, 
                        fill="toself", 
                        name="Média Atual",
                        line_color='#1f77b4'
                    ))
                    
                    # Adicionar linha da meta
                    meta_vals = [goal] * len(questoes_sistema)
                    fig_radar.add_trace(go.Scatterpolar(
                        r=meta_vals, 
                        theta=questoes_sistema, 
                        fill=None, 
                        name="Meta",
                        line=dict(color='red', dash='dash', width=2)
                    ))
                    
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(
                            visible=True, 
                            range=[1, 5],
                            tickvals=[1, 2, 3, 4, 5],
                            ticktext=['1', '2', '3', '4', '5']
                        )),
                        showlegend=True,
                        height=500,
                        title="Comparação: Desempenho Atual vs Meta"
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                else:
                    st.warning("⚠️ Não há questões válidas para exibir no gráfico de radar.")
            else:
                st.warning("⚠️ Não há dados suficientes para exibir o gráfico de radar. Verifique se o arquivo contém as questões esperadas.")
            
            # Gráfico de barras horizontal
            st.subheader("📊 Ranking das Questões")
            
            dim_data = []
            for questao, media in medias_questoes.items():
                if "satisfação" not in questao.lower():  # Excluir satisfação do ranking
                    dim_data.append({
                        'Questão': questao[:30] + "..." if len(questao) > 30 else questao,
                        'Média': media,
                        'Status': 'Acima da Meta' if media >= goal else 'Abaixo da Meta'
                    })
            
            if dim_data:  # Verificar se há dados antes de criar o DataFrame
                try:
                    df_dim = pd.DataFrame(dim_data)
                    # Verificar se o DataFrame tem dados e a coluna 'Média' existe
                    if not df_dim.empty and 'Média' in df_dim.columns:
                        df_dim = df_dim.sort_values('Média', ascending=True)
                        
                        # Criar o gráfico apenas se temos dados válidos
                        fig_bar = px.bar(
                            df_dim, 
                            x='Média', 
                            y='Questão', 
                            color='Status',
                            color_discrete_map={
                                'Acima da Meta': '#2ecc71',
                                'Abaixo da Meta': '#e74c3c'
                            },
                            orientation='h',
                            title="Desempenho por Questão"
                        )
                        fig_bar.add_vline(x=goal, line_dash="dash", line_color="red", 
                                         annotation_text=f"Meta: {goal}")
                        fig_bar.update_layout(height=400)
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.warning("⚠️ DataFrame criado mas sem dados válidos para o gráfico.")
                except Exception as e:
                    st.error(f"Erro ao criar DataFrame: {e}")
            else:
                st.warning("⚠️ Não há dados suficientes para gerar o gráfico de barras. Verifique se os dados foram carregados corretamente.")
        
        with col_right:
            st.subheader("🎯 Status das Questões")
            
            # Cards de status
            for questao, media in medias_questoes.items():
                if "satisfação" not in questao.lower():  # Excluir satisfação dos cards
                    if media >= goal:
                        status_color = "#d4edda"
                        status_icon = "✅"
                        status_text = "Meta Atingida"
                    else:
                        status_color = "#f8d7da"
                        status_icon = "⚠️"
                        status_text = "Abaixo da Meta"
                    
                    questao_short = questao[:25] + "..." if len(questao) > 25 else questao
                    st.markdown(f"""
                    <div style="
                        background-color: {status_color}; 
                        padding: 10px; 
                        border-radius: 5px; 
                        margin-bottom: 10px;
                        border-left: 4px solid {'#28a745' if media >= goal else '#dc3545'};
                    ">
                        <strong>{status_icon} {questao_short}</strong><br>
                        Média: <strong>{media:.2f}</strong><br>
                        <small>{status_text}</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Seção de Ações Sugeridas
        st.subheader("💡 Ações Sugeridas para Melhoria")
        st.write("Com base na análise das médias, aqui estão as ações recomendadas para cada questão:")
        
        # Definir ações por questão (baseado no acoesDash.docx.md)
        acoes_por_questao = {
            "O Portal é fácil de usar": {
                "titulo": "🎨 Melhorar Usabilidade",
                "acoes": [
                    "Implementar busca inteligente com filtros avançados e sugestões automáticas",
                    "Realizar testes de usabilidade com usuários reais para identificar pontos de fricção",
                    "Otimizar interface para dispositivos móveis com design responsivo",
                    "Adicionar tutoriais interativos e onboarding para novos usuários",
                    "Criar atalhos de teclado para usuários avançados"
                ]
            },
            "É fácil localizar os dados e as informações no Portal": {
                "titulo": "🔍 Facilitar Localização de Dados",
                "acoes": [
                    "Reorganizar categorização de dados por frequência de uso e relevância",
                    "Implementar sistema de tags e metadados para melhor organização",
                    "Criar mapa visual do portal com localização de informações",
                    "Desenvolver busca semântica que entenda sinônimos e contexto",
                    "Adicionar filtros inteligentes baseados no perfil do usuário"
                ]
            },
            "A navegação pelo Portal é intuitiva": {
                "titulo": "🧭 Aprimorar Navegação",
                "acoes": [
                    "Implementar breadcrumbs em todas as páginas para orientação",
                    "Criar menu de navegação contextual baseado na seção atual",
                    "Desenvolver sistema de navegação por abas para múltiplas consultas",
                    "Adicionar histórico de navegação e páginas visitadas recentemente",
                    "Implementar navegação por gestos em dispositivos touch"
                ]
            },
            "O Portal funciona sem falhas": {
                "titulo": "⚙️ Otimizar Funcionamento",
                "acoes": [
                    "Implementar monitoramento de performance em tempo real com alertas",
                    "Criar dashboard de status do sistema visível aos usuários",
                    "Estabelecer SLA de 99.9% de disponibilidade com compensações",
                    "Implementar sistema de cache inteligente para reduzir latência",
                    "Desenvolver testes automatizados de regressão e performance"
                ]
            },
            "As informações são fáceis de entender": {
                "titulo": "💡 Aumentar Clareza",
                "acoes": [
                    "Desenvolver glossário interativo de termos técnicos e jurídicos",
                    "Padronizar linguagem simples e acessível em todo o portal",
                    "Criar guias visuais e infográficos para processos complexos",
                    "Implementar sistema de ajuda contextual com tooltips explicativos",
                    "Adicionar exemplos práticos para cada tipo de informação"
                ]
            },
            "As informações são precisas": {
                "titulo": "🎯 Melhorar Precisão",
                "acoes": [
                    "Implementar conciliação automática de dados entre sistemas",
                    "Criar validações em tempo real com regras de negócio",
                    "Estabelecer processo de auditoria contínua de qualidade dos dados",
                    "Desenvolver alertas automáticos para inconsistências detectadas",
                    "Implementar versionamento e rastreabilidade de alterações"
                ]
            },
            "As informações disponibilizadas estão atualizadas": {
                "titulo": "🔄 Automatizar Atualização",
                "acoes": [
                    "Implementar atualização automática de dados via APIs integradas",
                    "Criar cronograma transparente de publicação com datas previstas",
                    "Desenvolver notificações push para usuários sobre novas atualizações",
                    "Estabelecer versionamento automático com histórico de mudanças",
                    "Implementar indicadores visuais de última atualização em cada dataset"
                ]
            },
            "Consigo obter o que preciso no menor tempo possível": {
                "titulo": "⏱️ Reduzir Tempo de Acesso",
                "acoes": [
                    "Criar dashboard personalizado de acesso rápido por perfil de usuário",
                    "Implementar busca por voz para consultas mais naturais",
                    "Otimizar consultas de banco de dados com indexação inteligente",
                    "Desenvolver API REST pública para integração com sistemas externos",
                    "Criar widgets embarcáveis para sites de terceiros"
                ]
            }
        }
        
        # Mostrar ações organizadas por prioridade
        questoes_abaixo_meta = [(q, m) for q, m in medias_questoes.items() if "satisfação" not in q.lower() and m < goal]
        questoes_acima_meta = [(q, m) for q, m in medias_questoes.items() if "satisfação" not in q.lower() and m >= goal]
        
        if questoes_abaixo_meta:
            st.markdown("### 🚨 Prioridade Alta - Questões Abaixo da Meta")
            questoes_abaixo_meta.sort(key=lambda x: x[1])  # Ordenar por média (pior primeiro)
            
            for questao, media_atual in questoes_abaixo_meta:
                if questao in acoes_por_questao:
                    acao_info = acoes_por_questao[questao]
                    gap = goal - media_atual
                    
                    with st.expander(f"{acao_info['titulo']} - Média: {media_atual:.2f} (Gap: -{gap:.2f})"):
                        st.write("**Ações Recomendadas:**")
                        for i, acao in enumerate(acao_info["acoes"], 1):
                            st.write(f"{i}. {acao}")
                        
                        # Barra de progresso
                        progresso = (media_atual / goal) * 100
                        st.progress(min(progresso / 100, 1.0))
                        st.caption(f"Progresso em relação à meta: {progresso:.1f}%")
                        
                        # Indicador de prioridade
                        if media_atual < 2.5:
                            st.error("🔴 **Prioridade Crítica** - Requer ação imediata")
                        elif media_atual < 3.5:
                            st.warning("🟡 **Prioridade Alta** - Ação necessária em breve")
                        else:
                            st.info("🔵 **Prioridade Média** - Melhorias incrementais")
        
        if questoes_acima_meta:
            st.markdown("### ✅ Manutenção - Questões Acima da Meta")
            questoes_acima_meta.sort(key=lambda x: x[1], reverse=True)  # Ordenar por média (melhor primeiro)
            
            for questao, media_atual in questoes_acima_meta:
                if questao in acoes_por_questao:
                    acao_info = acoes_por_questao[questao]
                    
                    with st.expander(f"{acao_info['titulo']} - Média: {media_atual:.2f} ✅"):
                        st.success("Esta questão está atingindo a meta! Ações para manter e aprimorar:")
                        for i, acao in enumerate(acao_info["acoes"], 1):
                            st.write(f"{i}. {acao}")
                        
                        # Indicador de excelência
                        if media_atual >= 4.5:
                            st.success("🌟 **Excelência** - Referência para outras questões")
                        else:
                            st.info("📈 **Bom desempenho** - Oportunidade de otimização")
        
        # Resumo executivo
        st.markdown("---")
        st.subheader("📋 Resumo Executivo")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🎯 Metas Atingidas:**")
            if questoes_acima_meta:
                for questao, media in questoes_acima_meta:
                    questao_short = questao[:40] + "..." if len(questao) > 40 else questao
                    st.write(f"✅ {questao_short}: {media:.2f}")
            else:
                st.write("Nenhuma questão atingiu a meta ainda.")
        
        with col2:
            st.markdown("**⚠️ Necessitam Atenção:**")
            if questoes_abaixo_meta:
                for questao, media in questoes_abaixo_meta:
                    questao_short = questao[:40] + "..." if len(questao) > 40 else questao
                    gap = goal - media
                    st.write(f"🔴 {questao_short}: {media:.2f} (Gap: -{gap:.2f})")
            else:
                st.write("Todas as questões estão atingindo a meta! 🎉")
        
        # Análise de satisfação geral
        if "Nível de satisfação com o Portal da Transparência do RS" in medias_questoes:
            satisfacao_geral = medias_questoes["Nível de satisfação com o Portal da Transparência do RS"]
            st.markdown("---")
            st.subheader("😊 Análise de Satisfação Geral")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Satisfação Atual", f"{satisfacao_geral:.2f}")
            with col2:
                if satisfacao_geral >= goal:
                    st.success("Meta de Satisfação Atingida! ✅")
                else:
                    gap_sat = goal - satisfacao_geral
                    st.error(f"Gap de Satisfação: -{gap_sat:.2f}")
            with col3:
                # Correlação com questões técnicas
                media_tecnica = np.mean([m for q, m in medias_questoes.items() if "satisfação" not in q.lower()])
                correlacao = abs(satisfacao_geral - media_tecnica)
                if correlacao < 0.5:
                    st.info("Alta correlação com questões técnicas")
                else:
                    st.warning("Baixa correlação - investigar fatores externos")
        
        # Indicadores de tendência e recomendações finais
        st.markdown("---")
        st.info("💡 **Dica:** Use os filtros na barra lateral para analisar segmentos específicos da população e identificar oportunidades de melhoria direcionadas.")
        
        # Exportar dados para análise
        if st.button("📊 Exportar Relatório de Análise"):
            if not medias_questoes:
                st.warning("⚠️ Não há dados suficientes para gerar o relatório. Verifique os filtros aplicados.")
            else:
                relatorio_data = {
                    'Questão': [],
                    'Média': [],
                    'Status': [],
                    'Gap': [],
                    'Prioridade': []
                }
                
                for questao, media in medias_questoes.items():
                    if "satisfação" not in questao.lower():
                        relatorio_data['Questão'].append(questao)
                        relatorio_data['Média'].append(media)
                        relatorio_data['Status'].append('Acima da Meta' if media >= goal else 'Abaixo da Meta')
                        relatorio_data['Gap'].append(goal - media if media < goal else 0)
                        
                        if media < 2.5:
                            prioridade = "Crítica"
                        elif media < 3.5:
                            prioridade = "Alta"
                        elif media < goal:
                            prioridade = "Média"
                        else:
                            prioridade = "Manutenção"
                        relatorio_data['Prioridade'].append(prioridade)
                
                df_relatorio = pd.DataFrame(relatorio_data)
                csv = df_relatorio.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"relatorio_portal_transparencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )


# -----------------------------
# Page: Configurações
# -----------------------------
if page == "Configurações":
    st.header("⚙️ Configurações e Metas")
    st.write("""
    Defina a **meta (goal)** global na barra lateral. 
    Agora você também pode definir metas por dimensão e salvar filtros padrões.
    """)

    # Metas por dimensão (persistentes)
    if st.session_state.auth["logged_in"]:
        user_prefs = st.session_state.dm.get_user_preferences(st.session_state.auth["email"])  # dict
        st.subheader("Metas por Dimensão")
        with st.form("form_goals_by_dim"):
            new_goals = {}
            for dim in DIMENSIONS.keys():
                # Ajustar default_val usando dict
                _default_goal_cfg = float(user_prefs.get("goal", user_prefs.get("goal_global", DEFAULT_GOAL))) if isinstance(user_prefs, dict) else DEFAULT_GOAL
                default_val = user_prefs.get("goal_by_dimension", {}).get(dim, _default_goal_cfg) if isinstance(user_prefs, dict) else _default_goal_cfg
                new_goals[dim] = st.number_input(f"Meta para {dim}", min_value=1.0, max_value=5.0, step=0.1, value=float(default_val))
            submitted = st.form_submit_button("Salvar metas por dimensão")
            if submitted:
                try:
                    # Substituir construção de UserPreferences por dict
                    updated = dict(user_prefs or {}) if isinstance(user_prefs, dict) else {}
                    updated["goal_by_dimension"] = {k: float(v) for k, v in new_goals.items()}
                    st.session_state.dm.save_user_preferences(st.session_state.auth["email"], updated)
                    st.success("Metas por dimensão salvas.")
                except Exception as e:
                    st.error(f"Falha ao salvar metas: {e}")

        st.subheader("Preferências de Filtros")
        st.caption("Os filtros selecionados na sidebar são salvos automaticamente por usuário.")
    else:
        st.info("Faça login para salvar metas por dimensão e filtros padrão.")

    st.write("### Mapeamento de Itens por Dimensão")
    st.json(DIMENSIONS, expanded=False)

    st.write("### Ordem e Mapeamento Likert")
    col1, col2 = st.columns(2)
    with col1:
        st.json(LIKERT_ORDER, expanded=False)
    with col2:
        st.json(LIKERT_MAP, expanded=False)

    st.write("### Campo de Satisfação e Mapeamento")
    st.write(f"Campo de satisfação: **{SAT_FIELD}**")
    st.json(SAT_MAP, expanded=False)

    st.write("### Campos de Perfil")
    st.json(PROFILE_FIELDS, expanded=False)
