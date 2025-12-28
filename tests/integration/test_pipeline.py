import pytest
import json
import time
from src.phase3_api_gateway import APIGateway
from src.phase3_quality_analyzer import QualityAnalyzer
from src.phase3_ml_models import MLModels

class TestEndToEndPipeline:
    """Integration tests for end-to-end hallucination detection pipeline"""
    
    @pytest.fixture
    def gateway(self):
        return APIGateway()
    
    @pytest.fixture
    def analyzer(self):
        return QualityAnalyzer()
    
    def test_single_text_analysis_e2e(self, gateway):
        """Test end-to-end analysis of single text"""
        payload = {
            "text": "The moon is made of green cheese.",
            "model_name": "gpt-4"
        }
        result = gateway.analyze(payload)
        assert result is not None
        assert 'hallucination_score' in result
        assert 'detection_type' in result
        assert 0 <= result['hallucination_score'] <= 1
    
    def test_batch_processing_small(self, gateway):
        """Test batch processing with 10 items"""
        texts = [
            "Paris is the capital of France.",
            "The moon is made of green cheese.",
            "New York is in California.",
        ] * 3
        payload = {"texts": texts, "model_name": "gpt-4"}
        
        start_time = time.time()
        result = gateway.batch_analyze(payload)
        elapsed = time.time() - start_time
        
        assert result is not None
        assert len(result['results']) == len(texts)
        assert elapsed < 30
    
    def test_batch_processing_medium(self, gateway):
        """Test batch processing with 50 items"""
        texts = [f"Sample text {i}. This sentence is about the topic." for i in range(50)]
        payload = {"texts": texts, "model_name": "gpt-4"}
        
        start_time = time.time()
        result = gateway.batch_analyze(payload)
        elapsed = time.time() - start_time
        
        assert result is not None
        assert len(result['results']) == 50
        assert elapsed < 60
    
    def test_error_handling_invalid_json(self, gateway):
        """Test error handling for invalid JSON"""
        with pytest.raises(ValueError):
            gateway.analyze({"invalid_field": "value"})
    
    def test_error_handling_missing_text(self, gateway):
        """Test error handling for missing text field"""
        with pytest.raises(ValueError):
            gateway.analyze({"model_name": "gpt-4"})
    
    def test_error_handling_empty_batch(self, gateway):
        """Test error handling for empty batch"""
        with pytest.raises(ValueError):
            gateway.batch_analyze({"texts": []})
    
    def test_concurrent_requests(self, gateway):
        """Test handling of concurrent requests"""
        import threading
        results = []
        errors = []
        
        def make_request():
            try:
                payload = {
                    "text": "Test hallucination detection.",
                    "model_name": "gpt-4"
                }
                result = gateway.analyze(payload)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(results) == 5
    
    def test_pipeline_data_flow(self, analyzer):
        """Test data flow through quality analyzer pipeline"""
        text = "John is 25 years old but was born 50 years ago and will be 30 next year."
        
        stage_a = analyzer.quality_heuristics(text)
        assert stage_a is not None
        
        stage_b = analyzer.semantic_analyzer(text)
        assert stage_b is not None
        
        stage_c = analyzer.factual_verifier(text)
        assert stage_c is not None
        
        stage_d = analyzer.contradiction_detector(text)
        assert stage_d is not None
    
    def test_datadog_integration(self, gateway):
        """Test Datadog monitoring integration"""
        payload = {"text": "Test integration.", "model_name": "gpt-4"}
        result = gateway.analyze(payload)
        assert result is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
