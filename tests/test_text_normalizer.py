"""
Unit tests for TextNormalizer class

Tests all text normalization functionality including accent removal,
question text normalization, response text normalization, and fuzzy matching.
"""
import pytest
from core.text_normalizer import TextNormalizer


class TestTextNormalizer:
    """Test suite for TextNormalizer class"""
    
    def test_remove_accents_basic(self):
        """Test basic accent removal functionality"""
        # Test common Portuguese accents
        assert TextNormalizer.remove_accents("informação") == "informacao"
        assert TextNormalizer.remove_accents("operação") == "operacao"
        assert TextNormalizer.remove_accents("satisfação") == "satisfacao"
        assert TextNormalizer.remove_accents("público") == "publico"
        assert TextNormalizer.remove_accents("fácil") == "facil"
        assert TextNormalizer.remove_accents("útil") == "util"
        assert TextNormalizer.remove_accents("rápido") == "rapido"
        assert TextNormalizer.remove_accents("prático") == "pratico"
    
    def test_remove_accents_mixed_text(self):
        """Test accent removal in mixed text"""
        text = "O sistema é fácil de usar e muito útil para operação"
        expected = "O sistema e facil de usar e muito util para operacao"
        assert TextNormalizer.remove_accents(text) == expected
    
    def test_remove_accents_edge_cases(self):
        """Test accent removal edge cases"""
        # Empty string
        assert TextNormalizer.remove_accents("") == ""
        
        # None input
        assert TextNormalizer.remove_accents(None) == ""
        
        # Text without accents
        assert TextNormalizer.remove_accents("sistema funciona bem") == "sistema funciona bem"
        
        # Numbers and symbols
        assert TextNormalizer.remove_accents("versão 2.0 - configuração!") == "versao 2.0 - configuracao!"
    
    def test_normalize_question_text_basic(self):
        """Test basic question text normalization"""
        # Test case conversion and accent removal
        text = "O Sistema É Fácil de Usar?"
        expected = "o sistema e facil de usar"
        assert TextNormalizer.normalize_question_text(text) == expected
    
    def test_normalize_question_text_punctuation(self):
        """Test punctuation removal in question normalization"""
        # Test punctuation removal
        text = "O sistema funciona bem, não é?"
        expected = "o sistema funciona bem nao e"
        assert TextNormalizer.normalize_question_text(text) == expected
        
        # Test multiple punctuation marks
        text = "Sistema: fácil, útil & rápido!!!"
        expected = "sistema facil util rapido"
        assert TextNormalizer.normalize_question_text(text) == expected
    
    def test_normalize_question_text_whitespace(self):
        """Test whitespace normalization"""
        # Test multiple spaces
        text = "O    sistema     é    fácil"
        expected = "o sistema e facil"
        assert TextNormalizer.normalize_question_text(text) == expected
        
        # Test leading/trailing whitespace
        text = "   O sistema é fácil   "
        expected = "o sistema e facil"
        assert TextNormalizer.normalize_question_text(text) == expected
    
    def test_normalize_question_text_common_replacements(self):
        """Test common Portuguese word replacements"""
        # Test specific replacements from COMMON_REPLACEMENTS
        text = "A informação técnica é específica"
        expected = "a informacao tecnica e especifica"
        assert TextNormalizer.normalize_question_text(text) == expected
        
        text = "Configuração automática disponível"
        expected = "configuracao automatica disponivel"
        assert TextNormalizer.normalize_question_text(text) == expected
    
    def test_normalize_response_text_basic(self):
        """Test basic response text normalization"""
        # Test Likert scale responses
        assert TextNormalizer.normalize_response_text("Concordo Totalmente") == "concordo totalmente"
        assert TextNormalizer.normalize_response_text("Discordo Totalmente") == "discordo totalmente"
        assert TextNormalizer.normalize_response_text("Não Sei") == "nao sei"
    
    def test_normalize_response_text_preserves_structure(self):
        """Test that response normalization preserves word structure"""
        # Response normalization should be lighter than question normalization
        text = "Concordo, mas não totalmente"
        expected = "concordo mas nao totalmente"
        result = TextNormalizer.normalize_response_text(text)
        assert result == expected
        
        # Should preserve meaningful punctuation structure in responses
        text = "Nem concordo nem discordo"
        expected = "nem concordo nem discordo"
        assert TextNormalizer.normalize_response_text(text) == expected
    
    def test_create_question_mapping_basic(self):
        """Test basic question mapping creation"""
        questions = [
            "O sistema é fácil de usar",
            "A informação é precisa",
            "O sistema funciona bem"
        ]
        
        mapping = TextNormalizer.create_question_mapping(questions)
        
        # Check that normalized keys map to original questions
        assert mapping["o sistema e facil de usar"] == "O sistema é fácil de usar"
        assert mapping["a informacao e precisa"] == "A informação é precisa"
        assert mapping["o sistema funciona bem"] == "O sistema funciona bem"
    
    def test_create_question_mapping_edge_cases(self):
        """Test question mapping with edge cases"""
        # Empty list
        mapping = TextNormalizer.create_question_mapping([])
        assert mapping == {}
        
        # List with empty strings
        questions = ["", "Sistema funciona", "", "Informação útil"]
        mapping = TextNormalizer.create_question_mapping(questions)
        
        # Should only include non-empty questions
        assert len(mapping) == 2
        assert mapping["sistema funciona"] == "Sistema funciona"
        assert mapping["informacao util"] == "Informação útil"
    
    def test_create_question_mapping_duplicates(self):
        """Test question mapping with duplicate normalized forms"""
        questions = [
            "Sistema é fácil",
            "Sistema e facil",  # Same when normalized
            "Sistema funciona"
        ]
        
        mapping = TextNormalizer.create_question_mapping(questions)
        
        # Should handle duplicates (last one wins)
        assert len(mapping) == 2
        assert "sistema e facil" in mapping
        assert "sistema funciona" in mapping
    
    def test_find_best_match_exact(self):
        """Test exact matching in find_best_match"""
        target = "Sistema é fácil de usar"
        candidates = [
            "O sistema funciona bem",
            "Sistema é fácil de usar",
            "Informação é precisa"
        ]
        
        match = TextNormalizer.find_best_match(target, candidates)
        assert match == "Sistema é fácil de usar"
    
    def test_find_best_match_fuzzy(self):
        """Test fuzzy matching with similar but not identical text"""
        target = "Sistema fácil usar"
        candidates = [
            "O sistema é fácil de usar",
            "Sistema difícil de usar",
            "Informação é precisa"
        ]
        
        match = TextNormalizer.find_best_match(target, candidates)
        assert match == "O sistema é fácil de usar"
    
    def test_find_best_match_threshold(self):
        """Test threshold behavior in find_best_match"""
        target = "Sistema"
        candidates = [
            "O sistema é muito complexo e difícil",
            "Informação precisa e útil"
        ]
        
        # With high threshold, should not match
        match = TextNormalizer.find_best_match(target, candidates, threshold=0.8)
        assert match is None
        
        # With low threshold, should match
        match = TextNormalizer.find_best_match(target, candidates, threshold=0.1)
        assert match == "O sistema é muito complexo e difícil"
    
    def test_find_best_match_edge_cases(self):
        """Test edge cases in find_best_match"""
        # Empty target
        match = TextNormalizer.find_best_match("", ["Sistema funciona"])
        assert match is None
        
        # Empty candidates
        match = TextNormalizer.find_best_match("Sistema", [])
        assert match is None
        
        # None values
        match = TextNormalizer.find_best_match(None, ["Sistema"])
        assert match is None
        
        # Candidates with empty strings
        candidates = ["", "Sistema funciona", ""]
        match = TextNormalizer.find_best_match("Sistema", candidates)
        assert match == "Sistema funciona"
    
    def test_create_aliases_basic(self):
        """Test basic alias creation"""
        text = "O sistema funciona bem"
        aliases = TextNormalizer.create_aliases(text)
        
        # Should include original normalized form
        assert "o sistema funciona bem" in aliases
        
        # Should include version without articles
        assert "sistema funciona bem" in aliases
    
    def test_create_aliases_with_prepositions(self):
        """Test alias creation with prepositions"""
        text = "O sistema de informação é útil"
        aliases = TextNormalizer.create_aliases(text)
        
        # Should include versions without articles and prepositions
        expected_aliases = [
            "o sistema de informacao e util",
            "sistema de informacao e util",
            "sistema informacao e util"
        ]
        
        for expected in expected_aliases:
            assert expected in aliases
    
    def test_create_aliases_short_text(self):
        """Test alias creation with short text"""
        # Short text should return minimal aliases
        text = "Sistema"
        aliases = TextNormalizer.create_aliases(text)
        assert aliases == ["sistema"]
        
        text = "Sistema funciona"
        aliases = TextNormalizer.create_aliases(text)
        assert aliases == ["sistema funciona"]
    
    def test_create_aliases_long_text(self):
        """Test alias creation with long text"""
        text = "O sistema de informação funciona muito bem para operação"
        aliases = TextNormalizer.create_aliases(text)
        
        # Should include shortened versions
        assert len(aliases) > 3
        
        # Should include first 3 words
        first_three = "o sistema de"
        assert any(first_three in alias for alias in aliases)
        
        # Should include last 3 words
        last_three = "bem para operacao"
        assert any(last_three in alias for alias in aliases)
    
    def test_create_aliases_edge_cases(self):
        """Test alias creation edge cases"""
        # Empty string
        aliases = TextNormalizer.create_aliases("")
        assert aliases == []
        
        # None input
        aliases = TextNormalizer.create_aliases(None)
        assert aliases == []
    
    def test_create_aliases_no_duplicates(self):
        """Test that aliases don't contain duplicates"""
        text = "Sistema sistema funciona"  # Intentional duplicate
        aliases = TextNormalizer.create_aliases(text)
        
        # Should not have duplicates
        assert len(aliases) == len(set(aliases))
    
    def test_integration_normalize_and_match(self):
        """Test integration between normalization and matching"""
        # Test realistic scenario with Portuguese questionnaire data
        questions = [
            "O sistema é fácil de usar?",
            "A informação apresentada é precisa?",
            "O sistema funciona sem falhas?",
            "Você está satisfeito com o sistema?"
        ]
        
        # Create mapping
        mapping = TextNormalizer.create_question_mapping(questions)
        
        # Test finding matches for slightly different versions
        test_cases = [
            ("Sistema fácil usar", "O sistema é fácil de usar?"),
            ("Informação precisa", "A informação apresentada é precisa?"),
            ("Sistema funciona falhas", "O sistema funciona sem falhas?"),
            ("Satisfeito sistema", "Você está satisfeito com o sistema?")
        ]
        
        for target, expected in test_cases:
            match = TextNormalizer.find_best_match(target, questions, threshold=0.3)
            assert match == expected, f"Failed to match '{target}' to '{expected}', got '{match}'"
    
    def test_portuguese_specific_normalizations(self):
        """Test Portuguese-specific text normalizations"""
        # Test comprehensive Portuguese text with various accents and special cases
        text = "Configuração automática não está disponível para operação técnica"
        normalized = TextNormalizer.normalize_question_text(text)
        expected = "configuracao automatica nao esta disponivel para operacao tecnica"
        assert normalized == expected
        
        # Test response normalization preserves Likert scale structure
        responses = [
            "Concordo Totalmente",
            "Discordo Totalmente", 
            "Não Sei",
            "Nem concordo nem discordo"
        ]
        
        expected_responses = [
            "concordo totalmente",
            "discordo totalmente",
            "nao sei", 
            "nem concordo nem discordo"
        ]
        
        for response, expected in zip(responses, expected_responses):
            normalized = TextNormalizer.normalize_response_text(response)
            assert normalized == expected