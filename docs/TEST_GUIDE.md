# Testing Guide - LLM Quality Guardian

## Overview

This guide provides comprehensive instructions for running tests, load testing, and performance validation for the LLM Quality Guardian project.

## Prerequisites

```bash
pip install -r requirements.txt
```

Key test dependencies:
- pytest>=7.0
- flask
- locust>=2.0
- requests

## Test Structure

```
tests/
├── unit/
│   └── test_quality_analyzer.py      # Unit tests for analyzer module
├── integration/
│   ├── test_pipeline.py              # End-to-end pipeline tests
│   └── test_api_endpoints.py         # API endpoint validation
├── load/
│   └── locustfile.py                 # Load testing suite
└── conftest.py                       # Pytest fixtures and configuration
```

## Running Tests

### 1. Unit Tests

**Run all unit tests:**
```bash
pytest tests/unit/ -v
```

**Run specific test file:**
```bash
pytest tests/unit/test_quality_analyzer.py -v
```

**Run with coverage:**
```bash
pytest tests/unit/ --cov=src --cov-report=html
```

### 2. Integration Tests

**Run all integration tests:**
```bash
pytest tests/integration/ -v
```

**Run end-to-end pipeline tests:**
```bash
pytest tests/integration/test_pipeline.py -v
```

**Run API endpoint tests:**
```bash
pytest tests/integration/test_api_endpoints.py -v
```

### 3. Full Test Suite

**Run all tests with markers:**
```bash
pytest tests/ -v
```

**Run only unit tests:**
```bash
pytest -m unit -v
```

**Run only integration tests:**
```bash
pytest -m integration -v
```

### 4. Load Testing

**Start the API first:**
```bash
python -m src.phase3_api_gateway
```

**Light load test (10 users):**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -c 10 -r 1 --run-time 5m
```

**Medium load test (50 users):**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -c 50 -r 5 --run-time 10m
```

**Heavy load test (100 users):**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -c 100 -r 10 --run-time 15m
```

**Stress test (200 users):**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -c 200 -r 20 --run-time 5m
```

## Demo Script

**Run the comprehensive demo:**
```bash
python demo_script.py
```

The demo includes:
- Single text analysis demonstrations
- Batch processing examples
- Hallucination type detection showcase
- Performance metrics display
- API endpoint validation
- Datadog monitoring metrics

## Test Coverage

### Unit Tests Coverage (Target: 80%+)
- QualityAnalyzer: 85%+ coverage
  - Stage A (Syntax): 90%
  - Stage B (Semantic): 85%
  - Stage C (Factual): 80%
  - Stage D (Contradiction): 80%
- API Gateway: 90%+ coverage
- ML Models: 80%+ coverage
- Datadog Monitor: 75%+ coverage

### Integration Test Scenarios
1. Single text analysis (E2E)
2. Batch processing (10, 50, 1000 items)
3. Error handling (invalid input, timeouts)
4. Datadog event logging
5. Concurrent requests (up to 100)

### Performance Benchmarks

| Metric | Target | Acceptable | Critical |
|--------|--------|-----------|----------|
| P50 Latency | <400ms | <600ms | >1000ms |
| P95 Latency | <800ms | <1200ms | >2000ms |
| P99 Latency | <1200ms | <1800ms | >3000ms |
| Throughput | >100 req/s | >50 req/s | <20 req/s |
| Error Rate | <0.5% | <2% | >5% |
| Memory/req | <50MB | <100MB | >200MB |

## Pytest Configuration

Located in `pytest.ini`:
```ini
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = -v --strict-markers --tb=short

markers =
    unit: Unit tests for individual modules
    integration: Integration tests for components
    api: API endpoint tests
    performance: Performance and load tests
```

## CI/CD Integration

### Pre-Commit Checks
```bash
pytest tests/unit/ --cov=src --cov-fail-under=80
```

### GitHub Actions (Example)
```yaml
- name: Run tests
  run: |
    pytest tests/ -v
    locust -f tests/load/locustfile.py -c 10 -r 1 --run-time 1m
```

## Troubleshooting

### Issue: Tests Failing with Import Errors
**Solution:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

### Issue: API Port Already in Use
**Solution:**
```bash
kill -9 $(lsof -t -i:8000)
python -m src.phase3_api_gateway
```

### Issue: Load Test Connection Errors
**Solution:**
1. Ensure API is running: `python -m src.phase3_api_gateway`
2. Check localhost connectivity: `curl http://localhost:8000/health`
3. Verify firewall settings

## Performance Optimization Tips

1. **Model Caching**: Pre-load ML models in API initialization
2. **Batch Optimization**: Process multiple items in parallel
3. **Database Connection Pooling**: Reuse DB connections
4. **Async Processing**: Use async/await for I/O operations
5. **Rate Limiting**: Implement per-client rate limits

## Test Results Archive

Test results are stored in:
- `tests/results/` - Test execution logs
- `tests/coverage/` - Coverage reports
- `tests/load/results/` - Load test reports

## Success Criteria (Phase 4)

✅ Unit Tests: >80% code coverage, all tests passing
✅ Integration Tests: End-to-end pipeline fully functional
✅ Performance: Meets target latency benchmarks
✅ Monitoring: Datadog dashboard live and functional
✅ Demo Ready: All demo scenarios working smoothly
✅ No Critical Bugs: All blocking issues resolved
✅ Optimization: Performance optimized for demo

## Next Steps

After completing Phase 4 testing:
1. Fix any identified issues
2. Optimize critical paths
3. Prepare deployment documentation
4. Create Devpost submission (Phase 5)
5. Package for production deployment
