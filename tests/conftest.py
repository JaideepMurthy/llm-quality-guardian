import pytest
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.example
load_dotenv('.env.example')

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class MockDatadog:
    """Mock Datadog client for testing"""
    def __init__(self):
        self.events = []
        self.metrics = []
    
    def send_event(self, event):
        self.events.append(event)
    
    def send_metric(self, metric):
        self.metrics.append(metric)

class MockModel:
    """Mock ML model for testing"""
    def predict(self, features):
        return 0.5  # Default neutral score

@pytest.fixture(scope="session")
def datadog_client():
    """Provide mock Datadog client for entire test session"""
    return MockDatadog()

@pytest.fixture(scope="session")
def test_data():
    """Provide test data for entire test session"""
    return {
        "hallucinations": [
            "The moon is made of green cheese.",
            "Paris is the capital of Germany.",
            "John is 25 years old but was born 50 years ago."
        ],
        "valid_texts": [
            "The Earth revolves around the Sun.",
            "Paris is the capital of France.",
            "Water boils at 100 degrees Celsius."
        ],
        "edge_cases": [
            "",  # Empty
            "word " * 5000,  # Very long
            "!@#$%^&*()",  # Special characters
        ]
    }

@pytest.fixture
def sample_texts():
    """Provide sample texts for tests"""
    return {
        "factual": "The sky appears blue due to Rayleigh scattering.",
        "hallucination": "The moon is made of green cheese.",
        "contradiction": "John is 25 years old but was born 50 years ago and will be 30 next year.",
        "logical_error": "All birds can fly because eagles can fly."
    }

@pytest.fixture
def api_client():
    """Provide Flask test client for API tests"""
    from src.phase3_api_gateway import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_model():
    """Provide mock ML model for tests"""
    return MockModel()

@pytest.fixture(autouse=True)
def reset_mock_datadog(datadog_client):
    """Reset mock Datadog before each test"""
    datadog_client.events = []
    datadog_client.metrics = []
    yield

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual modules"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for components"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Auto-mark based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
