"""
Text normalization utilities for questionnaire processing

This module provides utilities for normalizing Portuguese text, removing accents,
and standardizing question and response texts for consistent processing.
"""
import re
import unicodedata
from typing import Dict, List, Optional


class TextNormalizer:
    """
    Utility class for normalizing Portuguese text in questionnaire data.
    
    Provides methods for accent removal, text standardization, and creating
    normalized mappings for question matching.
    """
    
    # Common Portuguese text patterns and their standardized forms
    COMMON_REPLACEMENTS = {
        # Question text standardizations
        'questão': 'questao',
        'informação': 'informacao',
        'operação': 'operacao',
        'satisfação': 'satisfacao',
        'público': 'publico',
        'fácil': 'facil',
        'útil': 'util',
        'rápido': 'rapido',
        'prático': 'pratico',
        'específico': 'especifico',
        'técnico': 'tecnico',
        'básico': 'basico',
        'automático': 'automatico',
        'eletrônico': 'eletronico',
        'disponível': 'disponivel',
        'confiável': 'confiavel',
        'acessível': 'acessivel',
        
        # Response text standardizations
        'não': 'nao',
        'são': 'sao',
        'então': 'entao',
        'função': 'funcao',
        'versão': 'versao',
        'decisão': 'decisao',
        'precisão': 'precisao',
        'organização': 'organizacao',
        'comunicação': 'comunicacao',
        'integração': 'integracao',
        'configuração': 'configuracao',
        'implementação': 'implementacao',
    }
    
    @staticmethod
    def remove_accents(text: str) -> str:
        """
        Remove accents and diacritical marks from Portuguese text.
        
        Args:
            text: Input text with potential accents
            
        Returns:
            Text with accents removed
            
        Example:
            >>> TextNormalizer.remove_accents("Informação técnica")
            "Informacao tecnica"
        """
        if not text:
            return ""
        
        # Normalize to NFD (decomposed form) and remove combining characters
        normalized = unicodedata.normalize('NFD', text)
        without_accents = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        
        return without_accents
    
    @staticmethod
    def normalize_question_text(text: str) -> str:
        """
        Normalize question text for consistent matching.
        
        Performs the following normalizations:
        - Removes accents
        - Converts to lowercase
        - Removes extra whitespace
        - Removes punctuation
        - Applies common Portuguese word replacements
        
        Args:
            text: Original question text
            
        Returns:
            Normalized question text
            
        Example:
            >>> TextNormalizer.normalize_question_text("O sistema é fácil de usar?")
            "o sistema e facil de usar"
        """
        if not text:
            return ""
        
        # Remove accents
        normalized = TextNormalizer.remove_accents(text)
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Apply common replacements
        for original, replacement in TextNormalizer.COMMON_REPLACEMENTS.items():
            normalized = normalized.replace(original, replacement)
        
        # Remove punctuation and special characters, keep only letters, numbers, and spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace (replace multiple spaces with single space)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def normalize_response_text(text: str) -> str:
        """
        Normalize response text for scale conversion.
        
        Performs lighter normalization suitable for Likert scale responses:
        - Removes accents
        - Converts to lowercase
        - Trims whitespace
        - Applies common Portuguese word replacements
        - Removes punctuation (lighter than question normalization)
        
        Args:
            text: Original response text
            
        Returns:
            Normalized response text
            
        Example:
            >>> TextNormalizer.normalize_response_text("Concordo Totalmente")
            "concordo totalmente"
        """
        if not text:
            return ""
        
        # Remove accents
        normalized = TextNormalizer.remove_accents(text)
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Apply common replacements
        for original, replacement in TextNormalizer.COMMON_REPLACEMENTS.items():
            normalized = normalized.replace(original, replacement)
        
        # Remove punctuation but keep structure (lighter than question normalization)
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace but keep structure for responses
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def create_question_mapping(questions: List[str]) -> Dict[str, str]:
        """
        Create a mapping from normalized question text to original text.
        
        This is useful for fuzzy matching where we need to find questions
        with slight variations in text.
        
        Args:
            questions: List of original question texts
            
        Returns:
            Dictionary mapping normalized text to original text
            
        Example:
            >>> questions = ["O sistema é fácil?", "Sistema fácil de usar"]
            >>> mapping = TextNormalizer.create_question_mapping(questions)
            >>> mapping["o sistema e facil"]
            "O sistema é fácil?"
        """
        mapping = {}
        
        for question in questions:
            if question:  # Skip empty questions
                normalized = TextNormalizer.normalize_question_text(question)
                if normalized:  # Only add if normalization produced non-empty result
                    mapping[normalized] = question
        
        return mapping
    
    @staticmethod
    def find_best_match(target: str, candidates: List[str], threshold: float = 0.3) -> Optional[str]:
        """
        Find the best matching question from a list of candidates.
        
        Uses normalized text comparison and simple similarity scoring
        based on common words.
        
        Args:
            target: Target question text to match
            candidates: List of candidate question texts
            threshold: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            Best matching candidate or None if no match above threshold
            
        Example:
            >>> target = "Sistema é fácil usar"
            >>> candidates = ["O sistema é fácil de usar", "Sistema difícil"]
            >>> TextNormalizer.find_best_match(target, candidates)
            "O sistema é fácil de usar"
        """
        if not target or not candidates:
            return None
        
        normalized_target = TextNormalizer.normalize_question_text(target)
        target_words = set(normalized_target.split())
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            if not candidate:
                continue
                
            normalized_candidate = TextNormalizer.normalize_question_text(candidate)
            candidate_words = set(normalized_candidate.split())
            
            # Calculate Jaccard similarity (intersection over union)
            if not target_words and not candidate_words:
                similarity = 1.0
            elif not target_words or not candidate_words:
                similarity = 0.0
            else:
                intersection = len(target_words.intersection(candidate_words))
                union = len(target_words.union(candidate_words))
                similarity = intersection / union if union > 0 else 0.0
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = candidate
        
        return best_match
    
    @staticmethod
    def create_aliases(text: str) -> List[str]:
        """
        Create common aliases/variations for a given text.
        
        Generates variations that might appear in different datasets:
        - With/without articles
        - With/without prepositions
        - Common abbreviations
        
        Args:
            text: Original text
            
        Returns:
            List of text aliases/variations
            
        Example:
            >>> TextNormalizer.create_aliases("O sistema funciona bem")
            ["sistema funciona bem", "o sistema funciona", "funciona bem"]
        """
        if not text:
            return []
        
        normalized = TextNormalizer.normalize_question_text(text)
        words = normalized.split()
        
        if len(words) <= 2:
            return [normalized]
        
        aliases = [normalized]
        
        # Remove articles (o, a, os, as, um, uma)
        articles = {'o', 'a', 'os', 'as', 'um', 'uma'}
        words_no_articles = [w for w in words if w not in articles]
        if len(words_no_articles) != len(words):
            aliases.append(' '.join(words_no_articles))
        
        # Remove common prepositions (de, do, da, dos, das, em, no, na, nos, nas)
        prepositions = {'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas', 'para', 'por'}
        words_no_prep = [w for w in words_no_articles if w not in prepositions]
        if len(words_no_prep) != len(words_no_articles):
            aliases.append(' '.join(words_no_prep))
        
        # Create shorter versions (first and last few words)
        if len(words) > 4:
            # First 3 words
            aliases.append(' '.join(words[:3]))
            # Last 3 words
            aliases.append(' '.join(words[-3:]))
            # First and last 2 words
            if len(words) > 6:
                aliases.append(' '.join(words[:2] + words[-2:]))
        
        # Remove duplicates while preserving order
        unique_aliases = []
        seen = set()
        for alias in aliases:
            if alias and alias not in seen:
                unique_aliases.append(alias)
                seen.add(alias)
        
        return unique_aliases