"""Locustfile for LLM Quality Guardian load testing
Phase 4: Performance validation and stress testing

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
    locust -f tests/load/locustfile.py --host=http://localhost:8000 -c 50 -r 5 --run-time 5m
"""

import random
from locust import HttpUser, task, between, events
import time

# Test data
HALLUCINATION_TESTS = [
    "The moon is made of green cheese.",
    "Paris is the capital of Germany.",
    "Water boils at 50 degrees Celsius.",
    "The Earth is flat.",
    "Napoleon was 6 inches tall.",
]

VALID_TESTS = [
    "The Earth revolves around the Sun.",
    "Paris is the capital of France.",
    "Water boils at 100 degrees Celsius.",
    "The Great Wall of China is visible from space.",
    "Albert Einstein developed the theory of relativity.",
]

class HallucrationDetectionUser(HttpUser):
    """Simulates a user performing hallucination detection requests"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.request_count = 0
        self.error_count = 0
    
    @task(3)  # Higher weight for single text analysis
    def analyze_single_text(self):
        """Task: Analyze single text for hallucination"""
        text = random.choice(HALLUCINATION_TESTS + VALID_TESTS)
        payload = {
            "text": text,
            "model_name": random.choice(["gpt-4", "claude-2", "gemini"])
        }
        
        with self.client.post("/analyze", json=payload, catch_response=True) as response:
            self.request_count += 1
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
                self.error_count += 1
    
    @task(2)  # Medium weight for batch analysis
    def batch_analyze_texts(self):
        """Task: Batch analyze multiple texts"""
        batch_size = random.randint(5, 20)
        texts = random.choices(HALLUCINATION_TESTS + VALID_TESTS, k=batch_size)
        payload = {
            "texts": texts,
            "model_name": random.choice(["gpt-4", "claude-2", "gemini"])
        }
        
        with self.client.post("/batch-analyze", json=payload, catch_response=True) as response:
            self.request_count += 1
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
                self.error_count += 1
    
    @task(1)  # Low weight for health checks
    def health_check(self):
        """Task: Check API health"""
        with self.client.get("/health", catch_response=True) as response:
            self.request_count += 1
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
                self.error_count += 1
    
    def on_stop(self):
        """Called when a simulated user stops"""
        print(f"User stopping. Requests: {self.request_count}, Errors: {self.error_count}")

# Custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts"""
    print("\n" + "="*60)
    print("LLM Quality Guardian Load Test Started")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops"""
    print("\n" + "="*60)
    print("Load Test Completed")
    print("="*60)
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.0f}ms")
    print(f"Median response time: {environment.stats.total.median_response_time:.0f}ms")
    if environment.stats.total.num_requests > 0:
        success_rate = (1 - environment.stats.total.num_failures / environment.stats.total.num_requests) * 100
        print(f"Success rate: {success_rate:.1f}%")

# Load test scenarios
"""
Scenario 1: Light Load (Low: 10 users, 1 req/sec)
    locust -f tests/load/locustfile.py -c 10 -r 1 --run-time 5m

Scenario 2: Medium Load (Medium: 50 users, 5 req/sec)
    locust -f tests/load/locustfile.py -c 50 -r 5 --run-time 10m

Scenario 3: High Load (High: 100 users, 10 req/sec)
    locust -f tests/load/locustfile.py -c 100 -r 10 --run-time 15m

Scenario 4: Stress Test (200 users, 20 req/sec)
    locust -f tests/load/locustfile.py -c 200 -r 20 --run-time 5m
"""
