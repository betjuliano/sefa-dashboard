"""
Unit tests for ScaleConverter class

Tests all scale conversion scenarios including Likert scales, satisfaction scales,
validation, error handling, and edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from core.scale_converter import ScaleConverter, ScaleStats


class TestScaleConverter:
    """Test cases for ScaleConverter class"""
    
    def test_default_initialization(self):
        """Test ScaleConverter initialization with default mapping"""
        converter = ScaleConverter()
        assert converter.scale_mapping is not None
        assert len(converter.scale_mapping) > 0
        assert "concordo totalmente" in converter.scale_mapping
        assert converter.scale_mapping["concordo totalmente"] == 5
    
    def test_custom_mapping_initialization(self):
        """Test ScaleConverter initialization with custom mapping"""
        custom_mapping = {"sim": 1, "nao": 0}
        converter = ScaleConverter(custom_mapping)
        assert "sim" in converter.scale_mapping
        assert converter.scale_mapping["sim"] == 1
    
    def test_likert_scale_conversion_basic(self):
        """Test basic Likert scale conversion (Requirements 2.1-2.5)"""
        converter = ScaleConverter()
        
        # Test all basic Likert responses
        test_data = pd.Series([
            "Discordo totalmente",
            "Discordo", 
            "Não sei",
            "Concordo",
            "Concordo totalmente"
        ])
        
        result = converter.convert_likert_column(test_data)
        expected = [1, 2, 3, 4, 5]
        
        assert result.tolist() == expected
    
    def test_likert_scale_conversion_with_accents(self):
        """Test Likert scale conversion with Portuguese accents"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Discordo totalmente",
            "Não sei",
            "Concordo totalmente"
        ])
        
        result = converter.convert_likert_column(test_data)
        expected = [1, 3, 5]
        
        assert result.tolist() == expected
    
    def test_likert_scale_conversion_case_insensitive(self):
        """Test case insensitive Likert scale conversion"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "CONCORDO TOTALMENTE",
            "discordo totalmente",
            "Concordo",
            "DISCORDO"
        ])
        
        result = converter.convert_likert_column(test_data)
        expected = [5, 1, 4, 2]
        
        assert result.tolist() == expected
    
    def test_likert_scale_conversion_with_whitespace(self):
        """Test Likert scale conversion with extra whitespace"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "  Concordo totalmente  ",
            "\tDiscordo\t",
            " Não sei "
        ])
        
        result = converter.convert_likert_column(test_data)
        expected = [5, 2, 3]
        
        assert result.tolist() == expected
    
    def test_invalid_values_handling(self):
        """Test handling of invalid values (Requirement 2.6)"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Concordo",
            "Invalid response",
            "Random text",
            "123",
            ""
        ])
        
        result = converter.convert_likert_column(test_data)
        
        # First value should convert, others should be NaN
        assert result.iloc[0] == 4
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])
        assert pd.isna(result.iloc[3])
        assert pd.isna(result.iloc[4])
    
    def test_null_values_handling(self):
        """Test handling of null/NaN values (Requirement 2.6)"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Concordo",
            None,
            np.nan,
            "Discordo"
        ])
        
        result = converter.convert_likert_column(test_data)
        
        assert result.iloc[0] == 4
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])
        assert result.iloc[3] == 2
    
    def test_satisfaction_scale_conversion(self):
        """Test satisfaction scale conversion"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Muito insatisfeito",
            "Insatisfeito",
            "Indiferente", 
            "Satisfeito",
            "Muito satisfeito"
        ])
        
        result = converter.convert_satisfaction_column(test_data)
        expected = [1, 2, 3, 4, 5]
        
        assert result.tolist() == expected
    
    def test_neutral_responses(self):
        """Test various neutral response formats"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Não sei",
            "Neutro",
            "Indiferente",
            "Nem concordo nem discordo"
        ])
        
        result = converter.convert_likert_column(test_data)
        
        # All should map to 3 (neutral)
        for value in result:
            assert value == 3
    
    def test_scale_statistics(self):
        """Test scale conversion statistics"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Concordo",
            "Discordo", 
            "Invalid",
            None,
            "Concordo totalmente"
        ])
        
        stats = converter.get_scale_statistics(test_data)
        
        assert stats.total_values == 5
        assert stats.converted_values == 3  # Concordo, Discordo, Concordo totalmente
        assert stats.invalid_values == 1    # Invalid
        assert stats.null_values == 1       # None
        assert stats.conversion_rate == 0.6  # 3/5
        assert "Invalid" in stats.invalid_items
    
    def test_scale_validation(self):
        """Test scale value validation"""
        converter = ScaleConverter()
        
        # Test with mostly valid data
        valid_data = pd.Series(["Concordo", "Discordo", "Concordo totalmente"])
        issues = converter.validate_scale_values(valid_data)
        assert len(issues) == 0
        
        # Test with mostly invalid data
        invalid_data = pd.Series(["Invalid1", "Invalid2", "Concordo"])
        issues = converter.validate_scale_values(invalid_data)
        assert len(issues) > 0
        assert any("Low conversion rate" in issue for issue in issues)
    
    def test_empty_series(self):
        """Test handling of empty series"""
        converter = ScaleConverter()
        
        empty_series = pd.Series([], dtype=str)
        result = converter.convert_likert_column(empty_series)
        
        assert len(result) == 0
        assert result.dtype == float
    
    def test_create_likert_converter(self):
        """Test factory method for Likert converter"""
        converter = ScaleConverter.create_likert_converter()
        
        test_data = pd.Series(["Concordo totalmente", "Discordo"])
        result = converter.convert_likert_column(test_data)
        
        assert result.tolist() == [5, 2]
    
    def test_create_satisfaction_converter(self):
        """Test factory method for satisfaction converter"""
        converter = ScaleConverter.create_satisfaction_converter()
        
        test_data = pd.Series(["Muito satisfeito", "Insatisfeito"])
        result = converter.convert_likert_column(test_data)
        
        assert result.tolist() == [5, 2]
    
    def test_create_from_config(self):
        """Test creating converter from configuration"""
        config = {
            "likert_map": {
                "Sim": 1,
                "Não": 0,
                "Talvez": None
            }
        }
        
        converter = ScaleConverter.create_from_config(config)
        
        test_data = pd.Series(["Sim", "Não", "Talvez"])
        result = converter.convert_likert_column(test_data)
        
        assert result.iloc[0] == 1
        assert result.iloc[1] == 0
        assert pd.isna(result.iloc[2])
    
    def test_add_scale_mapping(self):
        """Test adding new scale mappings"""
        converter = ScaleConverter()
        
        # Add custom mapping
        converter.add_scale_mapping("Excelente", 5)
        
        test_data = pd.Series(["Excelente", "Concordo"])
        result = converter.convert_likert_column(test_data)
        
        assert result.iloc[0] == 5
        assert result.iloc[1] == 4
    
    def test_remove_scale_mapping(self):
        """Test removing scale mappings"""
        converter = ScaleConverter()
        
        # Add a custom mapping first
        converter.add_scale_mapping("Custom Response", 9)
        
        # Test that it works
        test_data = pd.Series(["Custom Response"])
        result = converter.convert_likert_column(test_data)
        assert result.iloc[0] == 9
        
        # Remove the custom mapping
        success = converter.remove_scale_mapping("Custom Response")
        assert success == True
        
        # Try to remove non-existent mapping
        success = converter.remove_scale_mapping("Non-existent")
        assert success == False
        
        # Test that removed mapping no longer works
        test_data = pd.Series(["Custom Response"])
        result = converter.convert_likert_column(test_data)
        assert pd.isna(result.iloc[0])
    
    def test_get_valid_scale_values(self):
        """Test getting list of valid scale values"""
        converter = ScaleConverter()
        
        valid_values = converter.get_valid_scale_values()
        
        assert isinstance(valid_values, list)
        assert len(valid_values) > 0
        assert "concordo totalmente" in valid_values
    
    def test_aliases_matching(self):
        """Test that scale aliases work correctly"""
        converter = ScaleConverter()
        
        # Test various aliases for the same concept
        test_data = pd.Series([
            "Concordo totalmente",
            "Concordo completamente",
            "Totalmente de acordo"
        ])
        
        result = converter.convert_likert_column(test_data)
        
        # All should map to the same value (5)
        for value in result:
            assert value == 5
    
    def test_partial_matching(self):
        """Test partial matching for scale values"""
        converter = ScaleConverter()
        
        # Test responses that contain valid scale text
        test_data = pd.Series([
            "Eu concordo totalmente com isso",
            "Realmente discordo desta afirmação"
        ])
        
        result = converter.convert_likert_column(test_data)
        
        # Should find partial matches
        assert result.iloc[0] == 5  # Contains "concordo totalmente"
        assert result.iloc[1] == 2  # Contains "discordo"
    
    def test_numeric_input_handling(self):
        """Test handling of numeric inputs"""
        converter = ScaleConverter()
        
        test_data = pd.Series([1, 2, 3, 4, 5])
        result = converter.convert_likert_column(test_data)
        
        # Numeric values should not be converted (treated as invalid)
        for value in result:
            assert pd.isna(value)
    
    def test_mixed_data_types(self):
        """Test handling of mixed data types in series"""
        converter = ScaleConverter()
        
        test_data = pd.Series([
            "Concordo",
            123,
            None,
            "Discordo",
            True
        ])
        
        result = converter.convert_likert_column(test_data)
        
        assert result.iloc[0] == 4      # Valid text
        assert pd.isna(result.iloc[1])  # Number
        assert pd.isna(result.iloc[2])  # None
        assert result.iloc[3] == 2      # Valid text
        assert pd.isna(result.iloc[4])  # Boolean


class TestScaleStats:
    """Test cases for ScaleStats dataclass"""
    
    def test_scale_stats_creation(self):
        """Test ScaleStats creation and calculation"""
        stats = ScaleStats(
            total_values=10,
            converted_values=7,
            invalid_values=2,
            null_values=1,
            conversion_rate=0.0,  # Will be calculated
            invalid_items=["Invalid1", "Invalid2"]
        )
        
        assert stats.conversion_rate == 0.7
        assert stats.total_values == 10
        assert len(stats.invalid_items) == 2
    
    def test_scale_stats_zero_total(self):
        """Test ScaleStats with zero total values"""
        stats = ScaleStats(
            total_values=0,
            converted_values=0,
            invalid_values=0,
            null_values=0,
            conversion_rate=0.0,
            invalid_items=[]
        )
        
        assert stats.conversion_rate == 0.0


class TestScaleConverterIntegration:
    """Integration tests for ScaleConverter with real-world scenarios"""
    
    def test_real_world_likert_data(self):
        """Test with realistic Likert scale data"""
        converter = ScaleConverter()
        
        # Simulate real questionnaire responses
        test_data = pd.Series([
            "Concordo totalmente",
            "Concordo",
            "Não sei",
            "Discordo",
            "Discordo totalmente",
            "",  # Empty response
            "Concordo totalmente",
            "Indiferente",
            None,  # Missing response
            "Concordo"
        ])
        
        result = converter.convert_likert_column(test_data)
        stats = converter.get_scale_statistics(test_data)
        
        # Check that most values were converted successfully
        assert stats.conversion_rate >= 0.7
        assert stats.total_values == 10
        
        # Check specific conversions
        assert result.iloc[0] == 5  # Concordo totalmente
        assert result.iloc[1] == 4  # Concordo
        assert result.iloc[2] == 3  # Não sei
        assert result.iloc[3] == 2  # Discordo
        assert result.iloc[4] == 1  # Discordo totalmente
    
    def test_real_world_satisfaction_data(self):
        """Test with realistic satisfaction scale data"""
        converter = ScaleConverter()
        
        # Simulate real satisfaction responses
        test_data = pd.Series([
            "Muito satisfeito",
            "Satisfeito", 
            "Indiferente",
            "Insatisfeito",
            "Muito insatisfeito",
            "Neutro",
            "Satisfeito",
            ""
        ])
        
        result = converter.convert_satisfaction_column(test_data)
        
        # Create satisfaction converter to get proper stats
        satisfaction_converter = ScaleConverter.create_satisfaction_converter()
        stats = satisfaction_converter.get_scale_statistics(test_data)
        
        # Check conversion success
        assert stats.conversion_rate >= 0.8
        
        # Check specific conversions
        assert result.iloc[0] == 5  # Muito satisfeito
        assert result.iloc[1] == 4  # Satisfeito
        assert result.iloc[2] == 3  # Indiferente
        assert result.iloc[3] == 2  # Insatisfeito
        assert result.iloc[4] == 1  # Muito insatisfeito
    
    def test_performance_with_large_dataset(self):
        """Test performance with large dataset"""
        converter = ScaleConverter()
        
        # Create large dataset
        responses = ["Concordo totalmente", "Concordo", "Não sei", "Discordo", "Discordo totalmente"]
        large_data = pd.Series(responses * 1000)  # 5000 responses
        
        result = converter.convert_likert_column(large_data)
        
        assert len(result) == 5000
        assert result.notna().all()  # All should be converted successfully
    
    def test_data_quality_validation(self):
        """Test data quality validation scenarios"""
        converter = ScaleConverter()
        
        # Test high null percentage
        mostly_null = pd.Series([None] * 8 + ["Concordo", "Discordo"])
        issues = converter.validate_scale_values(mostly_null)
        assert any("null values" in issue for issue in issues)
        
        # Test all identical values
        all_same = pd.Series(["Concordo"] * 10)
        issues = converter.validate_scale_values(all_same)
        assert any("identical" in issue for issue in issues)
        
        # Test low conversion rate
        mostly_invalid = pd.Series(["Invalid"] * 8 + ["Concordo", "Discordo"])
        issues = converter.validate_scale_values(mostly_invalid)
        assert any("conversion rate" in issue for issue in issues)


if __name__ == "__main__":
    pytest.main([__file__])