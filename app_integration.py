"""
Integração do novo sistema de processamento de questionários com o app.py

Este arquivo contém as funções atualizadas que substituem as antigas funções
do app.py, integrando o QuestionnaireProcessor e o sistema de filtros.
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Any, Tuple, Optional

# Import do novo sistema
from core import QuestionnaireProcessor, ScaleConverter, TextNormalizer


class AppIntegration:
    """
    Classe para integrar o novo sistema de processamento com o app.py existente.
    
    Substitui as funções antigas mantendo compatibilidade com a interface atual.
    """
    
    def __init__(self):
        """Initialize the integration system"""
        self.processor = QuestionnaireProcessor()
        self.scale_converter = ScaleConverter()
        self.text_normalizer = TextNormalizer()
        
        # Cache para resultados processados
        self._results_cache = {}
        self._current_question_set = None
        
    def update_global_variables(self, question_set: str) -> None:
        """
        Substitui a função update_global_variables do app.py original.
        
        Agora usa o QuestionnaireProcessor para carregar configurações.
        """
        # Mapear nomes da interface para nomes internos
        question_set_mapping = {
            "Completo (26 questões)": "base26",  # Base completa com 26 questões
            "20 questões": "base20_filtered",     # Base20 com 6 questões removidas
            "8 questões": "base8"                 # Base8 original
        }
        
        internal_name = question_set_mapping.get(question_set, "base26")
        
        try:
            # Carregar configuração usando o novo sistema
            if internal_name == "base26":
                # Base26 usa a configuração base20 (que tem 26 questões)
                config = self.processor.load_configuration("base20")
            elif internal_name == "base20_filtered":
                # Base20 filtrado usa base20 mas remove 6 questões específicas
                config = self.processor.load_configuration("base20")
            else:
                # base8 ou outros
                config = self.processor.load_configuration(internal_name)
            
            # Atualizar variáveis globais para compatibilidade
            import app
            app.MAPPING = config
            app.DIMENSIONS = config["dimensions"]
            app.LIKERT_ORDER = config["likert_order"]
            app.LIKERT_MAP = {k: v for k, v in config["likert_map"].items()}
            app.SAT_FIELD = config["satisfaction_field"]
            app.SAT_MAP = config["satisfaction_map"]
            app.PROFILE_FIELDS = config["profile_fields"]
            
            self._current_question_set = internal_name
                
        except Exception as e:
            st.error(f"Erro ao carregar configuração para {question_set}: {str(e)}")
    
    def _show_structure_validation(self) -> None:
        """Mostra validação da estrutura de dimensões na barra lateral"""
        if self._current_question_set:
            report = self.processor.get_dimension_structure_report()
            
            st.sidebar.write("**📊 Estrutura de Dimensões:**")
            for dim_name, dim_data in report["dimensions"].items():
                st.sidebar.write(f"• {dim_name}: {dim_data['question_count']} questões")
            
            if "validation" in report and report["validation"]:
                st.sidebar.write("**✅ Validação:**")
                for dim_name, validation in report["validation"].items():
                    status = "✅" if validation["valid"] else "⚠️"
                    st.sidebar.write(f"{status} {dim_name}: {validation['actual']}/{validation['expected']}")
    
    def filter_by_question_set(self, df: pd.DataFrame, question_set: str) -> pd.DataFrame:
        """
        Substitui a função filter_by_question_set do app.py original.
        
        Implementa filtros: Base26 (completo), Base20 (remove 6 questões), Base8.
        """
        # Mapear nomes da interface para nomes internos
        question_set_mapping = {
            "Completo (26 questões)": "base26",  # Base completa com 26 questões
            "20 questões": "base20_filtered",     # Base20 com 6 questões removidas
            "8 questões": "base8"                 # Base8 original
        }
        
        # Questões específicas a serem removidas no filtro "20 questões"
        QUESTOES_REMOVIDAS_BASE20 = [
            "Os recursos de acessibilidade do sistema são fáceis de encontrar.",
            "O sistema informa sobre as políticas de privacidade e segurança.",
            "O sistema oferece instruções úteis de como utilizar os serviços.",
            "O prazo de entrega dos serviços é informado.",
            "As taxas cobradas pelos serviços são informadas.",
            "Os serviços permitem interações em tempo real (ex. chatbot, IA)."
        ]
        
        internal_name = question_set_mapping.get(question_set, "base20")
        
        try:
            # Atualizar configuração
            self.update_global_variables(question_set)
            
            if question_set == "Completo (26 questões)":
                # Base26: Retornar todos os dados (26 questões completas)
                return df
            
            elif question_set == "20 questões":
                # Base20: Remover 6 questões específicas do Base26
                columns_to_keep = []
                removed_cols = []
                
                for col in df.columns:
                    if col in QUESTOES_REMOVIDAS_BASE20:
                        removed_cols.append(col)
                    else:
                        columns_to_keep.append(col)
                
                # Armazenar informações sobre colunas removidas
                if removed_cols:
                    if not hasattr(st.session_state, 'removed_columns'):
                        st.session_state.removed_columns = {}
                    st.session_state.removed_columns[question_set] = removed_cols
                
                return df[columns_to_keep]
            
            elif question_set == "8 questões":
                # Base8: Usar o sistema de filtragem do QuestionnaireProcessor
                filtered_df, removed_cols = self.processor.filter_by_question_set(df, "base8")
                
                # Armazenar informações sobre colunas removidas
                if removed_cols:
                    if not hasattr(st.session_state, 'removed_columns'):
                        st.session_state.removed_columns = {}
                    st.session_state.removed_columns[question_set] = removed_cols
                
                return filtered_df
            
            else:
                st.warning(f"Conjunto de questões desconhecido: {question_set}")
                return df
                
        except Exception as e:
            st.error(f"Erro ao filtrar dados para {question_set}: {str(e)}")
            return df
    
    def compute_metrics(self, df: pd.DataFrame, goal: float) -> Dict[str, Any]:
        """
        Substitui a função compute_metrics do app.py original.
        
        Usa o novo QuestionnaireProcessor para cálculos mais robustos.
        """
        # Mapear question_set atual
        question_set_mapping = {
            "Completo (26 questões)": "base26",
            "20 questões": "base20_filtered", 
            "8 questões": "base8"
        }
        
        # Usar session_state se disponível, senão usar padrão
        try:
            current_question_set = getattr(st.session_state, 'question_set', 'Completo (26 questões)')
        except:
            current_question_set = 'Completo (26 questões)'
        internal_name = question_set_mapping.get(current_question_set, "base26")
        
        # Criar chave de cache
        cache_key = f"{internal_name}_{len(df)}_{hash(str(df.columns.tolist()))}"
        
        # Verificar cache
        if cache_key in self._results_cache:
            processing_results = self._results_cache[cache_key]
        else:
            # Processar dados usando o novo sistema
            try:
                # Mapear internal_name para configuração real
                if internal_name in ["base26", "base20_filtered"]:
                    # Ambos usam a configuração base20
                    config_name = "base20"
                else:
                    config_name = internal_name
                
                processing_results = self.processor.process_questionnaire_data(df, config_name)
                self._results_cache[cache_key] = processing_results
            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")
                return self._create_empty_results()
        
        # Converter para formato compatível com app.py original
        return self._convert_to_legacy_format(processing_results, goal)
    
    def _convert_to_legacy_format(self, processing_results, goal: float) -> Dict[str, Any]:
        """Converte resultados do novo sistema para formato compatível com app.py"""
        results = {
            "items": {},
            "dimensions": {},
            "satisfaction": processing_results.satisfaction_score,
            "insights": {"criticos": [], "acoes": [], "bons": []},
        }
        
        # Converter estatísticas por questão
        for dimension_name, dimension_stats in processing_results.dimensions.items():
            # Adicionar estatísticas da dimensão
            results["dimensions"][dimension_name] = {
                "mean": dimension_stats.mean_score,
                "n_items": dimension_stats.question_count
            }
            
            # Adicionar estatísticas por questão
            for question_stats in dimension_stats.questions:
                # Simular contagens de frequência (não disponível no novo sistema)
                freq_counts = self._simulate_frequency_counts()
                freq_pct = {k: (v / sum(freq_counts.values()) * 100 if sum(freq_counts.values()) > 0 else 0) 
                           for k, v in freq_counts.items()}
                
                results["items"][question_stats.question_text] = {
                    "dimension": dimension_name,
                    "mean": question_stats.mean_score,
                    "n": question_stats.valid_responses,
                    "freq_counts": freq_counts,
                    "freq_pct": freq_pct,
                }
                
                # Classificar para insights
                mean_val = question_stats.mean_score
                if mean_val is not None and not np.isnan(mean_val):
                    if mean_val < 3.0:
                        results["insights"]["criticos"].append((question_stats.question_text, dimension_name, mean_val))
                    elif mean_val < goal:
                        results["insights"]["acoes"].append((question_stats.question_text, dimension_name, mean_val))
                    else:
                        results["insights"]["bons"].append((question_stats.question_text, dimension_name, mean_val))
        
        # Ordenar insights
        for k in results["insights"]:
            results["insights"][k] = sorted(results["insights"][k], key=lambda x: x[2])
        
        return results
    
    def _simulate_frequency_counts(self) -> Dict[str, int]:
        """Simula contagens de frequência para compatibilidade"""
        # Retorna contagens simuladas baseadas na configuração atual
        if hasattr(self.processor, 'current_config') and self.processor.current_config:
            likert_order = self.processor.current_config.get("likert_order", [])
            return {label: 0 for label in likert_order + ["Não sei"]}
        else:
            return {
                "Discordo totalmente": 0,
                "Discordo": 0,
                "Indiferente": 0,
                "Concordo": 0,
                "Concordo totalmente": 0,
                "Não sei": 0
            }
    
    def _create_empty_results(self) -> Dict[str, Any]:
        """Cria resultados vazios em caso de erro"""
        return {
            "items": {},
            "dimensions": {},
            "satisfaction": None,
            "insights": {"criticos": [], "acoes": [], "bons": []},
        }
    
    def normalize_likert(self, series: pd.Series) -> pd.Series:
        """
        Substitui a função normalize_likert do app.py original.
        
        Usa o ScaleConverter para conversão mais robusta.
        """
        return self.scale_converter.convert_likert_column(series)
    
    def normalize_satisfaction(self, series: pd.Series) -> pd.Series:
        """
        Substitui a função normalize_satisfaction do app.py original.
        
        Usa o ScaleConverter para conversão de satisfação.
        """
        return self.scale_converter.convert_satisfaction_column(series)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do processamento atual.
        
        Útil para debugging e monitoramento.
        """
        return {
            "cache_size": len(self._results_cache),
            "current_question_set": self._current_question_set,
            "processor_config": self.processor.current_config is not None,
            "available_filters": ["Completo", "20 questões", "8 questões"]
        }
    
    def clear_cache(self) -> None:
        """Limpa o cache de resultados"""
        self._results_cache.clear()
        st.success("Cache limpo com sucesso!")
    
    def show_debug_info(self) -> None:
        """Mostra informações de debug na barra lateral"""
        if st.sidebar.checkbox("🐛 Debug Info"):
            stats = self.get_processing_stats()
            st.sidebar.json(stats)
            
            if st.sidebar.button("🗑️ Limpar Cache"):
                self.clear_cache()
    
    def show_validation_info(self) -> None:
        """Mostra informações de validação na barra lateral"""
        if st.sidebar.checkbox("🔍 Mostrar validação de estrutura"):
            self._show_structure_validation()
    
    def show_removed_columns_info(self) -> None:
        """Mostra informações sobre colunas removidas na barra lateral"""
        if hasattr(st.session_state, 'removed_columns') and st.session_state.removed_columns:
            current_question_set = getattr(st.session_state, 'question_set', 'Completo (26 questões)')
            if current_question_set in st.session_state.removed_columns:
                removed_cols = st.session_state.removed_columns[current_question_set]
                if removed_cols and st.sidebar.checkbox("🔍 Mostrar colunas removidas"):
                    st.sidebar.write(f"**Colunas removidas ({len(removed_cols)}):**")
                    for col in removed_cols[:5]:  # Mostrar apenas as primeiras 5
                        st.sidebar.write(f"• {col[:50]}...")
                    if len(removed_cols) > 5:
                        st.sidebar.write(f"... e mais {len(removed_cols) - 5}")


