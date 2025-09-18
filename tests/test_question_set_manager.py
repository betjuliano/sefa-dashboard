"""
Unit tests for QuestionSetManager class

Tests the filtering and processing of different question sets (26, 20, 8 questions)
with proper dimension organization.
"""
import pytest
import pandas as pd
import numpy as np
from core.question_set_manager import QuestionSetManager


class TestQuestionSetManager:
    """Test cases for QuestionSetManager class"""
    
    @pytest.fixture
    def sample_26_questions_data(self):