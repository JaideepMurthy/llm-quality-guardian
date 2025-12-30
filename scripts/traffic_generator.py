#!/usr/bin/env python3
"""
Traffic Generator for LLM Quality Guardian

Generates test traffic to demonstrate hallucination detection and Datadog monitoring.
Sends queries that include hallucinations to trigger detection rules.
"""

import requests
import json
import time
import sys
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_ENDPOINT = "http://localhost:8000/analyze"  # Change to deployed URL
NUM_REQUESTS = 20
REQUEST_INTERVAL = 2  # seconds

# Test cases: queries with varying hallucination risk
TEST_QUERIES = [
    {
        "text": "What is the capital of France?",
        "expected_answer": "Paris",
        "is_hallucination": False
    },
    {
        "text": "Who is the current President of the United States as of 2025?",
        "expected_answer": "I don't have information about current events",
        "is_hallucination": False
    },
    {
        "text": "What is the square root of 16?",
        "expected_answer": "4",
        "is_hallucination": False
    },
    {
        "text": "Did Einstein invent the internet?",
        "expected_answer": "No, Einstein did not invent the internet",
        "is_hallucination": False
    },
    {
        "text": "What color is the sky on Mars?",
        "expected_answer": "The Martian sky appears reddish/butterscotch due to dust",
        "is_hallucination": False
    },
]

def send_query(query_text: str) -> Dict:
    """
    Send a query to the LLM Quality Guardian API.
    
    Args:
        query_text: The question to analyze
        
    Returns:
        API response JSON
    """
    payload = {
        "query": query_text,
        "include_confidence": True
    }
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"error": str(e)}

def generate_traffic(num_requests: int = NUM_REQUESTS):
    """
    Generate test traffic to the API.
    
    Args:
        num_requests: Number of requests to send
    """
    logger.info(f"Starting traffic generation: {num_requests} requests")
    logger.info(f"Target API: {API_ENDPOINT}")
    logger.info("-" * 70)
    
    successful_requests = 0
    failed_requests = 0
    high_hallucination_detections = 0
    
    for i in range(num_requests):
        # Select a test query (cycle through them)
        test_case = TEST_QUERIES[i % len(TEST_QUERIES)]
        query_text = test_case["text"]
        
        logger.info(f"Request {i+1}/{num_requests}: {query_text[:50]}...")
        
        # Send request
        result = send_query(query_text)
        
        if "error" in result:
            failed_requests += 1
            logger.warning(f"  Status: FAILED - {result['error']}")
        else:
            successful_requests += 1
            
            # Extract hallucination score
            hallucination_score = result.get("hallucination_score", 0)
            confidence = result.get("confidence", 0)
            
            logger.info(f"  Status: SUCCESS")
            logger.info(f"  Hallucination Score: {hallucination_score:.2f}")
            logger.info(f"  Confidence: {confidence:.2f}")
            
            # Trigger detection if score is high
            if hallucination_score > 0.7:
                high_hallucination_detections += 1
                logger.warning(f"  🚨 HIGH HALLUCINATION DETECTED - Score: {hallucination_score:.2f}")
                logger.warning(f"  This should trigger a Datadog detection rule alert")
        
        logger.info("-" * 70)
        
        # Wait before next request
        if i < num_requests - 1:
            time.sleep(REQUEST_INTERVAL)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TRAFFIC GENERATION SUMMARY")
    logger.info("="*70)
    logger.info(f"Total Requests Sent: {num_requests}")
    logger.info(f"Successful: {successful_requests}")
    logger.info(f"Failed: {failed_requests}")
    logger.info(f"High Hallucination Detections: {high_hallucination_detections}")
    logger.info("="*70)
    logger.info("\nTraffic generation complete!")
    logger.info("Check your Datadog dashboard for monitoring metrics and alerts.")
    logger.info(f"Dashboard: https://app.datadoghq.com/dashboard/p4k-7se-hhe")

if __name__ == "__main__":
    try:
        num_requests = int(sys.argv[1]) if len(sys.argv) > 1 else NUM_REQUESTS
        generate_traffic(num_requests)
    except KeyboardInterrupt:
        logger.info("\nTraffic generation interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
