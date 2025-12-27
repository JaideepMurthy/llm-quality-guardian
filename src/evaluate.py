"""HaluEval Benchmark Evaluation - Day 2 Prototype"""
import json
import sys
from typing import List, Dict
from detector import HallucinationDetector
from datadog_logging import DatadogLogger
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

class BenchmarkEvaluator:
    """Evaluate detector on HaluEval benchmark."""
    
    def __init__(self):
        self.detector = HallucinationDetector()
        self.logger = DatadogLogger()
    
    def load_halueval_sample(self, file_path='halueval_sample.jsonl'):
        """Load HaluEval benchmark sample."""
        data = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    data.append(json.loads(line))
        except FileNotFoundError:
            print(f"Sample file not found. Using synthetic data.")
            data = self._create_synthetic_data()
        return data
    
    def _create_synthetic_data(self, num_samples=100):
        """Create synthetic evaluation data for testing."""
        import random
        data = []
        questions = [
            "What is the capital of France?",
            "Who is the current US President?",
            "What year did WWII end?"
        ]
        correct_answers = [
            "Paris",
            "Joe Biden",
            "1945"
        ]
        
        for i in range(num_samples):
            idx = i % len(questions)
            if random.random() < 0.7:  # 70% correct
                answer = correct_answers[idx]
                label = 0
            else:
                answer = "Unknown or incorrect answer"
                label = 1
            
            data.append({
                'question': questions[idx],
                'reference': correct_answers[idx],
                'answer': answer,
                'hallucinated': label
            })
        return data
    
    def evaluate(self, data: List[Dict], sample_size=None):
        """Evaluate detector on benchmark data."""
        if sample_size:
            data = data[:sample_size]
        
        predictions = []
        ground_truth = []
        scores = []
        
        print(f"Evaluating detector on {len(data)} examples...")
        
        for i, example in enumerate(data):
            if i % 20 == 0:
                print(f"  {i}/{len(data)} completed...")
            
            result = self.detector.detect(
                example['question'],
                example['reference'],
                example['answer']
            )
            
            scores.append(result['score'])
            ground_truth.append(example.get('hallucinated', 0))
            predictions.append(1 if result['hallucinated'] else 0)
        
        # Compute metrics
        accuracy = accuracy_score(ground_truth, predictions)
        precision = precision_score(ground_truth, predictions, zero_division=0)
        recall = recall_score(ground_truth, predictions, zero_division=0)
        f1 = f1_score(ground_truth, predictions, zero_division=0)
        cm = confusion_matrix(ground_truth, predictions)
        
        # Find optimal threshold
        best_threshold = self.detector.find_threshold(scores, ground_truth)
        
        # Log metrics
        self.logger.log_batch_evaluation(accuracy, precision, recall, f1, best_threshold)
        
        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist(),
            'optimal_threshold': best_threshold,
            'total_evaluated': len(data)
        }
        
        return results
    
    def print_results(self, results: Dict):
        """Print evaluation results."""
        print("\n=== Day 2 Prototype Evaluation Results ===")
        print(f"Total Evaluated: {results['total_evaluated']}")
        print(f"Accuracy:   {results['accuracy']:.4f}")
        print(f"Precision:  {results['precision']:.4f}")
        print(f"Recall:     {results['recall']:.4f}")
        print(f"F1-Score:   {results['f1_score']:.4f}")
        print(f"Optimal Threshold: {results['optimal_threshold']}")
        print(f"\nConfusion Matrix:\n{results['confusion_matrix']}")
    
    def save_results(self, results: Dict, output_file='results/benchmark_day2.json'):
        """Save results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {output_file}")
        self.logger.export_metrics()

if __name__ == '__main__':
    evaluator = BenchmarkEvaluator()
    data = evaluator.load_halueval_sample()
    results = evaluator.evaluate(data, sample_size=100)
    evaluator.print_results(results)
    evaluator.save_results(results)
