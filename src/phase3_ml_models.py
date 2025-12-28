# PHASE 3 - ML Model Ensemble
# Multiple ML models for robust hallucination detection

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# ==================== Base Model Classes ====================

class HallucinationModel(ABC):
    """Abstract base class for hallucination detection models"""
    
    def __init__(self, model_name: str, version: str = "1.0"):
        self.model_name = model_name
        self.version = version
        self.logger = logging.getLogger(__name__)
        self.is_loaded = False
    
    @abstractmethod
    async def predict(self, text: str, features: Dict[str, Any]) -> float:
        """
        Make prediction on text
        
        Args:
            text: Input text to analyze
            features: Extracted features from text
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        pass
    
    @abstractmethod
    async def load(self):
        """Load model weights and configuration"""
        pass
    
    def get_info(self) -> Dict[str, str]:
        """Get model information"""
        return {
            "name": self.model_name,
            "version": self.version,
            "loaded": self.is_loaded
        }

# ==================== Concrete Model Implementations ====================

class FactualConsistencyModel(HallucinationModel):
    """Model for detecting factual inconsistencies"""
    
    def __init__(self):
        super().__init__("factual_consistency_model", "1.0")
    
    async def load(self):
        """Load model"""
        self.logger.info(f"Loading {self.model_name}")
        # In production, load actual model weights
        self.is_loaded = True
    
    async def predict(self, text: str, features: Dict[str, Any]) -> float:
        """
        Predict hallucination probability based on factual consistency
        """
        score = 0.0
        
        # Check for factual markers
        if "wikipedia" in text.lower() or "according to" in text.lower():
            score += 0.1
        
        if "I believe" in text or "I think" in text:
            score += 0.15
        
        if "however" in text.lower() or "but" in text.lower():
            score -= 0.1
        
        # Entity consistency check
        entity_count = len(features.get("unique_entities", []))
        if entity_count > 15:
            score += 0.2
        
        return max(0.0, min(1.0, score))

class LogicalCoherenceModel(HallucinationModel):
    """Model for detecting logical inconsistencies"""
    
    def __init__(self):
        super().__init__("logical_coherence_model", "1.0")
    
    async def load(self):
        """Load model"""
        self.logger.info(f"Loading {self.model_name}")
        self.is_loaded = True
    
    async def predict(self, text: str, features: Dict[str, Any]) -> float:
        """
        Predict hallucination probability based on logical coherence
        """
        score = 0.0
        
        # Check sentence structure
        avg_length = features.get("avg_sentence_length", 0)
        if avg_length > 30:
            score += 0.1
        
        # Check for contradictory words
        contradictions = ["but", "however", "although", "yet"]
        text_lower = text.lower()
        contradiction_count = sum(1 for word in contradictions if word in text_lower)
        if contradiction_count > 2:
            score += 0.15
        
        # Check linguistic patterns
        patterns = features.get("linguistic_patterns", [])
        if len(patterns) > 0:
            score += 0.1 * min(len(patterns), 3) / 3
        
        return max(0.0, min(1.0, score))

class SemanticSimilarityModel(HallucinationModel):
    """Model for detecting semantic anomalies"""
    
    def __init__(self):
        super().__init__("semantic_similarity_model", "1.0")
    
    async def load(self):
        """Load model"""
        self.logger.info(f"Loading {self.model_name}")
        self.is_loaded = True
    
    async def predict(self, text: str, features: Dict[str, Any]) -> float:
        """
        Predict hallucination probability based on semantic consistency
        """
        score = 0.0
        
        # Check word count and diversity
        word_count = features.get("word_count", 0)
        entity_count = len(features.get("unique_entities", []))
        
        # High entity to word ratio may indicate fabrication
        if word_count > 0:
            entity_ratio = entity_count / word_count
            if entity_ratio > 0.3:
                score += 0.2
        
        # Check semantic features
        semantic_features = features.get("semantic_features", {})
        if semantic_features.get("entity_count", 0) > 10:
            score += 0.15
        
        return max(0.0, min(1.0, score))

class SyntacticAnomalyModel(HallucinationModel):
    """Model for detecting syntactic anomalies"""
    
    def __init__(self):
        super().__init__("syntactic_anomaly_model", "1.0")
    
    async def load(self):
        """Load model"""
        self.logger.info(f"Loading {self.model_name}")
        self.is_loaded = True
    
    async def predict(self, text: str, features: Dict[str, Any]) -> float:
        """
        Predict hallucination probability based on syntactic patterns
        """
        score = 0.0
        
        # Analyze sentence structure
        avg_length = features.get("avg_sentence_length", 0)
        
        # Very short or very long sentences might indicate issues
        if avg_length < 5:
            score += 0.1
        elif avg_length > 40:
            score += 0.15
        
        # Check for fragmented text
        sentence_count = features.get("sentence_count", 0)
        if sentence_count == 1 and features.get("word_count", 0) > 100:
            score += 0.2
        
        # Check syntactic features
        syntactic_features = features.get("syntactic_features", {})
        if syntactic_features.get("avg_length", 0) > 35:
            score += 0.1
        
        return max(0.0, min(1.0, score))

class EnsembleAnomalyModel(HallucinationModel):
    """Meta-model that combines multiple signals"""
    
    def __init__(self):
        super().__init__("ensemble_anomaly_model", "1.0")
        self.models: List[HallucinationModel] = []
    
    async def load(self):
        """Load model"""
        self.logger.info(f"Loading {self.model_name}")
        self.is_loaded = True
    
    async def predict(self, text: str, features: Dict[str, Any]) -> float:
        """
        Combine predictions from multiple models
        """
        # For simplicity, return weighted average if models provided
        if not self.models:
            return 0.3  # Default neutral score
        
        scores = []
        for model in self.models:
            try:
                score = await model.predict(text, features)
                scores.append(score)
            except Exception as e:
                logger.error(f"Error in model {model.model_name}: {str(e)}")
        
        if not scores:
            return 0.3
        
        return sum(scores) / len(scores)

# ==================== Model Ensemble Manager ====================

class ModelEnsemble:
    """Manages ensemble of hallucination detection models"""
    
    def __init__(self):
        self.models: Dict[str, HallucinationModel] = {}
        self.logger = logging.getLogger(__name__)
        self.is_loaded = False
    
    async def load_models(self):
        """
        Load all models in the ensemble
        """
        self.logger.info("Loading model ensemble...")
        
        try:
            # Initialize models
            self.models = {
                "factual_consistency": FactualConsistencyModel(),
                "logical_coherence": LogicalCoherenceModel(),
                "semantic_similarity": SemanticSimilarityModel(),
                "syntactic_anomaly": SyntacticAnomalyModel(),
            }
            
            # Load each model
            tasks = [model.load() for model in self.models.values()]
            await asyncio.gather(*tasks)
            
            self.is_loaded = True
            self.logger.info(f"Loaded {len(self.models)} models successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            raise
    
    async def predict(
        self,
        text: str,
        features: Dict[str, Any],
        model_name: str = "gpt-4"
    ) -> Dict[str, float]:
        """
        Get predictions from all models
        
        Args:
            text: Input text to analyze
            features: Extracted features
            model_name: Source LLM model name
            
        Returns:
            Dictionary with individual model scores
        """
        if not self.is_loaded:
            self.logger.warning("Models not loaded, loading now...")
            await self.load_models()
        
        scores = {}
        
        try:
            # Get predictions from all models
            tasks = [
                self._predict_with_timeout(model, text, features)
                for model in self.models.values()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for model, result in zip(self.models.values(), results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error in {model.model_name}: {str(result)}")
                    scores[model.model_name] = 0.0
                else:
                    scores[model.model_name] = result
            
            self.logger.info(f"Ensemble predictions: {scores}")
            return scores
            
        except Exception as e:
            self.logger.error(f"Error in ensemble prediction: {str(e)}")
            return {name: 0.0 for name in self.models.keys()}
    
    async def _predict_with_timeout(self, model: HallucinationModel, text: str, features: Dict[str, Any], timeout: int = 5) -> float:
        """
        Get prediction with timeout
        """
        try:
            return await asyncio.wait_for(model.predict(text, features), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout for model {model.model_name}")
            return 0.5  # Default neutral score on timeout
    
    def get_ensemble_info(self) -> Dict[str, Any]:
        """
        Get information about the ensemble
        """
        return {
            "ensemble_size": len(self.models),
            "is_loaded": self.is_loaded,
            "models": [model.get_info() for model in self.models.values()],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def aggregate_scores(
        self,
        scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Aggregate individual model scores
        
        Args:
            scores: Individual model scores
            weights: Optional weights for each model (default: equal)
            
        Returns:
            Aggregated score
        """
        if not scores:
            return 0.0
        
        if weights is None:
            # Equal weights
            return sum(scores.values()) / len(scores)
        
        # Weighted average
        total_weight = sum(weights.get(model, 1.0) for model in scores.keys())
        if total_weight == 0:
            return sum(scores.values()) / len(scores)
        
        weighted_sum = sum(
            score * weights.get(model, 1.0)
            for model, score in scores.items()
        )
        
        return weighted_sum / total_weight
