"""
Scale conversion utilities for questionnaire processing

This module provides utilities for converting Likert scales and satisfaction scales
to numeric values, with validation and error handling for invalid inputs.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from .text_normalizer import TextNormalizer


@dataclass
class ScaleStats:
    """Statistics for scale conversion results"""
    total_values: int
    converted_values: int
    invalid_values: int
    null_values: int
    conversion_rate: float
    invalid_items: List[str]
    
    def __post_init__(self):
        """Calculate conversion rate"""
        if self.total_values > 0:
            self.conversion_rate = self.converted_values / self.total_values
        else:
            self.conversion_rate = 0.0


class ScaleConverter:
    """
    Utility class for converting Likert scales and satisfaction scales to numeric values.
    
    Provides methods for different scale types with validation and error handling.
    Supports both 5-point Likert scales and satisfaction scales as specified in requirements.
    """
    
    # Default 5-point Likert scale mapping (Requirements 2.1-2.5)
    DEFAULT_LIKERT_MAPPING = {
        "discordo totalmente": 1,
        "discordo": 2,
        "nao sei": 3,
        "neutro": 3,
        "indiferente": 3,
        "nem concordo nem discordo": 3,
        "concordo": 4,
        "concordo totalmente": 5
    }
    
    # Default satisfaction scale mapping
    DEFAULT_SATISFACTION_MAPPING = {
        "muito insatisfeito": 1,
        "insatisfeito": 2,
        "indiferente": 3,
        "neutro": 3,
        "satisfeito": 4,
        "muito satisfeito": 5
    }
    
    # Common aliases for scale values
    SCALE_ALIASES = {
        # Likert scale aliases
        "discordo totalmente": ["discordo totalmente", "discordo completamente", "totalmente em desacordo"],
        "discordo": ["discordo", "em desacordo", "nao concordo"],
        "nao sei": ["nao sei", "nao tenho opiniao", "sem opiniao", "indeciso"],
        "neutro": ["neutro", "indiferente", "nem concordo nem discordo", "imparcial"],
        "concordo": ["concordo", "de acordo", "em acordo"],
        "concordo totalmente": ["concordo totalmente", "concordo completamente", "totalmente de acordo"],
        
        # Satisfaction scale aliases
        "muito insatisfeito": ["muito insatisfeito", "totalmente insatisfeito", "extremamente insatisfeito"],
        "insatisfeito": ["insatisfeito", "pouco satisfeito", "nao satisfeito"],
        "satisfeito": ["satisfeito", "bem satisfeito"],
        "muito satisfeito": ["muito satisfeito", "totalmente satisfeito", "extremamente satisfeito"]
    }
    
    def __init__(self, scale_mapping: Optional[Dict[str, Union[int, None]]] = None):
        """
        Initialize ScaleConverter with custom or default scale mapping.
        
        Args:
            scale_mapping: Custom mapping from scale text to numeric values.
                          If None, uses default Likert mapping.
        """
        if scale_mapping is None:
            self.scale_mapping = self.DEFAULT_LIKERT_MAPPING.copy()
        else:
            # Normalize the provided mapping keys
            self.scale_mapping = {}
            for key, value in scale_mapping.items():
                normalized_key = TextNormalizer.normalize_response_text(key)
                self.scale_mapping[normalized_key] = value
        
        # Create reverse mapping for validation
        self._create_alias_mapping()
    
    def _create_alias_mapping(self) -> None:
        """Create expanded mapping including aliases for better matching"""
        self.expanded_mapping = self.scale_mapping.copy()
        
        # Add aliases for better matching, but only if the canonical form exists in scale_mapping
        for canonical, aliases in self.SCALE_ALIASES.items():
            # Check if the canonical form exists in our current scale mapping
            canonical_normalized = TextNormalizer.normalize_response_text(canonical)
            if canonical_normalized in self.scale_mapping:
                canonical_value = self.scale_mapping[canonical_normalized]
                for alias in aliases:
                    normalized_alias = TextNormalizer.normalize_response_text(alias)
                    if normalized_alias not in self.expanded_mapping:
                        self.expanded_mapping[normalized_alias] = canonical_value
    
    def convert_likert_column(self, series: pd.Series) -> pd.Series:
        """
        Convert a pandas Series containing Likert scale responses to numeric values.
        
        Args:
            series: Pandas Series with Likert scale text responses
            
        Returns:
            Pandas Series with numeric values (1-5) and NaN for invalid responses
            
        Example:
            >>> converter = ScaleConverter()
            >>> series = pd.Series(["Concordo totalmente", "Discordo", "Não sei"])
            >>> result = converter.convert_likert_column(series)
            >>> result.tolist()
            [5, 2, 3]
        """
        if series.empty:
            return pd.Series(dtype=float)
        
        # Convert to string and handle NaN values
        string_series = series.astype(str).str.strip()
        
        # Replace pandas 'nan' string with actual NaN
        string_series = string_series.replace("nan", np.nan)
        
        # Apply conversion function to each value
        converted = string_series.apply(self._convert_single_value)
        
        return converted
    
    def convert_satisfaction_column(self, series: pd.Series) -> pd.Series:
        """
        Convert a pandas Series containing satisfaction scale responses to numeric values.
        
        Args:
            series: Pandas Series with satisfaction scale text responses
            
        Returns:
            Pandas Series with numeric values (1-5) and NaN for invalid responses
            
        Example:
            >>> converter = ScaleConverter(ScaleConverter.DEFAULT_SATISFACTION_MAPPING)
            >>> series = pd.Series(["Muito satisfeito", "Insatisfeito", "Neutro"])
            >>> result = converter.convert_satisfaction_column(series)
            >>> result.tolist()
            [5, 2, 3]
        """
        # Create a new converter specifically for satisfaction scales
        satisfaction_converter = ScaleConverter(self.DEFAULT_SATISFACTION_MAPPING)
        return satisfaction_converter.convert_likert_column(series)
    
    def _convert_single_value(self, value: Any) -> Union[int, float]:
        """
        Convert a single scale value to numeric.
        
        Args:
            value: Single scale response value
            
        Returns:
            Numeric value or NaN if invalid/missing
        """
        # Handle NaN, None, and empty values (Requirement 2.6)
        if pd.isna(value) or value is None or value == "":
            return np.nan
        
        # Convert to string and normalize
        str_value = str(value).strip()
        if str_value.lower() in ["nan", "none", ""]:
            return np.nan
        
        # Normalize the text for matching
        normalized_value = TextNormalizer.normalize_response_text(str_value)
        
        # Try exact match first
        if normalized_value in self.expanded_mapping:
            result = self.expanded_mapping[normalized_value]
            return result if result is not None else np.nan
        
        # Try partial matching for common variations
        # Look for scale values contained within the response
        best_match = None
        best_match_length = 0
        
        for key, numeric_value in self.expanded_mapping.items():
            # Check if the scale key is contained in the normalized response
            if len(key) > 3 and key in normalized_value:
                # Prefer longer matches (more specific)
                if len(key) > best_match_length:
                    best_match = numeric_value
                    best_match_length = len(key)
        
        if best_match is not None:
            return best_match if best_match is not None else np.nan
        
        # If no match found, return NaN (Requirement 2.6)
        return np.nan
    
    def get_scale_statistics(self, series: pd.Series) -> ScaleStats:
        """
        Get statistics about scale conversion results.
        
        Args:
            series: Original pandas Series before conversion
            
        Returns:
            ScaleStats object with conversion statistics
            
        Example:
            >>> converter = ScaleConverter()
            >>> series = pd.Series(["Concordo", "Invalid", None, "Discordo"])
            >>> stats = converter.get_scale_statistics(series)
            >>> stats.conversion_rate
            0.5
        """
        if series.empty:
            return ScaleStats(0, 0, 0, 0, 0.0, [])
        
        total_values = len(series)
        
        # Convert series to get results
        converted_series = self.convert_likert_column(series)
        
        # Count different types of values
        null_values = series.isna().sum()
        converted_values = converted_series.notna().sum()
        invalid_values = total_values - converted_values - null_values
        
        # Find invalid items
        invalid_mask = series.notna() & converted_series.isna()
        invalid_items = series[invalid_mask].unique().tolist()
        
        return ScaleStats(
            total_values=total_values,
            converted_values=converted_values,
            invalid_values=invalid_values,
            null_values=null_values,
            conversion_rate=0.0,  # Will be calculated in __post_init__
            invalid_items=[str(item) for item in invalid_items]
        )
    
    def validate_scale_values(self, series: pd.Series) -> List[str]:
        """
        Validate scale values and return list of validation issues.
        
        Args:
            series: Pandas Series with scale responses
            
        Returns:
            List of validation issue descriptions
            
        Example:
            >>> converter = ScaleConverter()
            >>> series = pd.Series(["Concordo", "Invalid Value", ""])
            >>> issues = converter.validate_scale_values(series)
            >>> len(issues)
            1
        """
        issues = []
        
        if series.empty:
            issues.append("Series is empty")
            return issues
        
        # Get statistics
        stats = self.get_scale_statistics(series)
        
        # Check for high percentage of invalid values
        if stats.conversion_rate < 0.5:
            issues.append(f"Low conversion rate: {stats.conversion_rate:.1%} of values could be converted")
        
        # Check for invalid values
        if stats.invalid_values > 0:
            issues.append(f"Found {stats.invalid_values} invalid scale values: {stats.invalid_items[:5]}")
        
        # Check for high percentage of null values
        null_percentage = stats.null_values / stats.total_values
        if null_percentage > 0.3:
            issues.append(f"High percentage of null values: {null_percentage:.1%}")
        
        # Check if all values are the same (potential data quality issue)
        non_null_values = series.dropna()
        if len(non_null_values) > 0 and len(non_null_values.unique()) == 1:
            issues.append(f"All non-null values are identical: '{non_null_values.iloc[0]}'")
        
        return issues
    
    @classmethod
    def create_likert_converter(cls) -> 'ScaleConverter':
        """
        Create a ScaleConverter configured for 5-point Likert scales.
        
        Returns:
            ScaleConverter instance with Likert scale mapping
        """
        return cls(cls.DEFAULT_LIKERT_MAPPING)
    
    @classmethod
    def create_satisfaction_converter(cls) -> 'ScaleConverter':
        """
        Create a ScaleConverter configured for satisfaction scales.
        
        Returns:
            ScaleConverter instance with satisfaction scale mapping
        """
        return cls(cls.DEFAULT_SATISFACTION_MAPPING)
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> 'ScaleConverter':
        """
        Create a ScaleConverter from configuration dictionary.
        
        Args:
            config: Configuration dictionary with scale mappings
            
        Returns:
            ScaleConverter instance configured from config
            
        Example:
            >>> config = {"likert_map": {"Sim": 1, "Não": 0}}
            >>> converter = ScaleConverter.create_from_config(config)
        """
        if "likert_map" in config:
            return cls(config["likert_map"])
        elif "satisfaction_map" in config:
            return cls(config["satisfaction_map"])
        else:
            return cls()
    
    def get_valid_scale_values(self) -> List[str]:
        """
        Get list of valid scale values that can be converted.
        
        Returns:
            List of valid scale value strings
        """
        return list(self.expanded_mapping.keys())
    
    def add_scale_mapping(self, text: str, value: Union[int, None]) -> None:
        """
        Add or update a scale mapping.
        
        Args:
            text: Scale response text
            value: Numeric value to map to (or None for invalid responses)
        """
        normalized_text = TextNormalizer.normalize_response_text(text)
        self.scale_mapping[normalized_text] = value
        self._create_alias_mapping()
    
    def remove_scale_mapping(self, text: str) -> bool:
        """
        Remove a scale mapping.
        
        Args:
            text: Scale response text to remove
            
        Returns:
            True if mapping was removed, False if not found
        """
        normalized_text = TextNormalizer.normalize_response_text(text)
        removed = False
        
        # Remove from main mapping
        if normalized_text in self.scale_mapping:
            del self.scale_mapping[normalized_text]
            removed = True
        
        # Also remove any aliases that point to this text
        aliases_to_remove = []
        for alias_key, alias_list in self.SCALE_ALIASES.items():
            if normalized_text == alias_key:
                aliases_to_remove.append(alias_key)
        
        # Rebuild the expanded mapping to remove aliases
        self._create_alias_mapping()
        
        return removed