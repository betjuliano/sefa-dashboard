"""
Questionnaire processing utilities for calculating means and organizing dimensions

This module provides utilities for processing questionnaire data, calculating
means by question and dimension, and organizing results according to the
quality framework (System Quality, Information Quality, Operation Quality).
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from pathlib import Path

from .scale_converter import ScaleConverter
from .text_normalizer import TextNormalizer


@dataclass
class QuestionStats:
    """Statistics for a single question"""
    question_text: str
    mean_score: float
    count: int
    valid_responses: int
    invalid_responses: int
    response_rate: float
    std_deviation: float
    
    def __post_init__(self):
        """Calculate response rate"""
        if self.count > 0:
            self.response_rate = self.valid_responses / self.count
        else:
            self.response_rate = 0.0


@dataclass
class DimensionStats:
    """Statistics for a dimension (group of questions)"""
    dimension_name: str
    mean_score: float
    question_count: int
    total_responses: int
    valid_responses: int
    questions: List[QuestionStats]
    
    def __post_init__(self):
        """Calculate derived statistics"""
        if self.questions:
            self.question_count = len(self.questions)
            self.total_responses = sum(q.count for q in self.questions)
            self.valid_responses = sum(q.valid_responses for q in self.questions)


@dataclass
class ProcessingResults:
    """Complete processing results for a questionnaire dataset"""
    overall_mean: float
    total_responses: int
    valid_responses: int
    dimensions: Dict[str, DimensionStats]
    satisfaction_score: Optional[float]
    processing_errors: List[str]
    question_mapping_issues: List[str]


class QuestionnaireProcessor:
    """
    Main processor for questionnaire data analysis.
    
    Handles conversion of Likert scales, calculation of means by question and dimension,
    and organization of results according to the quality framework.
    
    Supports different question sets:
    - base20: 20 questions (QS: 9, QI: 4, QO: 7) - removes 6 specific questions from base26
    - base8: 8 questions (QS: 4, QI: 3, QO: 1) - subset for transparency portal
    - base26: Complete set (QS: 10, QI: 7, QO: 9) - full questionnaire
    """
    
    # Expected dimension structure for validation
    EXPECTED_DIMENSIONS = {
        "base20": {
            "Qualidade do Sistema": 10,      # Actually has 10 in config
            "Qualidade da Informação": 7,    # Actually has 7 in config  
            "Qualidade da Operação": 9       # Actually has 9 in config
        },
        "base8": {
            "Qualidade do Sistema": 4,
            "Qualidade da Informação": 3,
            "Qualidade da Operação": 1
        }
    }
    
    def __init__(self, config_path: str = "config"):
        """
        Initialize the processor with configuration files.
        
        Args:
            config_path: Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.scale_converter = ScaleConverter()
        self.text_normalizer = TextNormalizer()
        
        # Will be loaded when needed
        self.current_config = None
        self.current_question_set = None
        
    def load_configuration(self, question_set: str = "base20") -> Dict[str, Any]:
        """
        Load configuration for specified question set.
        
        Args:
            question_set: Either "base20" or "base8"
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If question_set is invalid
        """
        if question_set == "base20":
            config_file = self.config_path / "items_mapping.json"
        elif question_set == "base8":
            config_file = self.config_path / "items_mapping_8q.json"
        else:
            raise ValueError(f"Invalid question set: {question_set}. Must be 'base20' or 'base8'")
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.current_config = config
        self.current_question_set = question_set
        
        # Update scale converter with config
        if "likert_map" in config:
            self.scale_converter = ScaleConverter(config["likert_map"])
        
        # Validate dimension structure
        self._validate_dimension_structure(question_set)
        
        return config
    
    def _validate_dimension_structure(self, question_set: str) -> None:
        """
        Validate that the loaded configuration has the expected dimension structure.
        
        Args:
            question_set: The question set being validated
        """
        if question_set not in self.EXPECTED_DIMENSIONS:
            return  # Skip validation for unknown question sets
        
        expected = self.EXPECTED_DIMENSIONS[question_set]
        actual_dimensions = self.current_config.get("dimensions", {})
        
        import os
        if os.getenv('DISABLE_EMOJIS', 'false').lower() == 'true':
            print(f"\nValidando estrutura de dimensoes para {question_set}:")
            
            for dimension_name, expected_count in expected.items():
                if dimension_name in actual_dimensions:
                    actual_count = len(actual_dimensions[dimension_name])
                    status = "OK" if actual_count == expected_count else "AVISO"
                    print(f"  {status} {dimension_name}: {actual_count} questoes (esperado: {expected_count})")
                    
                    if actual_count != expected_count:
                        print(f"    Diferenca: {actual_count - expected_count:+d} questoes")
                else:
                    print(f"  ERRO {dimension_name}: Dimensao nao encontrada")
        else:
            print(f"\n📊 Validando estrutura de dimensões para {question_set}:")
            
            for dimension_name, expected_count in expected.items():
                if dimension_name in actual_dimensions:
                    actual_count = len(actual_dimensions[dimension_name])
                    status = "✅" if actual_count == expected_count else "⚠️"
                    print(f"  {status} {dimension_name}: {actual_count} questões (esperado: {expected_count})")
                    
                    if actual_count != expected_count:
                        print(f"    Diferença: {actual_count - expected_count:+d} questões")
                else:
                    print(f"  ❌ {dimension_name}: Dimensão não encontrada")
    
    def get_dimension_structure_report(self) -> Dict[str, Any]:
        """
        Get a detailed report of the current dimension structure.
        
        Returns:
            Dictionary with dimension structure details
        """
        if not self.current_config:
            return {"error": "No configuration loaded"}
        
        dimensions = self.current_config.get("dimensions", {})
        report = {
            "question_set": self.current_question_set,
            "total_questions": sum(len(questions) for questions in dimensions.values()),
            "dimensions": {},
            "validation": {}
        }
        
        # Add dimension details
        for dimension_name, questions in dimensions.items():
            report["dimensions"][dimension_name] = {
                "question_count": len(questions),
                "questions": questions
            }
        
        # Add validation if we have expected structure
        if self.current_question_set in self.EXPECTED_DIMENSIONS:
            expected = self.EXPECTED_DIMENSIONS[self.current_question_set]
            for dimension_name, expected_count in expected.items():
                actual_count = len(dimensions.get(dimension_name, []))
                report["validation"][dimension_name] = {
                    "expected": expected_count,
                    "actual": actual_count,
                    "valid": actual_count == expected_count,
                    "difference": actual_count - expected_count
                }
        
        return report
    
    def identify_question_columns(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Identify which columns contain questionnaire questions vs other data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (question_columns, other_columns)
        """
        if self.current_config is None:
            raise ValueError("Configuration not loaded. Call load_configuration() first.")
        
        question_columns = []
        other_columns = []
        mapping_issues = []
        
        # Get all expected questions from dimensions
        expected_questions = []
        for dimension_questions in self.current_config["dimensions"].values():
            expected_questions.extend(dimension_questions)
        
        # Normalize expected questions for matching
        normalized_expected = {}
        for question in expected_questions:
            normalized = self.text_normalizer.normalize_question_text(question)
            normalized_expected[normalized] = question
        
        # Check each column in the DataFrame
        for col in df.columns:
            # Skip obvious non-question columns
            if col.lower() in ['timestamp', 'id', 'user_id', 'session_id']:
                other_columns.append(col)
                continue
            
            # Check if it's a profile field
            profile_fields = self.current_config.get("profile_fields", {})
            if col in profile_fields.values() or any(col.lower() in pf.lower() for pf in profile_fields.values()):
                other_columns.append(col)
                continue
            
            # Check if it's the satisfaction field
            satisfaction_field = self.current_config.get("satisfaction_field", "")
            if col == satisfaction_field or col.lower() in satisfaction_field.lower():
                other_columns.append(col)
                continue
            
            # Try to match with expected questions
            normalized_col = self.text_normalizer.normalize_question_text(col)
            
            # Exact match
            if normalized_col in normalized_expected:
                question_columns.append(col)
                continue
            
            # Fuzzy match
            best_match = self.text_normalizer.find_best_match(col, expected_questions, threshold=0.3)
            if best_match:
                question_columns.append(col)
                continue
            
            # Check if column contains Likert-like responses
            if self._contains_likert_responses(df[col]):
                question_columns.append(col)
                mapping_issues.append(f"Column '{col}' contains Likert responses but doesn't match expected questions")
            else:
                other_columns.append(col)
        
        return question_columns, other_columns
    
    def _contains_likert_responses(self, series: pd.Series) -> bool:
        """
        Check if a series contains Likert-like responses.
        
        Args:
            series: Pandas series to check
            
        Returns:
            True if series appears to contain Likert responses
        """
        if series.empty:
            return False
        
        # Get unique non-null values
        unique_values = series.dropna().unique()
        if len(unique_values) == 0:
            return False
        
        # Check if any values match known Likert responses
        likert_indicators = [
            "concordo", "discordo", "totalmente", "satisfeito", "insatisfeito",
            "neutro", "indiferente", "não sei", "nao sei"
        ]
        
        for value in unique_values:
            str_value = str(value).lower()
            if any(indicator in str_value for indicator in likert_indicators):
                return True
        
        return False
    
    def process_questionnaire_data(self, df: pd.DataFrame, question_set: str = "base20") -> ProcessingResults:
        """
        Process complete questionnaire dataset.
        
        Args:
            df: Input DataFrame with questionnaire responses
            question_set: Question set to use ("base20" or "base8")
            
        Returns:
            ProcessingResults with all calculated statistics
        """
        # Load configuration
        config = self.load_configuration(question_set)
        
        # Initialize results
        processing_errors = []
        question_mapping_issues = []
        
        # Identify question columns
        try:
            question_columns, other_columns = self.identify_question_columns(df)
        except Exception as e:
            processing_errors.append(f"Error identifying question columns: {str(e)}")
            question_columns = []
            other_columns = list(df.columns)
        
        if not question_columns:
            processing_errors.append("No question columns identified in the dataset")
            return ProcessingResults(
                overall_mean=np.nan,
                total_responses=len(df),
                valid_responses=0,
                dimensions={},
                satisfaction_score=None,
                processing_errors=processing_errors,
                question_mapping_issues=question_mapping_issues
            )
        
        # Process each dimension
        dimensions = {}
        all_question_stats = []
        
        for dimension_name, expected_questions in config["dimensions"].items():
            dimension_questions = []
            
            # Find matching columns for this dimension
            for expected_question in expected_questions:
                matching_column = self._find_matching_column(expected_question, question_columns, df)
                
                if matching_column:
                    try:
                        question_stats = self._calculate_question_stats(df[matching_column], expected_question)
                        dimension_questions.append(question_stats)
                        all_question_stats.append(question_stats)
                    except Exception as e:
                        processing_errors.append(f"Error processing question '{expected_question}': {str(e)}")
                else:
                    question_mapping_issues.append(f"Question not found: '{expected_question}'")
            
            # Calculate dimension statistics
            if dimension_questions:
                dimension_mean = np.mean([q.mean_score for q in dimension_questions if not np.isnan(q.mean_score)])
                dimensions[dimension_name] = DimensionStats(
                    dimension_name=dimension_name,
                    mean_score=dimension_mean,
                    question_count=len(dimension_questions),
                    total_responses=0,  # Will be calculated in __post_init__
                    valid_responses=0,  # Will be calculated in __post_init__
                    questions=dimension_questions
                )
        
        # Calculate overall statistics
        valid_means = [q.mean_score for q in all_question_stats if not np.isnan(q.mean_score)]
        overall_mean = np.mean(valid_means) if valid_means else np.nan
        
        total_responses = len(df)
        valid_responses = sum(q.valid_responses for q in all_question_stats)
        
        # Process satisfaction score if available
        satisfaction_score = None
        satisfaction_field = config.get("satisfaction_field")
        if satisfaction_field and satisfaction_field in df.columns:
            try:
                satisfaction_series = self.scale_converter.convert_satisfaction_column(df[satisfaction_field])
                satisfaction_score = satisfaction_series.mean()
            except Exception as e:
                processing_errors.append(f"Error processing satisfaction field: {str(e)}")
        
        return ProcessingResults(
            overall_mean=overall_mean,
            total_responses=total_responses,
            valid_responses=valid_responses,
            dimensions=dimensions,
            satisfaction_score=satisfaction_score,
            processing_errors=processing_errors,
            question_mapping_issues=question_mapping_issues
        )
    
    def _find_matching_column(self, expected_question: str, available_columns: List[str], df: pd.DataFrame) -> Optional[str]:
        """
        Find the column that best matches the expected question.
        
        Args:
            expected_question: The question text we're looking for
            available_columns: List of available column names
            df: DataFrame to check column contents
            
        Returns:
            Best matching column name or None
        """
        # Try exact match first
        if expected_question in available_columns:
            return expected_question
        
        # Try fuzzy matching
        best_match = self.text_normalizer.find_best_match(expected_question, available_columns, threshold=0.3)
        if best_match:
            return best_match
        
        # Try normalized matching
        normalized_expected = self.text_normalizer.normalize_question_text(expected_question)
        for col in available_columns:
            normalized_col = self.text_normalizer.normalize_question_text(col)
            if normalized_expected == normalized_col:
                return col
        
        return None
    
    def _calculate_question_stats(self, series: pd.Series, question_text: str) -> QuestionStats:
        """
        Calculate statistics for a single question.
        
        Args:
            series: Pandas series with responses
            question_text: Text of the question
            
        Returns:
            QuestionStats object
        """
        # Convert to numeric using scale converter
        numeric_series = self.scale_converter.convert_likert_column(series)
        
        # Calculate statistics
        count = len(series)
        valid_responses = numeric_series.notna().sum()
        invalid_responses = count - valid_responses
        
        if valid_responses > 0:
            mean_score = numeric_series.mean()
            std_deviation = numeric_series.std()
        else:
            mean_score = np.nan
            std_deviation = np.nan
        
        return QuestionStats(
            question_text=question_text,
            mean_score=mean_score,
            count=count,
            valid_responses=valid_responses,
            invalid_responses=invalid_responses,
            response_rate=0.0,  # Will be calculated in __post_init__
            std_deviation=std_deviation
        )
    
    def get_dimension_summary(self, results: ProcessingResults) -> pd.DataFrame:
        """
        Create a summary DataFrame of dimension statistics.
        
        Args:
            results: ProcessingResults from process_questionnaire_data
            
        Returns:
            DataFrame with dimension summary
        """
        summary_data = []
        
        for dimension_name, dimension_stats in results.dimensions.items():
            summary_data.append({
                'Dimensão': dimension_name,
                'Média': round(dimension_stats.mean_score, 2) if not np.isnan(dimension_stats.mean_score) else None,
                'Questões': dimension_stats.question_count,
                'Respostas Válidas': dimension_stats.valid_responses,
                'Total Respostas': dimension_stats.total_responses
            })
        
        return pd.DataFrame(summary_data)
    
    def get_question_summary(self, results: ProcessingResults) -> pd.DataFrame:
        """
        Create a detailed DataFrame of question statistics.
        
        Args:
            results: ProcessingResults from process_questionnaire_data
            
        Returns:
            DataFrame with question details
        """
        summary_data = []
        
        for dimension_name, dimension_stats in results.dimensions.items():
            for question_stats in dimension_stats.questions:
                summary_data.append({
                    'Dimensão': dimension_name,
                    'Questão': question_stats.question_text,
                    'Média': round(question_stats.mean_score, 2) if not np.isnan(question_stats.mean_score) else None,
                    'Desvio Padrão': round(question_stats.std_deviation, 2) if not np.isnan(question_stats.std_deviation) else None,
                    'Respostas Válidas': question_stats.valid_responses,
                    'Total Respostas': question_stats.count,
                    'Taxa de Resposta': f"{question_stats.response_rate:.1%}"
                })
        
        return pd.DataFrame(summary_data)
    
    def export_results_to_dict(self, results: ProcessingResults) -> Dict[str, Any]:
        """
        Export results to a dictionary format suitable for JSON serialization.
        
        Args:
            results: ProcessingResults to export
            
        Returns:
            Dictionary with all results
        """
        export_data = {
            'overall_statistics': {
                'overall_mean': results.overall_mean,
                'total_responses': results.total_responses,
                'valid_responses': results.valid_responses,
                'satisfaction_score': results.satisfaction_score
            },
            'dimensions': {},
            'processing_info': {
                'question_set': self.current_question_set,
                'processing_errors': results.processing_errors,
                'question_mapping_issues': results.question_mapping_issues
            }
        }
        
        # Export dimension data
        for dimension_name, dimension_stats in results.dimensions.items():
            export_data['dimensions'][dimension_name] = {
                'mean_score': dimension_stats.mean_score,
                'question_count': dimension_stats.question_count,
                'total_responses': dimension_stats.total_responses,
                'valid_responses': dimension_stats.valid_responses,
                'questions': [
                    {
                        'question_text': q.question_text,
                        'mean_score': q.mean_score,
                        'count': q.count,
                        'valid_responses': q.valid_responses,
                        'response_rate': q.response_rate,
                        'std_deviation': q.std_deviation
                    }
                    for q in dimension_stats.questions
                ]
            }
        
        return export_data
    
    def filter_by_question_set(self, df: pd.DataFrame, target_question_set: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Filter DataFrame to include only questions from the target question set.
        
        This simulates the sidebar filter functionality where users can switch
        between "Completo", "20 questões", and "8 questões".
        
        Args:
            df: Original DataFrame with all questions
            target_question_set: Target question set ("base20" or "base8")
            
        Returns:
            Tuple of (filtered_dataframe, removed_columns)
        """
        if target_question_set not in ["base20", "base8"]:
            raise ValueError(f"Invalid target question set: {target_question_set}")
        
        # Load target configuration
        target_config = self.load_configuration(target_question_set)
        target_questions = []
        
        # Get all questions from target configuration
        for dimension_questions in target_config["dimensions"].values():
            target_questions.extend(dimension_questions)
        
        # Identify columns to keep
        columns_to_keep = []
        columns_to_remove = []
        
        for col in df.columns:
            # Always keep non-question columns (profile, satisfaction, etc.)
            if not self._is_question_column(col, df):
                columns_to_keep.append(col)
                continue
            
            # Check if this question should be included in target set
            should_keep = False
            
            # Try exact match first
            if col in target_questions:
                should_keep = True
            else:
                # Try fuzzy matching with lower threshold for better matching
                best_match = self.text_normalizer.find_best_match(col, target_questions, threshold=0.3)
                if best_match:
                    should_keep = True
                else:
                    # For base8, be more restrictive - only keep questions that clearly match base8 patterns
                    if target_question_set == "base8":
                        # Base8 specific patterns (Portal questions)
                        base8_patterns = ["portal", "dados", "informações no portal", "navegação pelo portal"]
                        col_lower = col.lower()
                        
                        # Check if it's a base8-specific question
                        if any(pattern in col_lower for pattern in base8_patterns):
                            should_keep = True
                        # Or if it matches the single operation question
                        elif "consigo obter o que preciso" in col_lower:
                            should_keep = True
                        # Or if it's one of the core system/info questions that exist in base8
                        elif any(core in col_lower for core in ["fácil de usar", "informações são claras", "informações são precisas", "atualizadas"]):
                            should_keep = True
                        else:
                            should_keep = False
                    else:
                        # For base20, be more inclusive
                        should_keep = True
            
            if should_keep:
                columns_to_keep.append(col)
            else:
                columns_to_remove.append(col)
        
        # For base8, ensure we don't keep too many questions (should be around 8 + profile/satisfaction)
        if target_question_set == "base8":
            question_cols = [col for col in columns_to_keep if self._is_question_column(col, df)]
            if len(question_cols) > 8:
                # Keep only the first 8 question columns that match base8 patterns
                base8_priority_patterns = [
                    "portal.*fácil",
                    "localizar.*dados",
                    "navegação.*portal", 
                    "portal.*falhas",
                    "informações.*claras",
                    "informações.*precisas",
                    "informações.*atualizadas",
                    "consigo obter"
                ]
                
                prioritized_questions = []
                remaining_questions = question_cols.copy()
                
                # First, add questions that match priority patterns
                for pattern in base8_priority_patterns:
                    import re
                    for col in remaining_questions[:]:
                        if re.search(pattern, col.lower()):
                            prioritized_questions.append(col)
                            remaining_questions.remove(col)
                            if len(prioritized_questions) >= 8:
                                break
                    if len(prioritized_questions) >= 8:
                        break
                
                # Add remaining questions if needed
                while len(prioritized_questions) < 8 and remaining_questions:
                    prioritized_questions.append(remaining_questions.pop(0))
                
                # Update columns to keep
                non_question_cols = [col for col in columns_to_keep if not self._is_question_column(col, df)]
                columns_to_keep = non_question_cols + prioritized_questions[:8]
                
                # Update columns to remove
                all_question_cols = [col for col in df.columns if self._is_question_column(col, df)]
                columns_to_remove = [col for col in all_question_cols if col not in prioritized_questions[:8]]
        
        # Create filtered DataFrame
        filtered_df = df[columns_to_keep].copy()
        
        return filtered_df, columns_to_remove
    
    def _is_question_column(self, column_name: str, df: pd.DataFrame) -> bool:
        """
        Determine if a column contains questionnaire questions.
        
        Args:
            column_name: Name of the column
            df: DataFrame to check column contents
            
        Returns:
            True if column appears to contain questionnaire responses
        """
        # Check if it's obviously not a question
        non_question_indicators = [
            'timestamp', 'id', 'user_id', 'session_id', 'sexo', 'idade', 
            'escolaridade', 'funcionario', 'servidor', 'satisfação', 'satisfaction',
            'comentario', 'comment'
        ]
        
        col_lower = column_name.lower()
        if any(indicator in col_lower for indicator in non_question_indicators):
            return False
        
        # Check if column contains Likert-like responses
        return self._contains_likert_responses(df[column_name])
    
    def compare_question_sets(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare how the same data would be processed with different question sets.
        
        Args:
            df: Original DataFrame
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "original_data": {
                "total_columns": len(df.columns),
                "total_rows": len(df)
            },
            "question_sets": {}
        }
        
        for question_set in ["base20", "base8"]:
            try:
                # Filter data for this question set
                filtered_df, removed_cols = self.filter_by_question_set(df, question_set)
                
                # Process the filtered data
                results = self.process_questionnaire_data(filtered_df, question_set)
                
                # Get structure report
                structure_report = self.get_dimension_structure_report()
                
                comparison["question_sets"][question_set] = {
                    "filtered_columns": len(filtered_df.columns),
                    "removed_columns": len(removed_cols),
                    "removed_column_names": removed_cols[:5],  # First 5 for brevity
                    "overall_mean": results.overall_mean,
                    "satisfaction_score": results.satisfaction_score,
                    "dimensions": {
                        name: {
                            "mean_score": stats.mean_score,
                            "question_count": stats.question_count,
                            "valid_responses": stats.valid_responses
                        }
                        for name, stats in results.dimensions.items()
                    },
                    "structure_validation": structure_report.get("validation", {}),
                    "processing_errors": len(results.processing_errors),
                    "mapping_issues": len(results.question_mapping_issues)
                }
                
            except Exception as e:
                comparison["question_sets"][question_set] = {
                    "error": str(e)
                }
        
        return comparison
    
    def get_sidebar_filter_options(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the available filter options that would appear in the sidebar.
        
        Returns:
            Dictionary with filter options and their details
        """
        filter_options = {
            "Completo (26 questões)": {
                "question_set": "base26",
                "description": "Conjunto completo de questões",
                "dimensions": {
                    "QS": 10,
                    "QI": 7, 
                    "QO": 9
                },
                "total_questions": 26,
                "available": False,  # Not implemented yet
                "note": "Configuração completa não disponível"
            },
            "20 questões": {
                "question_set": "base20",
                "description": "Conjunto reduzido (remove 6 questões específicas)",
                "dimensions": {
                    "QS": 10,  # Actually has 10 in current config
                    "QI": 7,   # Actually has 7 in current config
                    "QO": 9    # Actually has 9 in current config
                },
                "total_questions": 26,  # Current config actually has 26
                "available": True,
                "note": "Configuração atual tem 26 questões (não 20)"
            },
            "8 questões": {
                "question_set": "base8",
                "description": "Conjunto mínimo para Portal da Transparência",
                "dimensions": {
                    "QS": 4,
                    "QI": 3,
                    "QO": 1
                },
                "total_questions": 8,
                "available": True,
                "note": "Configuração correta"
            }
        }
        
        return filter_options