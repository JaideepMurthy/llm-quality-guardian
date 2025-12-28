import pytest
import requests
import json
from flask import Flask
from src.phase3_api_gateway import app

class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_analyze_endpoint_valid(self, client):
        """Test POST /analyze with valid input"""
        payload = {
            "text": "The moon is made of green cheese.",
            "model_name": "gpt-4"
        }
        response = client.post('/analyze', 
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'hallucination_score' in data
        assert 'detection_type' in data
    
    def test_analyze_endpoint_missing_text(self, client):
        """Test POST /analyze with missing text field"""
        payload = {"model_name": "gpt-4"}
        response = client.post('/analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_analyze_endpoint_empty_text(self, client):
        """Test POST /analyze with empty text"""
        payload = {"text": "", "model_name": "gpt-4"}
        response = client.post('/analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_analyze_endpoint_text_too_long(self, client):
        """Test POST /analyze with text exceeding limit"""
        long_text = "word " * 3000
        payload = {"text": long_text, "model_name": "gpt-4"}
        response = client.post('/analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 413  # Payload too large
    
    def test_batch_analyze_endpoint_valid(self, client):
        """Test POST /batch-analyze with valid input"""
        payload = {
            "texts": [
                "Paris is the capital of France.",
                "The moon is made of green cheese.",
                "New York is in California."
            ],
            "model_name": "gpt-4"
        }
        response = client.post('/batch-analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert len(data['results']) == 3
    
    def test_batch_analyze_endpoint_empty(self, client):
        """Test POST /batch-analyze with empty texts"""
        payload = {"texts": [], "model_name": "gpt-4"}
        response = client.post('/batch-analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_batch_analyze_endpoint_large_batch(self, client):
        """Test POST /batch-analyze with large batch"""
        texts = [f"Sample text {i}" for i in range(1000)]
        payload = {"texts": texts, "model_name": "gpt-4"}
        response = client.post('/batch-analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code in [200, 413]  # Either OK or too large
    
    def test_health_endpoint(self, client):
        """Test GET /health endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_status_endpoint(self, client):
        """Test GET /status endpoint"""
        response = client.get('/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'api_version' in data
        assert 'uptime' in data
    
    def test_config_endpoint(self, client):
        """Test GET /config endpoint"""
        response = client.get('/config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'models' in data
        assert 'max_text_length' in data
    
    def test_analyze_endpoint_invalid_model(self, client):
        """Test POST /analyze with invalid model name"""
        payload = {
            "text": "Test text.",
            "model_name": "invalid-model-xyz"
        }
        response = client.post('/analyze',
                             json=payload,
                             content_type='application/json')
        assert response.status_code in [400, 404]
    
    def test_analyze_endpoint_malformed_json(self, client):
        """Test POST /analyze with malformed JSON"""
        response = client.post('/analyze',
                             data="{invalid json",
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_response_headers(self, client):
        """Test response headers contain correct content type"""
        payload = {"text": "Test text.", "model_name": "gpt-4"}
        response = client.post('/analyze', json=payload)
        assert 'Content-Type' in response.headers
        assert 'application/json' in response.headers['Content-Type']
    
    def test_multiple_requests_sequential(self, client):
        """Test multiple sequential requests"""
        payload = {"text": "Test hallucination.", "model_name": "gpt-4"}
        for i in range(5):
            response = client.post('/analyze', json=payload)
            assert response.status_code == 200
    
    def test_analyze_endpoint_various_text_lengths(self, client):
        """Test analyze endpoint with various text lengths"""
        test_cases = [
            "Short text.",
            "This is a medium length text that tests hallucination detection.",
            "word " * 100,  # ~500 chars
        ]
        for text in test_cases:
            payload = {"text": text, "model_name": "gpt-4"}
            response = client.post('/analyze', json=payload)
            assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
