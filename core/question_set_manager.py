"""
Question Set Manager for handling different questionnaire configurations

This module manages the filtering and processing of different question sets
(26 questions, 20 questions, 8 questions) with proper dimension organization.
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
from .questionnaire_processor import QuestionnaireProcessor


class QuestionSetManager:
    """
    Manages different question sets and their filtering logic.
    
    Handles the transition between 26, 20, and 8 question configurations
    while maintaining proper dimension structure.
    """
    
    # Questions to remove for 20-question set
    QUESTIONS_TO_REMOVE_FOR_20 = [
        "O sistema está disponível para uso em qualquer dia e hora.",  # QS4
        "O prazo de entrega dos serviços é informado.",  # QI5
        "As taxas cobradas pelos serviços são informadas.",  # QI6
        "As informações disponibilizadas estão atualizadas.",  # QI7
        "Os serviços oferecidos são confiáveis.",  # QO8
        "Os serviços permitem interações em tempo real (ex. chatbot, IA)."  # QO9
    ]
    
    def __init__(self):
        """Initialize the QuestionSetManager"""
        self.processor = QuestionnaireProcessor()
        self.current_question_set = None
        self.current_config = None
    
    def get_question_set_info(self, question_set: str) -> Dict[str, int]:
        """
        Get information about a specific question set.
        
        Args:
            question_set: "26 questões", "20 questões", or "8 questões"
            
        Returns:
            Dictionary with dimension counts
        """
        if question_set == "26 questões" or question_set == "Completo":
            return {
                "Qualidade do Sistema": 10,
                "Qualidade da Informação": 7,
                "Qualidade da Operação": 9,
                "total": 26
            }
        elif question_set == "20 questões":
            return {
                "Qualidade do Sistema": 9,  # Remove 1 (QS4)
                "Qualidade da Informação": 4,  # Remove 3 (QI5, QI6, QI7)
                "Qualidade da Operação": 7,  # Remove 2 (QO8, QO9)
                "total": 20
            }
        elif question_set == "8 questões":
            return {
                "Qualidade do Sistema": 4,
                "Qualidade da Informação": 3,
                "Qualidade da Operação": 1,
                "total": 8
            }
        else:
            raise ValueError(f"Unknown question set: {question_set}")
    
    def filter_dataframe_by_question_set(self, df: pd.DataFrame, question_set: str) -> pd.DataFrame:
        """
        Filter DataFrame based on question set selection.
        
        Args:
            df: Input DataFrame
            question_set: "26 questões", "20 questões", or "8 questões"
            
        Returns:
            Filtered DataFrame
        """
        if question_set == "26 questões" or question_set == "Completo":
            # Return complete dataset
            return df
        
        elif question_set == "20 questões":
            # Remove specific 6 questions to get 20
            cols_to_keep = [col for col in df.columns if col not in self.QUESTIONS_TO_REMOVE_FOR_20]
            return df[cols_to_keep]
        
        elif question_set == "8 questões":
            # This should load a different dataset entirely
            # For now, return the input df (this would be handled by the calling code)
            return df
        
        else:
            raise ValueError(f"Unknown question set: {question_set}")
    
    def process_questionnaire_with_question_set(self, df: pd.DataFrame, question_set: str):
        """
        Process questionnaire data with specific question set configuration.
        
        Args:
            df: Input DataFrame
            question_set: "26 questões", "20 questões", or "8 questões"
            
        Returns:
            ProcessingResults from QuestionnaireProcessor
        """
        # Filter DataFrame first
        filtered_df = self.filter_dataframe_by_question_set(df, question_set)
        
        # Determine which configuration to use
        if question_set == "8 questões":
            config_type = "base8"
        else:
            # Both 26 and 20 questions use the same base configuration
            config_type = "base20"
        
        # Process with QuestionnaireProcessor
        results = self.processor.process_questionnaire_data(filtered_df, config_type)
        
        # Add metadata about question set
        results.question_set_used = question_set
        results.expected_structure = self.get_question_set_info(question_set)
        
        return results
    
    def validate_question_set_structure(self, df: pd.DataFrame, question_set: str) -> Dict[str, any]:
        """
        Validate that DataFrame matches expected question set structure.
        
        Args:
            df: Input DataFrame
            question_set: Expected question set
            
        Returns:
            Validation results dictionary
        """
        expected_info = self.get_question_set_info(question_set)
        
        # Process the data to get actual structure
        try:
            results = self.process_questionnaire_with_question_set(df, question_set)
            
            validation = {
                "valid": True,
                "expected_total": expected_info["total"],
                "actual_questions_found": sum(dim.question_count for dim in results.dimensions.values()),
                "dimension_validation": {},
                "issues": []
            }
            
            # Validate each dimension
            for dim_name, expected_count in expected_info.items():
                if dim_name == "total":
                    continue
                
                if dim_name in results.dimensions:
                    actual_count = results.dimensions[dim_name].question_count
                    validation["dimension_validation"][dim_name] = {
                        "expected": expected_count,
                        "actual": actual_count,
                        "valid": actual_count == expected_count
                    }
                    
                    if actual_count != expected_count:
                        validation["valid"] = False
                        validation["issues"].append(
                            f"{dim_name}: esperado {expected_count}, encontrado {actual_count}"
                        )
                else:
                    validation["valid"] = False
                    validation["dimension_validation"][dim_name] = {
                        "expected": expected_count,
                        "actual": 0,
                        "valid": False
                    }
                    validation["issues"].append(f"{dim_name}: dimensão não encontrada")
            
            # Add processing issues
            if results.processing_errors:
                validation["issues"].extend(results.processing_errors)
            
            if results.question_mapping_issues:
                validation["issues"].extend(results.question_mapping_issues)
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "expected_total": expected_info["total"],
                "actual_questions_found": 0,
                "dimension_validation": {},
                "issues": [f"Erro no processamento: {str(e)}"]
            }
    
    def get_dimension_summary_for_question_set(self, df: pd.DataFrame, question_set: str) -> pd.DataFrame:
        """
        Get dimension summary for specific question set.
        
        Args:
            df: Input DataFrame
            question_set: Question set to analyze
            
        Returns:
            DataFrame with dimension summary
        """
        results = self.process_questionnaire_with_question_set(df, question_set)
        return self.processor.get_dimension_summary(results)
    
    def get_question_summary_for_question_set(self, df: pd.DataFrame, question_set: str) -> pd.DataFrame:
        """
        Get question summary for specific question set.
        
        Args:
            df: Input DataFrame
            question_set: Question set to analyze
            
        Returns:
            DataFrame with question summary
        """
        results = self.process_questionnaire_with_question_set(df, question_set)
        return self.processor.get_question_summary(results)
    
    def compare_question_sets(self, df_26: pd.DataFrame, df_8: Optional[pd.DataFrame] = None) -> Dict[str, any]:
        """
        Compare results across different question sets.
        
        Args:
            df_26: DataFrame with 26 questions
            df_8: Optional DataFrame with 8 questions
            
        Returns:
            Comparison results
        """
        comparison = {
            "question_sets": {},
            "dimension_comparison": {}
        }
        
        # Process 26 questions
        results_26 = self.process_questionnaire_with_question_set(df_26, "26 questões")
        comparison["question_sets"]["26 questões"] = {
            "overall_mean": results_26.overall_mean,
            "total_responses": results_26.total_responses,
            "dimensions": {name: stats.mean_score for name, stats in results_26.dimensions.items()}
        }
        
        # Process 20 questions (filtered from 26)
        results_20 = self.process_questionnaire_with_question_set(df_26, "20 questões")
        comparison["question_sets"]["20 questões"] = {
            "overall_mean": results_20.overall_mean,
            "total_responses": results_20.total_responses,
            "dimensions": {name: stats.mean_score for name, stats in results_20.dimensions.items()}
        }
        
        # Process 8 questions if available
        if df_8 is not None:
            results_8 = self.process_questionnaire_with_question_set(df_8, "8 questões")
            comparison["question_sets"]["8 questões"] = {
                "overall_mean": results_8.overall_mean,
                "total_responses": results_8.total_responses,
                "dimensions": {name: stats.mean_score for name, stats in results_8.dimensions.items()}
            }
        
        # Create dimension comparison
        for dimension_name in ["Qualidade do Sistema", "Qualidade da Informação", "Qualidade da Operação"]:
            comparison["dimension_comparison"][dimension_name] = {}
            
            if dimension_name in results_26.dimensions:
                comparison["dimension_comparison"][dimension_name]["26 questões"] = results_26.dimensions[dimension_name].mean_score
            
            if dimension_name in results_20.dimensions:
                comparison["dimension_comparison"][dimension_name]["20 questões"] = results_20.dimensions[dimension_name].mean_score
            
            if df_8 is not None and dimension_name in results_8.dimensions:
                comparison["dimension_comparison"][dimension_name]["8 questões"] = results_8.dimensions[dimension_name].mean_score
        
        return comparison
    
    def get_removed_questions_info(self) -> Dict[str, List[str]]:
        """
        Get information about which questions are removed in each configuration.
        
        Returns:
            Dictionary with removed questions by dimension
        """
        return {
            "20_questoes_removidas": self.QUESTIONS_TO_REMOVE_FOR_20,
            "por_dimensao": {
                "Qualidade do Sistema": [
                    "O sistema está disponível para uso em qualquer dia e hora."  # QS4
                ],
                "Qualidade da Informação": [
                    "O prazo de entrega dos serviços é informado.",  # QI5
                    "As taxas cobradas pelos serviços são informadas.",  # QI6
                    "As informações disponibilizadas estão atualizadas."  # QI7
                ],
                "Qualidade da Operação": [
                    "Os serviços oferecidos são confiáveis.",  # QO8
                    "Os serviços permitem interações em tempo real (ex. chatbot, IA)."  # QO9
                ]
            }
        }