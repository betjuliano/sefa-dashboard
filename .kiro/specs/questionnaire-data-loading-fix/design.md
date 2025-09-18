# Design Document

## Overview

Este documento descreve o design de uma solução robusta para resolver os problemas de carregamento e processamento das questões nos sistemas base20 e base8. A solução implementa um sistema de normalização de dados, validação de mapeamentos e processamento consistente de escalas Likert que funciona de forma transparente para ambos os conjuntos de questões.

## Architecture

### Current System Analysis

O sistema atual possui:
- Arquivos de configuração JSON separados (`items_mapping.json` e `items_mapping_8q.json`)
- Função `get_mapping_for_question_set()` que seleciona o mapeamento apropriado
- Processamento de dados no `app.py` com funções `normalize_likert()` e `normalize_satisfaction()`
- Sistema de filtros baseado em conjuntos de questões

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Processing Layer                     │
├─────────────────────────────────────────────────────────────┤
│  QuestionnaireProcessor                                     │
│  ├── DataValidator                                          │
│  ├── TextNormalizer                                         │
│  ├── MappingManager                                         │
│  └── ScaleConverter                                         │
├─────────────────────────────────────────────────────────────┤
│                   Configuration Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ConfigurationValidator                                     │
│  ├── MappingValidator                                       │
│  ├── SchemaValidator                                        │
│  └── ConsistencyChecker                                     │
├─────────────────────────────────────────────────────────────┤
│                     Storage Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Enhanced DataManager                                       │
│  └── ProcessedDataCache                                     │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. QuestionnaireProcessor

**Responsabilidade:** Processamento principal de dados de questionários

```python
class QuestionnaireProcessor:
    def __init__(self, question_set: str)
    def load_and_process_data(self, df: pd.DataFrame) -> ProcessedData
    def validate_data_structure(self, df: pd.DataFrame) -> ValidationResult
    def normalize_question_texts(self, df: pd.DataFrame) -> pd.DataFrame
    def convert_likert_scales(self, df: pd.DataFrame) -> pd.DataFrame
    def map_questions_to_codes(self, df: pd.DataFrame) -> pd.DataFrame
    def calculate_dimension_scores(self, df: pd.DataFrame) -> pd.DataFrame
```

### 2. TextNormalizer

**Responsabilidade:** Normalização de textos de questões e respostas

```python
class TextNormalizer:
    @staticmethod
    def remove_accents(text: str) -> str
    @staticmethod
    def normalize_question_text(text: str) -> str
    @staticmethod
    def normalize_response_text(text: str) -> str
    @staticmethod
    def create_question_mapping(questions: List[str]) -> Dict[str, str]
```

### 3. MappingManager

**Responsabilidade:** Gerenciamento de mapeamentos entre questões e códigos

```python
class MappingManager:
    def __init__(self, question_set: str)
    def load_mapping_config(self) -> Dict[str, Any]
    def get_question_to_code_mapping(self) -> Dict[str, str]
    def get_dimension_mapping(self) -> Dict[str, List[str]]
    def find_matching_questions(self, available_questions: List[str]) -> Dict[str, str]
    def get_missing_questions(self, available_questions: List[str]) -> List[str]
```

### 4. ScaleConverter

**Responsabilidade:** Conversão de escalas Likert para valores numéricos

```python
class ScaleConverter:
    def __init__(self, scale_mapping: Dict[str, int])
    def convert_likert_column(self, series: pd.Series) -> pd.Series
    def convert_satisfaction_column(self, series: pd.Series) -> pd.Series
    def get_scale_statistics(self, series: pd.Series) -> ScaleStats
    def validate_scale_values(self, series: pd.Series) -> List[str]
```

### 5. ConfigurationValidator

**Responsabilidade:** Validação de arquivos de configuração

```python
class ConfigurationValidator:
    def validate_mapping_files(self) -> ValidationReport
    def check_question_consistency(self) -> List[ValidationIssue]
    def validate_scale_mappings(self) -> List[ValidationIssue]
    def suggest_corrections(self, issues: List[ValidationIssue]) -> List[Correction]
```

## Data Models

### ProcessedData

```python
@dataclass
class ProcessedData:
    dataframe: pd.DataFrame
    question_mapping: Dict[str, str]
    dimension_scores: Dict[str, float]
    validation_report: ValidationReport
    processing_metadata: ProcessingMetadata
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    warnings: List[str]
    missing_questions: List[str]
    extra_questions: List[str]
```

### ValidationIssue

```python
@dataclass
class ValidationIssue:
    type: str  # 'missing_question', 'invalid_scale', 'duplicate_mapping'
    severity: str  # 'error', 'warning', 'info'
    message: str
    affected_items: List[str]
    suggested_fix: Optional[str]
```

### ProcessingMetadata

