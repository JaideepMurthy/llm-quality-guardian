import pytest
from src.phase3_quality_analyzer import QualityAnalyzer

class TestQualityAnalyzer:
    """Unit tests for QualityAnalyzer module"""
    
    @pytest.fixture
    def analyzer(self):
        return QualityAnalyzer()
    
    def test_initialization(self, analyzer):
        """Test QualityAnalyzer initialization"""
        assert analyzer is not None
        assert hasattr(analyzer, 'quality_heuristics')
        assert hasattr(analyzer, 'semantic_analyzer')
        assert hasattr(analyzer, 'factual_verifier')
        assert hasattr(analyzer, 'contradiction_detector')
    
    def test_stage_a_syntax_check(self, analyzer):
        """Test Stage A: Syntax and Structure Check"""
        valid_text = "This is a valid sentence."
        result = analyzer.quality_heuristics(valid_text)
        assert isinstance(result, dict)
        assert 'syntax_score' in result
        assert 0 <= result['syntax_score'] <= 1
    
    def test_stage_b_semantic_analysis(self, analyzer):
        """Test Stage B: Semantic Analysis"""
        text = "The moon is made of green cheese."
        result = analyzer.semantic_analyzer(text)
        assert isinstance(result, dict)
        assert 'semantic_score' in result
        assert 0 <= result['semantic_score'] <= 1
    
    def test_stage_c_factual_verification(self, analyzer):
        """Test Stage C: Factual Verification"""
        hallucination = "Paris is the capital of Germany."
        result = analyzer.factual_verifier(hallucination)
        assert isinstance(result, dict)
        assert 'factual_score' in result
        assert 0 <= result['factual_score'] <= 1
    
    def test_stage_d_contradiction_detection(self, analyzer):
        """Test Stage D: Contradiction Detection"""
        contradiction = "John is 25 years old but was born 50 years ago."
        result = analyzer.contradiction_detector(contradiction)
        assert isinstance(result, dict)
        assert 'contradiction_score' in result
        assert 0 <= result['contradiction_score'] <= 1
    
    def test_empty_input(self, analyzer):
        """Test handling of empty input"""
        with pytest.raises(ValueError):
            analyzer.quality_heuristics("")
    
    def test_very_long_input(self, analyzer):
        """Test handling of very long input"""
        long_text = "word " * 5000  # 25K characters
        result = analyzer.quality_heuristics(long_text[:10000])  # Truncate to 10K limit
        assert isinstance(result, dict)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
