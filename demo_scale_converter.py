"""
Demonstration script for ScaleConverter functionality

This script shows how to use the ScaleConverter class for converting
Likert scales and satisfaction scales to numeric values.
"""
import pandas as pd
import json
from core.scale_converter import ScaleConverter


def demo_basic_usage():
    """Demonstrate basic ScaleConverter usage"""
    print("=== Basic ScaleConverter Usage ===")
    
    # Create a default Likert scale converter
    converter = ScaleConverter()
    
    # Sample Likert responses
    responses = pd.Series([
        "Concordo totalmente",
        "Concordo", 
        "Não sei",
        "Discordo",
        "Discordo totalmente",
        "Invalid response",
        None
    ])
    
    print("Original responses:")
    for i, response in enumerate(responses):
        print(f"  {i+1}. {response}")
    
    # Convert to numeric
    numeric_result = converter.convert_likert_column(responses)
    
    print("\nConverted to numeric:")
    for i, (original, numeric) in enumerate(zip(responses, numeric_result)):
        print(f"  {i+1}. '{original}' -> {numeric}")
    
    # Get statistics
    stats = converter.get_scale_statistics(responses)
    print(f"\nConversion Statistics:")
    print(f"  Total values: {stats.total_values}")
    print(f"  Converted: {stats.converted_values}")
    print(f"  Invalid: {stats.invalid_values}")
    print(f"  Null: {stats.null_values}")
    print(f"  Conversion rate: {stats.conversion_rate:.1%}")
    if stats.invalid_items:
        print(f"  Invalid items: {stats.invalid_items}")


def demo_satisfaction_scale():
    """Demonstrate satisfaction scale conversion"""
    print("\n=== Satisfaction Scale Conversion ===")
    
    converter = ScaleConverter()
    
    # Sample satisfaction responses
    satisfaction_responses = pd.Series([
        "Muito satisfeito",
        "Satisfeito",
        "Indiferente", 
        "Insatisfeito",
        "Muito insatisfeito",
        "Neutro"
    ])
    
    print("Satisfaction responses:")
    for i, response in enumerate(satisfaction_responses):
        print(f"  {i+1}. {response}")
    
    # Convert using satisfaction scale
    numeric_result = converter.convert_satisfaction_column(satisfaction_responses)
    
    print("\nConverted to numeric:")
    for i, (original, numeric) in enumerate(zip(satisfaction_responses, numeric_result)):
        print(f"  {i+1}. '{original}' -> {numeric}")


def demo_config_integration():
    """Demonstrate integration with configuration files"""
    print("\n=== Configuration File Integration ===")
    
    try:
        # Load configuration from file
        with open("config/items_mapping.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Create converter from config
        converter = ScaleConverter.create_from_config(config)
        
        print("Loaded configuration from items_mapping.json")
        print("Valid scale values:", converter.get_valid_scale_values()[:5], "...")
        
        # Test with config-based conversion
        test_responses = pd.Series([
            "Discordo totalmente",
            "Indiferente",
            "Concordo totalmente"
        ])
        
        result = converter.convert_likert_column(test_responses)
        
        print("\nConfig-based conversion:")
        for original, numeric in zip(test_responses, result):
            print(f"  '{original}' -> {numeric}")
            
    except FileNotFoundError:
        print("Configuration file not found - using default mapping")


def demo_validation():
    """Demonstrate data validation features"""
    print("\n=== Data Validation ===")
    
    converter = ScaleConverter()
    
    # Create problematic data
    problematic_data = pd.Series([
        "Concordo",
        "Invalid response 1",
        "Invalid response 2", 
        "Random text",
        None,
        "",
        "Concordo"
    ])
    
    print("Problematic data:")
    for i, response in enumerate(problematic_data):
        print(f"  {i+1}. {response}")
    
    # Validate the data
    issues = converter.validate_scale_values(problematic_data)
    
    print(f"\nValidation issues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")


def demo_custom_mapping():
    """Demonstrate custom scale mapping"""
    print("\n=== Custom Scale Mapping ===")
    
    # Create custom binary scale
    custom_mapping = {
        "Sim": 1,
        "Não": 0,
        "Talvez": None  # Treated as invalid/missing
    }
    
    converter = ScaleConverter(custom_mapping)
    
    # Test custom mapping
    custom_responses = pd.Series([
        "Sim",
        "Não", 
        "Talvez",
        "SIM",  # Case insensitive
        "não"   # Case insensitive
    ])
    
    print("Custom responses:")
    for i, response in enumerate(custom_responses):
        print(f"  {i+1}. {response}")
    
    result = converter.convert_likert_column(custom_responses)
    
    print("\nCustom conversion:")
    for original, numeric in zip(custom_responses, result):
        print(f"  '{original}' -> {numeric}")


def demo_performance():
    """Demonstrate performance with large dataset"""
    print("\n=== Performance Test ===")
    
    converter = ScaleConverter()
    
    # Create large dataset
    import time
    responses = ["Concordo totalmente", "Concordo", "Não sei", "Discordo", "Discordo totalmente"]
    large_dataset = pd.Series(responses * 2000)  # 10,000 responses
    
    print(f"Processing {len(large_dataset):,} responses...")
    
    start_time = time.time()
    result = converter.convert_likert_column(large_dataset)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    print(f"Processing completed in {processing_time:.3f} seconds")
    print(f"Rate: {len(large_dataset)/processing_time:,.0f} responses/second")
    print(f"All values converted successfully: {result.notna().all()}")


if __name__ == "__main__":
    print("ScaleConverter Demonstration")
    print("=" * 50)
    
    demo_basic_usage()
    demo_satisfaction_scale()
    demo_config_integration()
    demo_validation()
    demo_custom_mapping()
    demo_performance()
    
    print("\n" + "=" * 50)
    print("Demonstration completed!")