```python
@dataclass
class ProcessingMetadata:
    question_set: str
    total_questions: int
    processed_questions: int
    skipped_questions: List[str]
    conversion_stats: Dict[str, Any]
    processing_time: float
```

## Error Handling

### Error Hierarchy

```python
class QuestionnaireProcessingError(Exception):
    """Base exception for questionnaire processing"""
    pass

class MappingError(QuestionnaireProcessingError):
    """Errors related to question mapping"""
    pass

class ScaleConversionError(QuestionnaireProcessingError):
    """Errors related to scale conversion"""
    pass

class ValidationError(QuestionnaireProcessingError):
    """Errors related to data validation"""
    pass
```

### Error Handling Strategy

1. **Graceful Degradation:** Continue processing with available data when non-critical errors occur
2. **Detailed Logging:** Log all issues with context for debugging
3. **User Feedback:** Provide clear, actionable error messages to users
4. **Recovery Mechanisms:** Attempt automatic fixes for common issues

## Testing Strategy

### Unit Tests

1. **TextNormalizer Tests**
   - Test accent removal for Portuguese text
   - Test question text standardization
   - Test response text normalization

2. **ScaleConverter Tests**
   - Test Likert scale conversion for all possible values
   - Test handling of invalid/missing values
   - Test satisfaction scale conversion

3. **MappingManager Tests**
   - Test loading of different mapping configurations
   - Test question matching with fuzzy logic
   - Test handling of missing questions

4. **ConfigurationValidator Tests**
   - Test validation of mapping files
   - Test detection of inconsistencies
   - Test correction suggestions

### Integration Tests

1. **End-to-End Processing Tests**
   - Test complete processing pipeline for base20 data
   - Test complete processing pipeline for base8 data
   - Test switching between question sets

2. **Data Consistency Tests**
   - Test that processed data maintains referential integrity
   - Test that dimension calculations are correct
   - Test that filtering works correctly

### Performance Tests

1. **Load Testing**
   - Test processing of large datasets (10k+ rows)
   - Test memory usage during processing
   - Test processing time benchmarks

2. **Stress Testing**
   - Test handling of malformed data
   - Test processing with missing columns
   - Test concurrent processing requests

### Validation Tests

1. **Configuration Validation Tests**
   - Test validation of correct mapping files
   - Test detection of mapping errors
   - Test handling of corrupted configuration files

2. **Data Validation Tests**
   - Test validation of well-formed questionnaire data
   - Test detection of data quality issues
   - Test handling of edge cases in data

## Implementation Phases

### Phase 1: Core Infrastructure
- Implement TextNormalizer class
- Implement ScaleConverter class
- Create basic error handling framework
- Add comprehensive logging

### Phase 2: Mapping Management
- Implement MappingManager class
- Create fuzzy matching for questions
- Add configuration validation
- Implement automatic correction suggestions

### Phase 3: Processing Pipeline
- Implement QuestionnaireProcessor class
- Integrate all components
- Add caching mechanisms
- Implement performance optimizations

### Phase 4: Validation and Testing
- Implement ConfigurationValidator
- Add comprehensive test suite
- Performance testing and optimization
- Documentation and user guides

## Configuration Updates

### Enhanced Mapping Structure

```json
{
  "metadata": {
    "version": "2.0",
    "question_set": "base20",
    "last_updated": "2024-01-01T00:00:00Z"
  },
  "dimensions": {
    "Qualidade do Sistema": {
      "code": "QS",
      "questions": [
        {
          "text": "O sistema funciona sem falhas.",
          "code": "QS1",
          "normalized_text": "o sistema funciona sem falhas",
          "aliases": ["sistema funciona falhas", "funciona sem falhas"]
        }
      ]
    }
  },
  "scales": {
    "likert": {
      "mapping": {
        "Discordo totalmente": 1,
        "Discordo": 2,
        "Não sei": 3,
        "Concordo": 4,
        "Concordo totalmente": 5
      },
      "aliases": {
        "Discordo Totalmente": "Discordo totalmente",
        "Neutro": "Não sei",
        "Nem concordo nem discordo": "Não sei"
      }
    }
  }
}
```

## Performance Considerations

1. **Caching:** Cache processed mappings and normalized texts
2. **Lazy Loading:** Load configurations only when needed
3. **Batch Processing:** Process data in chunks for large datasets
4. **Memory Management:** Use generators for large data processing
5. **Parallel Processing:** Use multiprocessing for independent operations

## Security Considerations

1. **Input Validation:** Validate all input data before processing
2. **Path Traversal Protection:** Ensure file paths are within allowed directories
3. **Data Sanitization:** Sanitize text inputs to prevent injection attacks
4. **Access Control:** Maintain user isolation in data processing
5. **Audit Logging:** Log all data processing operations for audit trails