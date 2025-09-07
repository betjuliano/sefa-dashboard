
import os
import io
import json
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
    st.session_state.data = None

def read_csv(uploaded_file, delimiter=";", encoding="latin-1"):
    return pd.read_csv(uploaded_file, sep=delimiter, encoding=encoding)

def data_source_ui():
    st.markdown("#### Fonte de Dados")
    uploaded = st.file_uploader("Carregue um arquivo .csv", type=["csv"])
    col_delim, col_enc = st.columns(2)
    delimiter = col_delim.selectbox("Delimitador", options=[";", ",", "\\t"], index=0)
    enc = col_enc.selectbox("Codificação", options=["latin-1", "utf-8"], index=0)

    if uploaded is not None:
        try:
            df = read_csv(uploaded, delimiter=delimiter.replace("\\t", "\t"), encoding=enc)
            return df, uploaded.name
        except Exception as e:
            st.error(f"Erro ao ler CSV: {e}")

    # Sample fallback
    st.caption("Ou use o dado de exemplo: `sample_data/baseKelm.csv`")
    if st.button("Usar dado de exemplo"):
        try:
            df = read_csv(os.path.join("sample_data", "baseKelm.csv"))
            return df, "baseKelm.csv"
        except Exception as e:
            st.error(f"Erro ao carregar exemplo: {e}")
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

# -----------------------------
# Page: Dashboard
# -----------------------------
if page == "Dashboard":
    st.header("🏠 Visão Geral")
    if st.session_state.data is None:
        st.info("Carregue um CSV na página **Upload de Arquivo** ou use o dado de exemplo.")
    else:
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
