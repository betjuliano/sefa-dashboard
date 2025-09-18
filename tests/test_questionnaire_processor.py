"""
Unit tests for QuestionnaireProcessor class

Tests questionnaire data processing, mean calculations, dimension organization,
and integration with ScaleConverter and configuration files.
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from core.questionnaire_processor import (
    QuestionnaireProcessor, 
    QuestionStats, 
    DimensionStats, 
    ProcessingResults
)


class TestQuestionStats:
    """Test cases for QuestionStats dataclass"""
    
    def test_question_stats_creation(self):
        """Test QuestionStats creation and response rate calculation"""
        stats = QuestionStats(
            question_text="Test question",
            mean_score=4.2,
            count=100,
            valid_responses=85,
            invalid_responses=15,
            response_rate=0.0,  # Will be calculated
            std_deviation=1.1
        )
        
        assert stats.response_rate == 0.85
        assert stats.question_text == "Test question"
        assert stats.mean_score == 4.2
    
    def test_question_stats_zero_count(self):
        """Test QuestionStats with zero count"""
        stats = QuestionStats(
            question_text="Empty question",
            mean_score=np.nan,
            count=0,
            valid_responses=0,
            invalid_responses=0,
            response_rate=0.0,
            std_deviation=np.nan
        )
        
        assert stats.response_rate == 0.0


class TestDimensionStats:
    """Test cases for DimensionStats dataclass"""
    
    def test_dimension_stats_creation(self):
        """Test DimensionStats creation and calculation"""
        question1 = QuestionStats("Q1", 4.0, 100, 90, 10, 0.9, 1.0)
        question2 = QuestionStats("Q2", 3.5, 100, 85, 15, 0.85, 1.2)
        
        dimension = DimensionStats(
            dimension_name="Test Dimension",
            mean_score=3.75,
            question_count=0,  # Will be calculated
            total_responses=0,  # Will be calculated
            valid_responses=0,  # Will be calculated
            questions=[question1, question2]
        )
        
        assert dimension.question_count == 2
        assert dimension.total_responses == 200
        assert dimension.valid_responses == 175


class TestQuestionnaireProcessor:
    """Test cases for QuestionnaireProcessor class"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            "dimensions": {
                "Qualidade do Sistema": [
                    "O sistema é fácil de usar.",
                    "O sistema funciona sem falhas."
                ],
                "Qualidade da Informação": [
                    "As informações são claras.",
                    "As informações são precisas."
                ]
            },
            "likert_map": {
                "Discordo totalmente": 1,
                "Discordo": 2,
                "Indiferente": 3,
                "Concordo": 4,
                "Concordo totalmente": 5,
                "Não sei": None
            },
            "satisfaction_field": "Qual o seu nível de satisfação?",
            "satisfaction_map": {
                "Muito insatisfeito": 1,
                "Insatisfeito": 2,
                "Indiferente": 3,
                "Satisfeito": 4,
                "Muito satisfeito": 5
            },
            "profile_fields": {
                "Sexo": "Qual o seu sexo?",
                "Idade": "Qual a sua idade?"
            }
        }
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing"""
        return pd.DataFrame({
            "O sistema é fácil de usar.": [
                "Concordo totalmente", "Concordo", "Indiferente", 
                "Concordo", "Concordo totalmente"
            ],
            "O sistema funciona sem falhas.": [
                "Concordo", "Concordo totalmente", "Concordo",
                "Discordo", "Concordo"
            ],
            "As informações são claras.": [
                "Concordo totalmente", "Concordo totalmente", "Concordo",
                "Concordo", "Concordo totalmente"
            ],
            "As informações são precisas.": [
                "Concordo", "Concordo", "Concordo totalmente",
                "Indiferente", "Concordo"
            ],
            "Qual o seu nível de satisfação?": [
                "Muito satisfeito", "Satisfeito", "Satisfeito",
                "Indiferente", "Muito satisfeito"
            ],
            "Qual o seu sexo?": [
                "Masculino", "Feminino", "Masculino",
                "Feminino", "Masculino"
            ]
        })
    
    def test_processor_initialization(self):
        """Test QuestionnaireProcessor initialization"""
        processor = QuestionnaireProcessor()
        
        assert processor.config_path == Path("config")
        assert processor.scale_converter is not None
        assert processor.text_normalizer is not None
        assert processor.current_config is None
    
    def test_load_configuration_base20(self, sample_config):
        """Test loading base20 configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            loaded_config = processor.load_configuration("base20")
            
            assert loaded_config == sample_config
            assert processor.current_config == sample_config
            assert processor.current_question_set == "base20"
    
    def test_load_configuration_base8(self, sample_config):
        """Test loading base8 configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping_8q.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            loaded_config = processor.load_configuration("base8")
            
            assert loaded_config == sample_config
            assert processor.current_question_set == "base8"
    
    def test_load_configuration_invalid_set(self):
        """Test loading configuration with invalid question set"""
        processor = QuestionnaireProcessor()
        
        with pytest.raises(ValueError, match="Invalid question set"):
            processor.load_configuration("invalid")
    
    def test_load_configuration_file_not_found(self):
        """Test loading configuration when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = QuestionnaireProcessor(temp_dir)
            
            with pytest.raises(FileNotFoundError):
                processor.load_configuration("base20")
    
    def test_identify_question_columns(self, sample_config, sample_dataframe):
        """Test identification of question vs non-question columns"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            processor.load_configuration("base20")
            
            question_cols, other_cols = processor.identify_question_columns(sample_dataframe)
            
            # Should identify the 4 question columns
            expected_questions = [
                "O sistema é fácil de usar.",
                "O sistema funciona sem falhas.",
                "As informações são claras.",
                "As informações são precisas."
            ]
            
            assert len(question_cols) == 4
            for expected in expected_questions:
                assert expected in question_cols
            
            # Should identify satisfaction and profile as other columns
            assert "Qual o seu nível de satisfação?" in other_cols
            assert "Qual o seu sexo?" in other_cols
    
    def test_contains_likert_responses(self):
        """Test detection of Likert-like responses"""
        processor = QuestionnaireProcessor()
        
        # Series with Likert responses
        likert_series = pd.Series(["Concordo", "Discordo", "Concordo totalmente"])
        assert processor._contains_likert_responses(likert_series) == True
        
        # Series without Likert responses
        non_likert_series = pd.Series(["Masculino", "Feminino", "Outro"])
        assert processor._contains_likert_responses(non_likert_series) == False
        
        # Empty series
        empty_series = pd.Series([])
        assert processor._contains_likert_responses(empty_series) == False
    
    def test_calculate_question_stats(self, sample_config):
        """Test calculation of statistics for a single question"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            processor.load_configuration("base20")
            
            # Test series with known responses
            test_series = pd.Series([
                "Concordo totalmente",  # 5
                "Concordo",             # 4
                "Indiferente",          # 3
                "Concordo",             # 4
                "Invalid response"      # NaN
            ])
            
            stats = processor._calculate_question_stats(test_series, "Test Question")
            
            assert stats.question_text == "Test Question"
            assert stats.count == 5
            assert stats.valid_responses == 4
            assert stats.invalid_responses == 1
            assert stats.mean_score == 4.0  # (5+4+3+4)/4
            assert stats.response_rate == 0.8
    
    def test_process_questionnaire_data_complete(self, sample_config, sample_dataframe):
        """Test complete questionnaire data processing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            results = processor.process_questionnaire_data(sample_dataframe, "base20")
            
            # Check overall results
            assert isinstance(results, ProcessingResults)
            assert not np.isnan(results.overall_mean)
            assert results.total_responses == 5
            assert results.valid_responses > 0
            
            # Check dimensions
            assert len(results.dimensions) == 2
            assert "Qualidade do Sistema" in results.dimensions
            assert "Qualidade da Informação" in results.dimensions
            
            # Check dimension statistics
            qs_dimension = results.dimensions["Qualidade do Sistema"]
            assert qs_dimension.question_count == 2
            assert len(qs_dimension.questions) == 2
            
            qi_dimension = results.dimensions["Qualidade da Informação"]
            assert qi_dimension.question_count == 2
            assert len(qi_dimension.questions) == 2
            
            # Check satisfaction score
            assert results.satisfaction_score is not None
            assert not np.isnan(results.satisfaction_score)
    
    def test_get_dimension_summary(self, sample_config, sample_dataframe):
        """Test dimension summary DataFrame creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            results = processor.process_questionnaire_data(sample_dataframe, "base20")
            
            summary_df = processor.get_dimension_summary(results)
            
            assert isinstance(summary_df, pd.DataFrame)
            assert len(summary_df) == 2
            assert "Dimensão" in summary_df.columns
            assert "Média" in summary_df.columns
            assert "Questões" in summary_df.columns
    
    def test_get_question_summary(self, sample_config, sample_dataframe):
        """Test question summary DataFrame creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            results = processor.process_questionnaire_data(sample_dataframe, "base20")
            
            summary_df = processor.get_question_summary(results)
            
            assert isinstance(summary_df, pd.DataFrame)
            assert len(summary_df) == 4  # 4 questions total
            assert "Dimensão" in summary_df.columns
            assert "Questão" in summary_df.columns
            assert "Média" in summary_df.columns
            assert "Taxa de Resposta" in summary_df.columns
    
    def test_export_results_to_dict(self, sample_config, sample_dataframe):
        """Test exporting results to dictionary format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            results = processor.process_questionnaire_data(sample_dataframe, "base20")
            
            export_dict = processor.export_results_to_dict(results)
            
            assert "overall_statistics" in export_dict
            assert "dimensions" in export_dict
            assert "processing_info" in export_dict
            
            # Check overall statistics
            overall_stats = export_dict["overall_statistics"]
            assert "overall_mean" in overall_stats
            assert "total_responses" in overall_stats
            assert "satisfaction_score" in overall_stats
            
            # Check dimensions
            dimensions = export_dict["dimensions"]
            assert len(dimensions) == 2
            
            for dimension_name, dimension_data in dimensions.items():
                assert "mean_score" in dimension_data
                assert "questions" in dimension_data
                assert len(dimension_data["questions"]) > 0
    
    def test_error_handling_no_questions(self, sample_config):
        """Test error handling when no questions are found"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            
            # DataFrame with no question columns
            no_questions_df = pd.DataFrame({
                "Random Column 1": [1, 2, 3],
                "Random Column 2": ["A", "B", "C"]
            })
            
            results = processor.process_questionnaire_data(no_questions_df, "base20")
            
            assert np.isnan(results.overall_mean)
            assert results.valid_responses == 0
            assert len(results.dimensions) == 0
            assert len(results.processing_errors) > 0
    
    def test_missing_questions_handling(self, sample_config):
        """Test handling of missing questions"""
        # Modify config to expect more questions than available
        modified_config = sample_config.copy()
        modified_config["dimensions"]["Qualidade do Sistema"].append("Missing question")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir)
            config_file = config_path / "items_mapping.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(modified_config, f)
            
            processor = QuestionnaireProcessor(config_path)
            
            # DataFrame with only some questions
            partial_df = pd.DataFrame({
                "O sistema é fácil de usar.": ["Concordo", "Concordo totalmente"],
                "Random Column": ["A", "B"]
            })
            
            results = processor.process_questionnaire_data(partial_df, "base20")
            
            # Should have mapping issues for missing questions
            assert len(results.question_mapping_issues) > 0
            assert any("Missing question" in issue for issue in results.question_mapping_issues)


class TestQuestionnaireProcessorIntegration:
    """Integration tests with real configuration files"""
    
    def test_with_real_base20_config(self):
        """Test with actual base20 configuration file"""
        try:
            processor = QuestionnaireProcessor("config")
            config = processor.load_configuration("base20")
            
            # Should load successfully
            assert "dimensions" in config
            assert "likert_map" in config
            assert len(config["dimensions"]) >= 3  # QS, QI, QO
            
        except FileNotFoundError:
            pytest.skip("Real configuration files not available")
    
    def test_with_real_base8_config(self):
        """Test with actual base8 configuration file"""
        try:
            processor = QuestionnaireProcessor("config")
            config = processor.load_configuration("base8")
            
            # Should load successfully
            assert "dimensions" in config
            assert "likert_map" in config
            assert len(config["dimensions"]) >= 3  # QS, QI, QO
            
        except FileNotFoundError:
            pytest.skip("Real configuration files not available")
    
    def test_realistic_data_processing(self):
        """Test with realistic questionnaire data"""
        try:
            processor = QuestionnaireProcessor("config")
            
            # Create realistic sample data
            realistic_data = pd.DataFrame({
                "O sistema é fácil de usar.": [
                    "Concordo totalmente", "Concordo", "Indiferente",
                    "Concordo", "Concordo totalmente", "Discordo",
                    "Concordo", "Concordo totalmente", "Concordo", "Indiferente"
                ],
                "As informações são claras.": [
                    "Concordo", "Concordo totalmente", "Concordo",
                    "Indiferente", "Concordo", "Concordo totalmente",
                    "Concordo", "Discordo", "Concordo", "Concordo"
                ],
                "Timestamp": pd.date_range("2024-01-01", periods=10),
                "User_ID": range(1, 11)
            })
            
            results = processor.process_questionnaire_data(realistic_data, "base20")
            
            # Should process successfully
            assert not np.isnan(results.overall_mean)
            assert results.total_responses == 10
            assert len(results.dimensions) > 0
            
        except FileNotFoundError:
            pytest.skip("Real configuration files not available")


if __name__ == "__main__":
    pytest.main([__file__])