# Instância global para uso no app.py
app_integration = AppIntegration()


# Funções de compatibilidade para substituir no app.py
def update_global_variables(question_set: str) -> None:
    """Função de compatibilidade"""
    app_integration.update_global_variables(question_set)


def filter_by_question_set(df: pd.DataFrame, question_set: str) -> pd.DataFrame:
    """Função de compatibilidade"""
    return app_integration.filter_by_question_set(df, question_set)


def compute_metrics(df: pd.DataFrame, goal: float) -> Dict[str, Any]:
    """Função de compatibilidade"""
    return app_integration.compute_metrics(df, goal)


def normalize_likert(series: pd.Series) -> pd.Series:
    """Função de compatibilidade"""
    return app_integration.normalize_likert(series)


def normalize_satisfaction(series: pd.Series) -> pd.Series:
    """Função de compatibilidade"""
    return app_integration.normalize_satisfaction(series)


# Função para mostrar informações do novo sistema
def show_new_system_info():
    """Mostra informações sobre o novo sistema na barra lateral"""
    if st.sidebar.checkbox("ℹ️ Sobre o Novo Sistema"):
        st.sidebar.markdown("""
        **🚀 Sistema Atualizado**
        
        ✅ **ScaleConverter**: Conversão robusta de escalas Likert
        
        ✅ **QuestionnaireProcessor**: Processamento completo de questionários
        
        ✅ **Validação automática** da estrutura de dimensões
        
        ✅ **Cache inteligente** para melhor performance
        
        ✅ **Tratamento de erros** aprimorado
        """)
        
        # Mostrar debug info
        app_integration.show_debug_info()


# Função para adicionar à barra lateral do app.py
def add_sidebar_enhancements():
    """Adiciona melhorias à barra lateral"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 Sistema de Processamento**")
    
    show_new_system_info()
    
    # Mostrar validação se disponível
    if hasattr(app_integration.processor, 'current_config') and app_integration.processor.current_config:
        app_integration.show_validation_info()
    
    # Mostrar informações sobre colunas removidas
    app_integration.show_removed_columns_info()