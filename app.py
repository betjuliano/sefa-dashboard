
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

# Optional: Supabase
try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None

load_dotenv()

st.set_page_config(
    page_title="Dashboard de Qualidade - MVP",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Utils
# -----------------------------
@st.cache_resource
def load_mapping(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

MAPPING = load_mapping(os.path.join("config", "items_mapping.json"))

DIMENSIONS = MAPPING["dimensions"]
LIKERT_ORDER = MAPPING["likert_order"]
LIKERT_MAP = {k: v for k, v in MAPPING["likert_map"].items()}
SAT_FIELD = MAPPING["satisfaction_field"]
SAT_MAP = MAPPING["satisfaction_map"]
PROFILE_FIELDS = MAPPING["profile_fields"]

DEFAULT_GOAL = float(os.getenv("DEFAULT_GOAL", "4.0"))

# Supabase client (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
sb_client = None
if SUPABASE_URL and SUPABASE_ANON_KEY and create_client:
    try:
        sb_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        st.sidebar.warning(f"Supabase não inicializado: {e}")
        sb_client = None

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
    if st.sidebar.button("Sair"):
        if sb_client:
            try:
                sb_client.auth.sign_out()
            except Exception:
                pass
        st.session_state.auth = {"email": None, "logged_in": False}
        st.rerun()

# -----------------------------
# Data processing
# -----------------------------
def normalize_likert(series: pd.Series) -> pd.Series:
    # Strip & standardize strings, map to numbers, keep NaN for "Não sei"
    s = series.astype(str).str.strip()
    s = s.replace("nan", np.nan)
    return s.map(LIKERT_MAP)

def normalize_satisfaction(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().replace("nan", np.nan)
    return s.map(SAT_MAP)

def compute_metrics(df: pd.DataFrame, goal: float):
    results = {
        "items": {},  # per item: mean, n, freq (counts and %)
        "dimensions": {},  # per dimension: mean of item means
        "satisfaction": None,
        "insights": {"prioritarios": [], "acoes": [], "bons": []},
    }

    # Frequencies and means per item
    for dim_name, items in DIMENSIONS.items():
        for item in items:
            col = df[item]
            numeric = normalize_likert(col)
            mean_val = numeric.mean(skipna=True)
            n = numeric.notna().sum()

            # frequency counts in original labels (ordered)
            counts = col.value_counts(dropna=False).to_dict()
            # enforce full order
            freq_counts = {label: int(counts.get(label, 0)) for label in (LIKERT_ORDER + ["Não sei"])}
            total = sum(v for k, v in freq_counts.items() if k != "Não sei")
            freq_pct = {k: (v / total * 100 if total > 0 else 0) for k, v in freq_counts.items() if k != "Não sei"}

            results["items"][item] = {
                "dimension": dim_name,
                "mean": float(mean_val) if mean_val is not None and not np.isnan(mean_val) else None,
                "n": int(n),
                "freq_counts": freq_counts,
                "freq_pct": freq_pct,
            }

    # Dimension means (average of item means)
    for dim_name, items in DIMENSIONS.items():
        means = [results["items"][it]["mean"] for it in items if results["items"][it]["mean"] is not None]
        dim_mean = float(np.mean(means)) if len(means) else None
        results["dimensions"][dim_name] = {"mean": dim_mean, "n_items": len(means)}

    # Satisfaction overall (if column exists)
    if SAT_FIELD in df.columns:
        sat_mean = normalize_satisfaction(df[SAT_FIELD]).mean(skipna=True)
        results["satisfaction"] = float(sat_mean) if sat_mean is not None and not np.isnan(sat_mean) else None

    # Insights
    for item, info in results["items"].items():
        mean_val = info["mean"]
        if mean_val is None:
            continue
        if mean_val < (0.5 * goal):
            results["insights"]["prioritarios"].append((item, info["dimension"], mean_val))
        elif mean_val < goal:
            results["insights"]["acoes"].append((item, info["dimension"], mean_val))
        else:
            results["insights"]["bons"].append((item, info["dimension"], mean_val))

    # Sort insights by mean ascending (prioritize worst first)
    for k in results["insights"]:
        results["insights"][k] = sorted(results["insights"][k], key=lambda x: x[2])

    return results

# -----------------------------
# Statistical Analysis Functions
# -----------------------------

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
    for dim_name, items in DIMENSIONS.items():
        available_items = [item for item in items if item in df_analysis.columns]
        if available_items:
            df_analysis[f'{dim_name}_score'] = df_analysis[available_items].mean(axis=1)
    
    # Encode categorical variables
    le_sexo = LabelEncoder()
    le_escolaridade = LabelEncoder()
    le_servidor = LabelEncoder()
    
    if PROFILE_FIELDS["Sexo"] in df_analysis.columns:
        df_analysis['sexo_encoded'] = le_sexo.fit_transform(df_analysis[PROFILE_FIELDS["Sexo"]].fillna('Não informado'))
    
    if PROFILE_FIELDS["Escolaridade"] in df_analysis.columns:
        df_analysis['escolaridade_encoded'] = le_escolaridade.fit_transform(df_analysis[PROFILE_FIELDS["Escolaridade"]].fillna('Não informado'))
    
    if PROFILE_FIELDS["Servidor Público"] in df_analysis.columns:
        df_analysis['servidor_encoded'] = le_servidor.fit_transform(df_analysis[PROFILE_FIELDS["Servidor Público"]].fillna('Não informado'))
    
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
        min_age = int(np.nanmin(df[PROFILE_FIELDS["Idade"]]))
        max_age = int(np.nanmax(df[PROFILE_FIELDS["Idade"]]))
        default_age = tuple(saved.get("idade", (min_age, max_age)))
        age_min, age_max = st.sidebar.slider("Idade", min_value=min_age, max_value=max_age, value=default_age)
        df_filtered = df_filtered[
            (df_filtered[PROFILE_FIELDS["Idade"]] >= age_min) &
            (df_filtered[PROFILE_FIELDS["Idade"]] <= age_max)
        ]

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
    if PROFILE_FIELDS["Servidor Público"] in df.columns:
        sp_opts = ["Todos"] + sorted([x for x in df[PROFILE_FIELDS["Servidor Público"]].dropna().unique().tolist()])
        default_sp = saved.get("servidor_publico", "Todos")
        sp_sel = st.sidebar.selectbox("Servidor Público", options=sp_opts, index=sp_opts.index(default_sp) if default_sp in sp_opts else 0)
        if sp_sel != "Todos":
            df_filtered = df_filtered[df_filtered[PROFILE_FIELDS["Servidor Público"]] == sp_sel]

    # salvar filtros atualizados, se logado
    if st.session_state.auth["logged_in"]:
        try:
            current = st.session_state.dm.get_user_preferences(st.session_state.auth["email"]) 
            new_saved = {
                "idade": (age_min, age_max) if PROFILE_FIELDS["Idade"] in df.columns else saved.get("idade"),
                "sexo": sex_sel if PROFILE_FIELDS["Sexo"] in df.columns else saved.get("sexo"),
                "escolaridade": esc_sel if PROFILE_FIELDS["Escolaridade"] in df.columns else saved.get("escolaridade"),
                "servidor_publico": sp_sel if PROFILE_FIELDS["Servidor Público"] in df.columns else saved.get("servidor_publico"),
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
st.sidebar.caption("CSV padrão: separador `;` e codificação `latin-1`.")

# -----------------------------
# Main Pages
# -----------------------------
pages = {
    "Dashboard": "dashboard",
    "Upload de Arquivo": "upload",
    "Análise Detalhada": "analysis",
    "Perfil": "profile",
    "Configurações": "settings",
}
page = st.sidebar.radio("Navegação", options=list(pages.keys()))

# -----------------------------
# Load data (uploaded or sample)
# -----------------------------
if "data" not in st.session_state:
    # Carregar dados padrão automaticamente
    try:
        default_df = read_csv(os.path.join("sample_data", "baseKelm.csv"))
        st.session_state.data = default_df
        st.session_state.data_source = "baseKelm.csv (padrão)"
    except Exception as e:
        st.session_state.data = None
        st.session_state.data_source = None

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

    # Botão para restaurar dados padrão
    st.markdown("#### Restaurar Dados Padrão")
    st.caption("Use o botão abaixo para restaurar os dados padrão do sistema")
    if st.button("🔄 Restaurar baseKelm.csv (padrão)"):
        try:
            df = read_csv(os.path.join("sample_data", "baseKelm.csv"))
            return df, "baseKelm.csv (restaurado)"
        except Exception as e:
            st.error(f"Erro ao carregar dados padrão: {e}")
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
        st.info(f"📊 **Analisando dados de:** {st.session_state.data_source}")
        df = st.session_state.data.copy()
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
        r_vals = [metrics["dimensions"][d]["mean"] for d in DIMENSIONS.keys()]
        radar_cat = list(DIMENSIONS.keys())
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=r_vals, theta=radar_cat, fill="toself", name="Média"))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
            showlegend=False,
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ===== Novo layout de Insights =====
        # CSS básico para badges e cards
        st.markdown(
            """
            <style>
            .badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:12px; color:#fff; margin-left:6px; }
            .badge-green{ background:#16a34a; }
            .badge-orange{ background:#f59e0b; }
            .badge-red{ background:#dc2626; }
            .card { border:1px solid #e5e7eb; border-radius:10px; padding:12px 14px; background:#ffffff; margin-bottom:10px; }
            .item-row{ display:flex; align-items:center; justify-content:space-between; gap:8px; }
            .item-name{ font-size:0.92rem; }
            .item-mean{ font-weight:600; }
            .small { font-size:0.86rem; color:#6b7280; }
            .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-left:6px; vertical-align:baseline; }
            .sugg { color:#374151; font-size:0.85rem; margin-top:4px; }
            .sugg i { color:#6b7280; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        # Linha de atenção
        pri, aco, bons = metrics["insights"]["prioritarios"], metrics["insights"]["acoes"], metrics["insights"]["bons"]
        all_items_stats = []
        for dim_name, its in DIMENSIONS.items():
            for it in its:
                if it in metrics["items"]:
                    all_items_stats.append((it, dim_name, metrics["items"][it]["mean"]))
        if all_items_stats:
            worst_item, worst_dim, worst_mean = min(all_items_stats, key=lambda x: x[2])
            gap = float(goal) - float(worst_mean)
            gap_txt = f"(gap {gap:.2f})" if gap > 0 else ""
            st.warning(
                f"Atenção: {len(pri)+len(aco)} itens abaixo da meta — {len(pri)} prioritários. "
                f"Pior desempenho: [{worst_dim}] {worst_item} com média {worst_mean:.2f} {gap_txt}."
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
                    color = "#16a34a" if (dim_mean is not None and dim_mean >= dim_goal) else ("#f59e0b" if (dim_mean is not None and dim_goal - dim_mean <= 0.5) else "#dc2626")
                    st.markdown(
                        f"<div class='card'>"
                        f"<div class='item-row'><strong>{dim_name}</strong>"
                        f"<span class='dot' style='background:{color}'></span></div>"
                        f"<div class='small'>Média {(dim_mean if dim_mean is not None else 0):.2f} / Meta {dim_goal:.1f}</div>",
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
                        color = "#16a34a" if (mean is not None and mean >= dim_goal) else ("#f59e0b" if (mean is not None and dim_goal - mean <= 0.5) else "#dc2626")
                        bar_html = f"<div style='height:6px;background:#e5e7eb;border-radius:6px;overflow:hidden;'><div style='width:{int(pct*100)}%;height:100%;background:{color};'></div></div>"
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
            insight_options = {"Prioritários": "prioritarios", "Abaixo da meta": "acoes", "Bons (≥ meta)": "bons"}
            sel = st.multiselect("Filtrar tipos de insight", list(insight_options.keys()), default=list(insight_options.keys()))
            only_pri = st.checkbox("Mostrar apenas prioritários", value=False, key="only_pri_list")
            if only_pri:
                sel = ["Prioritários"]
            selected_keys = [insight_options[k] for k in sel]
        
            c1, c2, c3 = st.columns(3)
        
            def render_list(container, items, title, color):
                container.markdown(f"**{title}**")
                if not items:
                    container.write("—")
                    return
                for item, dim, mean in items:
                    container.write(f"- **[{dim}]** {item} → média **{mean:.2f}**")
        
            if "prioritarios" in selected_keys:
                render_list(c1, pri, "🔴 Prioritários (muito abaixo da meta)", "red")
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
        df_f = filters_ui(df)
        
        # Prepare data for analysis
        df_analysis = prepare_data_for_analysis(df_f)
        
        st.info(f"📊 **Analisando:** {len(df_analysis)} respostas válidas")
        
        # Tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Regressões por Dimensão", 
            "🎯 Regressões vs Satisfação", 
            "🔍 Análise Multivariada",
            "📊 Correlações e Associações"
        ])
        
        # Tab 1: Regressions by Dimension
        with tab1:
            st.subheader("Regressões das Dimensões vs Perfil Demográfico")
            st.caption("Análise de como variáveis demográficas influenciam cada dimensão de qualidade")
            
            dimension_sel = st.selectbox(
                "Selecione a dimensão para análise:",
                options=list(DIMENSIONS.keys()),
                key="regression_dimension"
            )
            
            if st.button("🔍 Executar Regressão", key="run_regression"):
                model, feature_names = regression_analysis(df_analysis, dimension_sel)
                
                if model is not None:
                    st.success(f"✅ Regressão executada com sucesso para **{dimension_sel}**")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📊 Resumo do Modelo")
                        st.write(f"**R² Ajustado:** {model.rsquared_adj:.3f}")
                        st.write(f"**F-statístico:** {model.fvalue:.2f}")
                        st.write(f"**p-valor (F):** {model.f_pvalue:.4f}")
                        st.write(f"**Observações:** {int(model.nobs)}")
                        
                        if model.f_pvalue < 0.05:
                            st.success("✅ Modelo estatisticamente significativo (p < 0.05)")
                        else:
                            st.warning("⚠️ Modelo não estatisticamente significativo (p ≥ 0.05)")
                    
                    with col2:
                        st.markdown("#### 📈 Coeficientes")
                        coef_df = pd.DataFrame({
                            'Variável': ['Intercepto'] + feature_names,
                            'Coeficiente': model.params.values,
                            'Erro Padrão': model.bse.values,
                            't-valor': model.tvalues.values,
                            'p-valor': model.pvalues.values
                        })
                        
                        # Highlight significant coefficients
                        def highlight_significant(row):
                            if row['p-valor'] < 0.05:
                                return ['background-color: #d4edda'] * len(row)
                            return [''] * len(row)
                        
                        st.dataframe(
                            coef_df.style.apply(highlight_significant, axis=1).format({
                                'Coeficiente': '{:.3f}',
                                'Erro Padrão': '{:.3f}',
                                't-valor': '{:.3f}',
                                'p-valor': '{:.4f}'
                            }),
                            use_container_width=True
                        )
                    
                    # Interpretation
                    st.markdown("#### 💡 Interpretação")
                    significant_vars = coef_df[coef_df['p-valor'] < 0.05]
                    
                    if len(significant_vars) > 1:  # More than just intercept
                        st.write("**Variáveis com influência significativa:**")
                        for _, row in significant_vars.iterrows():
                            if row['Variável'] != 'Intercepto':
                                direction = "positiva" if row['Coeficiente'] > 0 else "negativa"
                                st.write(f"- **{row['Variável']}**: Influência {direction} (β = {row['Coeficiente']:.3f})")
                    else:
                        st.info("Nenhuma variável demográfica apresenta influência significativa nesta dimensão.")
                
                else:
                    st.error("❌ Não foi possível executar a regressão. Verifique se há dados suficientes.")
        
        # Tab 2: Satisfaction Regression
        with tab2:
            st.subheader("Regressões das Dimensões vs Satisfação Geral")
            st.caption("Análise de como cada dimensão influencia a satisfação geral")
            
            if SAT_FIELD in df_analysis.columns:
                if st.button("🎯 Executar Análise de Satisfação", key="run_satisfaction"):
                    st.success("✅ Análise de satisfação executada")
                    
                    # Prepare data
                    satisfaction_data = df_analysis[[SAT_FIELD] + [f'{dim}_score' for dim in DIMENSIONS.keys()]].dropna()
                    
                    if len(satisfaction_data) > 10:
                        # Multiple regression
                        X = satisfaction_data[[f'{dim}_score' for dim in DIMENSIONS.keys()]]
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
        
        # Tab 3: Multivariate Analysis
        with tab3:
            st.subheader("Análise Multivariada")
            st.caption("Análise de Componentes Principais (PCA) e Clustering")
            
            if st.button("🔍 Executar Análise Multivariada", key="run_multivariate"):
                multivariate_result = multivariate_analysis(df_analysis)
                
                if multivariate_result is not None:
                    st.success("✅ Análise multivariada executada com sucesso")
                    
                    # PCA Results
                    st.markdown("#### 📊 Análise de Componentes Principais (PCA)")
                    
                    pca = multivariate_result['pca']
                    pca_result = multivariate_result['pca_result']
                    dimension_names = multivariate_result['dimension_names']
                    
                    # Explained variance
                    explained_var = pca.explained_variance_ratio_
                    cumsum_var = np.cumsum(explained_var)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### Variância Explicada")
                        for i, (var, cumvar) in enumerate(zip(explained_var, cumsum_var)):
                            st.write(f"**PC{i+1}**: {var:.1%} (Acumulada: {cumvar:.1%})")
                    
                    with col2:
                        # PCA Scree Plot
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=list(range(1, len(explained_var)+1)),
                            y=explained_var,
                            mode='lines+markers',
                            name='Variância Explicada'
                        ))
                        fig.update_layout(
                            title="Scree Plot - Variância Explicada por Componente",
                            xaxis_title="Componente Principal",
                            yaxis_title="Variância Explicada",
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # PCA Loadings
                    st.markdown("##### Cargas dos Componentes Principais")
                    loadings_df = pd.DataFrame(
                        pca.components_.T,
                        columns=[f'PC{i+1}' for i in range(len(dimension_names))],
                        index=dimension_names
                    )
                    st.dataframe(loadings_df.style.format('{:.3f}'), use_container_width=True)
                    
                    # Clustering Results
                    st.markdown("#### 🎯 Análise de Clustering")
                    
                    optimal_k = multivariate_result['optimal_k']
                    cluster_labels = multivariate_result['cluster_labels']
                    silhouette_scores = multivariate_result['silhouette_scores']
                    
                    st.write(f"**Número ótimo de clusters:** {optimal_k}")
                    st.write(f"**Score de Silhouette:** {silhouette_scores[np.argmax(silhouette_scores)]:.3f}")
                    
                    # Cluster visualization (first 2 PCs)
                    if len(pca_result) > 1:
                        fig = px.scatter(
                            x=pca_result[:, 0],
                            y=pca_result[:, 1],
                            color=cluster_labels,
                            title="Clusters nos Primeiros 2 Componentes Principais",
                            labels={'x': 'PC1', 'y': 'PC2'},
                            color_discrete_sequence=px.colors.qualitative.Set1
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Cluster characteristics
                    st.markdown("##### Características dos Clusters")
                    cluster_data = df_analysis.copy()
                    cluster_data['Cluster'] = cluster_labels
                    
                    # Use dimension score columns instead of dimension names
                    dimension_score_cols = [f'{dim}_score' for dim in dimension_names if f'{dim}_score' in cluster_data.columns]
                    if dimension_score_cols:
                        cluster_stats = cluster_data.groupby('Cluster')[dimension_score_cols].mean()
                        st.dataframe(cluster_stats.style.format('{:.2f}'), use_container_width=True)
                    else:
                        st.warning("Não foi possível calcular estatísticas dos clusters - colunas de dimensões não encontradas.")
                    
                    # Interpretation
                    st.markdown("#### 💡 Interpretação")
                    st.write("**Análise PCA:**")
                    if explained_var[0] > 0.5:
                        st.write(f"- O primeiro componente explica {explained_var[0]:.1%} da variância")
                        st.write("- Há uma dimensão dominante na qualidade do sistema")
                    else:
                        st.write("- As dimensões são relativamente independentes")
                    
                    st.write("**Análise de Clustering:**")
                    if optimal_k > 2:
                        st.write(f"- Identificados {optimal_k} grupos distintos de usuários")
                        st.write("- Sugere segmentação para estratégias diferenciadas")
                    else:
                        st.write("- Usuários formam grupos relativamente homogêneos")
                
                else:
                    st.error("❌ Não foi possível executar análise multivariada. Verifique os dados.")
        
        # Tab 4: Correlations and Associations
        with tab4:
            st.subheader("Correlações e Associações")
            st.caption("Análise de correlações entre variáveis e testes de associação")
            
            if st.button("📊 Executar Análise de Correlações", key="run_correlations"):
                st.success("✅ Análise de correlações executada")
                
                # Prepare correlation data
                corr_data = df_analysis[[f'{dim}_score' for dim in DIMENSIONS.keys()]].dropna()
                
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
                        
                        sex_dim_data = df_analysis[[PROFILE_FIELDS["Sexo"]] + [f'{dim}_score' for dim in DIMENSIONS.keys()]].dropna()
                        
                        if len(sex_dim_data) > 10:
                            # ANOVA for each dimension
                            for dim in DIMENSIONS.keys():
                                groups = [group[f'{dim}_score'].dropna() for name, group in sex_dim_data.groupby(PROFILE_FIELDS["Sexo"])]
                                if len(groups) > 1 and all(len(g) > 0 for g in groups):
                                    f_stat, p_val = stats.f_oneway(*groups)
                                    significance = "✅" if p_val < 0.05 else "❌"
                                    st.write(f"{significance} **{dim}**: F = {f_stat:.3f}, p = {p_val:.4f}")
                    
                    # Servidor Público vs Dimensions
                    if PROFILE_FIELDS["Servidor Público"] in df_analysis.columns:
                        st.markdown("##### Associação: Servidor Público vs Dimensões")
                        
                        serv_dim_data = df_analysis[[PROFILE_FIELDS["Servidor Público"]] + [f'{dim}_score' for dim in DIMENSIONS.keys()]].dropna()
                        
                        if len(serv_dim_data) > 10:
                            for dim in DIMENSIONS.keys():
                                groups = [group[f'{dim}_score'].dropna() for name, group in serv_dim_data.groupby(PROFILE_FIELDS["Servidor Público"])]
                                if len(groups) > 1 and all(len(g) > 0 for g in groups):
                                    f_stat, p_val = stats.f_oneway(*groups)
                                    significance = "✅" if p_val < 0.05 else "❌"
                                    st.write(f"{significance} **{dim}**: F = {f_stat:.3f}, p = {p_val:.4f}")
                
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
