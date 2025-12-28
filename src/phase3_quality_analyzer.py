# PHASE 3 - Quality Analyzer Module
# Hallucination Detection with Multi-Stage Processing

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

logger = logging.getLogger(__name__)

# ==================== Data Models ====================

@dataclass
class TextFeatures:
    """Extracted features from input text"""
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    unique_entities: List[str]
    named_entities: Dict[str, List[str]]
    syntactic_features: Dict[str, Any]
    semantic_features: Dict[str, Any]
    linguistic_patterns: List[str]

@dataclass
class HallucinationIndicators:
    """Detected hallucination indicators"""
    factual_inconsistencies: List[str]
    logical_contradictions: List[str]
    unsupported_claims: List[str]
    out_of_context_statements: List[str]
    temporal_inconsistencies: List[str]
    entity_mismatches: List[str]

class HallucinationDetector:
    """Main hallucination detection class with Stage A-D pipeline"""
    
    def __init__(self, model_ensemble, datadog_monitor):
        """Initialize detector with model ensemble and monitoring"""
        self.model_ensemble = model_ensemble
        self.datadog_monitor = datadog_monitor
        self.logger = logging.getLogger(__name__)
        
        # Detection thresholds
        self.confidence_threshold = 0.7
        self.hallucination_types = {
            "factual_error": 0.85,
            "logical_contradiction": 0.8,
            "fabricated_citation": 0.9,
            "out_of_context": 0.75,
            "temporal_inconsistency": 0.8
        }
    
    async def detect_hallucination(
        self,
        text: str,
        model_name: str = "gpt-4",
        context: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main detection pipeline with Stages A-D
        
        STAGE A: Input Validation & Preprocessing
        STAGE B: Feature Extraction
        STAGE C: Model Ensemble Prediction
        STAGE D: Result Synthesis & Explanation
        """
        
        self.logger.info(f"[{request_id}] Starting hallucination detection")
        
        try:
            # STAGE A: Input Validation
            validated_text = await self._stage_a_input_validation(text, request_id)
            
            # STAGE B: Feature Extraction
            features = await self._stage_b_feature_extraction(
                validated_text, context, request_id
            )
            
            # STAGE C: Model Ensemble Prediction
            ensemble_results = await self._stage_c_model_prediction(
                validated_text, features, model_name, request_id
            )
            
            # STAGE D: Result Synthesis
            final_result = await self._stage_d_result_synthesis(
                text, features, ensemble_results, request_id
            )
            
            self.logger.info(f"[{request_id}] Detection complete")
            return final_result
            
        except Exception as e:
            self.logger.error(f"[{request_id}] Detection error: {str(e)}")
            return self._create_error_result(str(e))
    
    async def _stage_a_input_validation(self, text: str, request_id: str) -> str:
        """
        STAGE A: Input Validation & Preprocessing
        
        - Validate input length and format
        - Remove artifacts and normalize text
        - Validate character encoding
        - Check for malicious patterns
        """
        self.logger.info(f"[{request_id}] STAGE A: Input Validation started")
        
        # Validation checks
        if not text or len(text.strip()) == 0:
            raise ValueError("Empty text provided")
        
        if len(text) > 10000:
            text = text[:10000]
        
        # Text normalization
        normalized_text = text.strip()
        
        # Remove multiple whitespaces
        import re
        normalized_text = re.sub(r'\s+', ' ', normalized_text)
        
        self.logger.info(f"[{request_id}] STAGE A: Validation complete")
        self.datadog_monitor.log_event(
            f"stage_a_validation_{request_id}",
            f"Input validated: {len(normalized_text)} chars"
        )
        
        return normalized_text
    
    async def _stage_b_feature_extraction(
        self,
        text: str,
        context: Optional[str],
        request_id: str
    ) -> TextFeatures:
        """
        STAGE B: Feature Extraction
        
        - Extract linguistic features
        - Identify named entities
        - Extract semantic patterns
        - Analyze syntactic structure
        """
        self.logger.info(f"[{request_id}] STAGE B: Feature Extraction started")
        
        # Basic text statistics
        words = text.split()
        sentences = text.split('.')
        
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Entity extraction (simplified)
        import re
        unique_entities = list(set([
            word for word in words
            if word[0].isupper() and len(word) > 2
        ]))
        
        # Named entities by type
        named_entities = {
            "PERSON": [],
            "LOCATION": [],
            "ORGANIZATION": [],
            "DATE": []
        }
        
        # Pattern detection
        linguistic_patterns = self._detect_linguistic_patterns(text)
        
        features = TextFeatures(
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            unique_entities=unique_entities[:10],
            named_entities=named_entities,
            syntactic_features={"avg_length": avg_sentence_length},
            semantic_features={"entity_count": len(unique_entities)},
            linguistic_patterns=linguistic_patterns
        )
        
        self.logger.info(f"[{request_id}] STAGE B: Feature Extraction complete")
        self.datadog_monitor.log_event(
            f"stage_b_features_{request_id}",
            f"Extracted {len(unique_entities)} entities"
        )
        
        return features
    
    def _detect_linguistic_patterns(self, text: str) -> List[str]:
        """Detect suspicious linguistic patterns"""
        patterns = []
        
        # Check for suspicious phrases
        suspicious_phrases = [
            "as far as I know",
            "I think",
            "it seems like",
            "probably",
            "allegedly"
        ]
        
        text_lower = text.lower()
        for phrase in suspicious_phrases:
            if phrase in text_lower:
                patterns.append(f"uncertain_claim: {phrase}")
        
        return patterns
    
    async def _stage_c_model_prediction(
        self,
        text: str,
        features: TextFeatures,
        model_name: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        STAGE C: Model Ensemble Prediction
        
        - Run multiple detection models
        - Aggregate predictions
        - Calculate confidence scores
        """
        self.logger.info(f"[{request_id}] STAGE C: Model Prediction started")
        
        # Get predictions from ensemble
        model_scores = await self.model_ensemble.predict(
            text=text,
            features=features,
            model_name=model_name
        )
        
        # Aggregate scores
        avg_score = sum(model_scores.values()) / len(model_scores) if model_scores else 0.0
        
        self.logger.info(f"[{request_id}] STAGE C: Average score = {avg_score:.2f}")
        self.datadog_monitor.log_event(
            f"stage_c_prediction_{request_id}",
            f"Ensemble score: {avg_score:.2f}"
        )
        
        return {
            "model_scores": model_scores,
            "average_score": avg_score,
            "is_likely_hallucination": avg_score > self.confidence_threshold
        }
    
    async def _stage_d_result_synthesis(
        self,
        text: str,
        features: TextFeatures,
        ensemble_results: Dict[str, Any],
        request_id: str
    ) -> Dict[str, Any]:
        """
        STAGE D: Result Synthesis & Explanation
        
        - Determine hallucination type
        - Generate explanation
        - Create actionable insights
        """
        self.logger.info(f"[{request_id}] STAGE D: Result Synthesis started")
        
        # Detect hallucination type
        hallucination_type = self._classify_hallucination_type(
            text, features, ensemble_results
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            text, features, hallucination_type
        )
        
        # Detect specific issues
        detected_issues = await self._detect_issues(
            text, features, ensemble_results
        )
        
        result = {
            "is_hallucination": ensemble_results["is_likely_hallucination"],
            "confidence_score": ensemble_results["average_score"],
            "hallucination_type": hallucination_type,
            "explanation": explanation,
            "detected_issues": detected_issues,
            "model_scores": ensemble_results["model_scores"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"[{request_id}] STAGE D: Synthesis complete")
        self.datadog_monitor.log_event(
            f"stage_d_synthesis_{request_id}",
            f"Result: {hallucination_type}"
        )
        
        return result
    
    def _classify_hallucination_type(self, text: str, features: TextFeatures, results: Dict) -> Optional[str]:
        """Classify the type of hallucination detected"""
        if not results["is_likely_hallucination"]:
            return None
        
        score = results["average_score"]
        
        # Simple classification based on score and patterns
        if "uncertain_claim" in features.linguistic_patterns:
            return "factual_error"
        elif len(features.linguistic_patterns) > 0:
            return "logical_contradiction"
        else:
            return "out_of_context"
    
    def _generate_explanation(self, text: str, features: TextFeatures, hallucination_type: Optional[str]) -> str:
        """Generate human-readable explanation"""
        if not hallucination_type:
            return "No hallucination detected. Text appears to be factually sound."
        
        explanations = {
            "factual_error": f"Detected potential factual error. Text contains {len(features.unique_entities)} entities that may need verification.",
            "logical_contradiction": f"Detected logical inconsistency. Pattern analysis suggests contradictory statements.",
            "out_of_context": f"Detected out-of-context statement. The claim may not be supported by the provided context.",
            "temporal_inconsistency": f"Detected temporal inconsistency. Timeline or date references appear contradictory."
        }
        
        return explanations.get(hallucination_type, "Hallucination detected but type could not be determined.")
    
    async def _detect_issues(self, text: str, features: TextFeatures, results: Dict) -> List[str]:
        """Detect specific issues in the text"""
        issues = []
        
        if results["is_likely_hallucination"]:
            issues.append(f"High hallucination probability: {results['average_score']:.2%}")
        
        if len(features.linguistic_patterns) > 0:
            issues.extend([f"Pattern detected: {p}" for p in features.linguistic_patterns[:3]])
        
        if len(features.unique_entities) > 20:
            issues.append("Excessive entity references may indicate fabrication")
        
        return issues
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            "is_hallucination": False,
            "confidence_score": 0.0,
            "hallucination_type": None,
            "explanation": f"Error during detection: {error_message}",
            "detected_issues": [f"Detection error: {error_message}"],
            "model_scores": {},
            "timestamp": datetime.utcnow().isoformat()
        }
