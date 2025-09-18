"""
Integration tests for ScaleConverter with existing configuration files

Tests that ScaleConverter works correctly with the actual mapping configurations
used in the questionnaire system.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
from core.scale_converter import ScaleConverter


class TestScaleConverterConfigIntegration:
    """Integration tests with actual configuration files"""
    
    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        config_path = Path("config") / config_file
        if not config_path.exists():
            pytest.skip(f"Configuration file {config_file} not found")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_with_base20_config(self):
        """Test ScaleConverter with base20 configuration"""
        config = self.load_config("items_mapping.json")
        
        # Create converter from config
        converter = ScaleConverter.create_from_config(config)
        
        # Test with sample Likert responses
        test_data = pd.Series([
            "Discordo totalmente",
            "Discordo",
            "Indiferente", 
            "Concordo",
            "Concordo totalmente",
            "Não sei"
        ])
        
        result = converter.convert_likert_column(test_data)
        
        # Verify conversions match expected mapping
        assert result.iloc[0] == 1  # Discordo totalmente
        assert result.iloc[1] == 2  # Discordo
        assert result.iloc[2] == 3  # Indiferente
        assert result.iloc[3] == 4  # Concordo
        assert result.iloc[4] == 5  # Concordo totalmente
        assert pd.isna(result.iloc[5])  # Não sei -> null
    
    def test_with_base8_config(self):
        """Test ScaleConverter with base8 configuration"""
        config = self.load_config("items_mapping_8q.json")
        
        # Create converter from config
        converter = ScaleConverter.create_from_config(config)
        
        # Test with sample Likert responses
        test_data = pd.Series([
            "Discordo totalmente",
            "Discordo",
            "Indiferente",
            "Concordo", 
            "Concordo totalmente"
        ])
        
        result = converter.convert_likert_column(test_data)
        
        # Verify conversions (should be same as base20)
        assert result.iloc[0] == 1  # Discordo totalmente
        assert result.iloc[1] == 2  # Discordo
        assert result.iloc[2] == 3  # Indiferente
        assert result.iloc[3] == 4  # Concordo
        assert result.iloc[4] == 5  # Concordo totalmente
    
    def test_satisfaction_mapping_consistency(self):
        """Test that satisfaction mappings are consistent between configs"""
        base20_config = self.load_config("items_mapping.json")
        base8_config = self.load_config("items_mapping_8q.json")
        
        # Both should have satisfaction mappings
        assert "satisfaction_map" in base20_config
        assert "satisfaction_map" in base8_config
        
        # Create converters for satisfaction scales
        base20_converter = ScaleConverter(base20_config["satisfaction_map"])
        base8_converter = ScaleConverter(base8_config["satisfaction_map"])
        
        # Test with sample satisfaction responses
        test_data = pd.Series([
            "Muito insatisfeito",
            "Insatisfeito",
            "Indiferente",
            "Satisfeito",
            "Muito satisfeito"
        ])
        
        result_base20 = base20_converter.convert_likert_column(test_data)
        result_base8 = base8_converter.convert_likert_column(test_data)
        
        # Results should be identical
        pd.testing.assert_series_equal(result_base20, result_base8)
    
    def test_config_validation(self):
        """Test that configuration files have valid structure"""
        for config_file in ["items_mapping.json", "items_mapping_8q.json"]:
            config = self.load_config(config_file)
            
            # Should have required keys
            assert "likert_map" in config
            assert "satisfaction_map" in config
            
            # Likert map should have 5-point scale
            likert_map = config["likert_map"]
            numeric_values = [v for v in likert_map.values() if v is not None]
            assert min(numeric_values) == 1
            assert max(numeric_values) == 5
            
            # Satisfaction map should have 5-point scale
            satisfaction_map = config["satisfaction_map"]
            sat_values = [v for v in satisfaction_map.values() if v is not None]
            assert min(sat_values) == 1
            assert max(sat_values) == 5
    
    def test_real_data_simulation(self):
        """Test with simulated real questionnaire data"""
        config = self.load_config("items_mapping.json")
        converter = ScaleConverter.create_from_config(config)
        
        # Simulate a realistic dataset with various response patterns
        realistic_data = pd.Series([
            "Concordo totalmente",
            "Concordo",
            "Concordo totalmente", 
            "Indiferente",
            "Concordo",
            "Discordo",
            "Concordo totalmente",
            "Concordo",
            "Não sei",
            "Concordo",
            "",  # Empty response
            "Concordo totalmente",
            "Indiferente",
            None,  # Missing response
            "Concordo",
            "Discordo totalmente",
            "Concordo",
            "Concordo totalmente",
            "Concordo",
            "Indiferente"
        ])
        
        result = converter.convert_likert_column(realistic_data)
        stats = converter.get_scale_statistics(realistic_data)
        
        # Should have high conversion rate for realistic data
        assert stats.conversion_rate >= 0.8
        
        # Should have reasonable distribution
        value_counts = result.value_counts()
        assert len(value_counts) >= 3  # Should have variety in responses
        
        # Most common response should be positive (4 or 5)
        most_common_value = value_counts.index[0]
        assert most_common_value in [4, 5]


if __name__ == "__main__":
    pytest.main([__file__])