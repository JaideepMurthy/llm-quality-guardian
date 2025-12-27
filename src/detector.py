"""Hallucination Detection Engine - LLM Quality Guardian"""
import json
from typing import Dict, Any
from datadog_logging import DatadogLogger

class HallucinationDetector:
    """Core detector using LLM-as-judge pattern."""
    
    def __init__(self, model_name='gemini-1.5-flash', api_key=None):
        import google.generativeai as genai
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger = DatadogLogger()
        self.scores = []
        self.labels = []
    
    def judge_answer(self, question: str, reference: str, candidate: str) -> int:
        """Score factual correctness (0-100)."""
        prompt = f"""Compare the candidate answer against reference. 
Question: {question}
Reference: {reference}
Candidate: {candidate}
Rate correctness (0-100): """
        
        response = self.model.generate_content(prompt)
        try:
            score = int(float(response.text.strip()))
            return max(0, min(100, score))
        except:
            return 50
    
    def detect(self, question: str, ref: str, answer: str) -> Dict[str, Any]:
        """Detect hallucination."""
        score = self.judge_answer(question, ref, answer)
        is_hallucinated = score < 65
        self.scores.append(score)
        return {
            'score': score,
            'hallucinated': is_hallucinated,
            'confidence': abs(score - 50) / 50
        }
    
    def find_threshold(self, scores, labels):
        """Optimize threshold using F1."""
        from sklearn.metrics import f1_score
        best_f1, best_thresh = 0, 50
        for t in range(0, 101, 5):
            preds = [1 if s < t else 0 for s in scores]
            f1 = f1_score(labels, preds, zero_division=0)
            if f1 > best_f1:
                best_f1, best_thresh = f1, t
        return best_thresh
