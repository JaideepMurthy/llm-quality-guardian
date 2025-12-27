"""Datadog Instrumentation & Logging"""
import os
from datetime import datetime
import json

class DatadogLogger:
    """Minimal Datadog integration for custom metrics & traces."""
    
    def __init__(self, service='llm-quality-guardian', env='prod'):
        self.service = service
        self.env = env
        self.traces = []
        self.metrics = {}
        self.api_key = os.getenv('DD_API_KEY')
    
    def log_detection(self, question, score, hallucinated, latency_ms):
        """Log hallucination detection event."""
        trace = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.service,
            'span_name': 'hallucination.detect',
            'duration_ms': latency_ms,
            'tags': {
                'hallucination.score': score,
                'hallucination.label': 1 if hallucinated else 0,
                'question_len': len(question),
            },
            'metrics': {
                'detection_latency_ms': latency_ms,
                'score': score,
            }
        }
        self.traces.append(trace)
        return trace
    
    def log_batch_evaluation(self, accuracy, precision, recall, f1, threshold):
        """Log benchmark evaluation metrics."""
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'threshold': threshold,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.metrics.update(metrics)
        return metrics
    
    def export_metrics(self, output_file='metrics.json'):
        """Export all metrics to JSON file."""
        with open(output_file, 'w') as f:
            json.dump({
                'traces': self.traces,
                'summary_metrics': self.metrics,
                'total_detections': len(self.traces),
                'export_time': datetime.utcnow().isoformat()
            }, f, indent=2)
        return output_file
