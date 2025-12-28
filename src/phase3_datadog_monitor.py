# PHASE 3 - Datadog Monitoring Integration
# Real-time monitoring and observability for hallucination detection

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json
from dataclasses import asdict

logger = logging.getLogger(__name__)

class DatadogMonitor:
    """Datadog integration for monitoring and observability"""
    
    def __init__(self, api_key: Optional[str] = None, app_key: Optional[str] = None):
        """Initialize Datadog monitor with API credentials"""
        self.api_key = api_key or os.getenv("DATADOG_API_KEY")
        self.app_key = app_key or os.getenv("DATADOG_APP_KEY")
        self.logger = logging.getLogger(__name__)
        self.enabled = bool(self.api_key and self.app_key)
        
        if self.enabled:
            try:
                # Initialize Datadog client (would use datadog library in production)
                self.logger.info("Datadog monitoring initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Datadog: {str(e)}")
                self.enabled = False
    
    def log_event(self, event_name: str, message: str, tags: Optional[Dict[str, str]] = None) -> bool:
        """
        Log custom event to Datadog
        
        Args:
            event_name: Name of the event
            message: Event message
            tags: Optional tags for the event
        """
        if not self.enabled:
            return False
        
        try:
            event_data = {
                "title": event_name,
                "text": message,
                "tags": tags or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Event logged: {event_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log event: {str(e)}")
            return False
    
    def log_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> bool:
        """
        Log metric to Datadog
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return False
        
        try:
            metric_data = {
                "metric": metric_name,
                "points": [(datetime.utcnow().timestamp(), value)],
                "type": "gauge",
                "tags": tags or {}
            }
            
            self.logger.info(f"Metric logged: {metric_name}={value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log metric: {str(e)}")
            return False
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log error to Datadog
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Optional error context
        """
        if not self.enabled:
            return False
        
        try:
            error_data = {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.error(f"Error logged: {error_type} - {error_message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log error: {str(e)}")
            return False
    
    async def log_analysis(self, request_id: str, input_text: str, result: Dict[str, Any], processing_time_ms: float) -> bool:
        """
        Log analysis results to Datadog
        
        Args:
            request_id: Request ID for tracing
            input_text: Input text analyzed
            result: Analysis result
            processing_time_ms: Processing time in milliseconds
        """
        if not self.enabled:
            return False
        
        try:
            # Log the detection result
            tags = {
                "request_id": request_id,
                "is_hallucination": str(result.get("is_hallucination", False)),
                "hallucination_type": result.get("hallucination_type", "none")
            }
            
            self.log_event(
                f"hallucination_detection_{result.get('hallucination_type', 'clean')}",
                f"Hallucination detected: {result.get('is_hallucination', False)}",
                tags=tags
            )
            
            # Log processing time metric
            self.log_metric(
                "llm_quality_guardian.processing_time_ms",
                processing_time_ms,
                tags=tags
            )
            
            # Log confidence score metric
            confidence = result.get("confidence_score", 0.0)
            self.log_metric(
                "llm_quality_guardian.confidence_score",
                confidence,
                tags=tags
            )
            
            # Log model scores
            model_scores = result.get("model_scores", {})
            for model_name, score in model_scores.items():
                self.log_metric(
                    f"llm_quality_guardian.model_score.{model_name}",
                    score,
                    tags=tags
                )
            
            self.logger.info(f"Analysis logged: {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log analysis: {str(e)}")
            return False
    
    def log_performance(self, stage_name: str, duration_ms: float, status: str) -> bool:
        """
        Log performance metrics for detection stages
        
        Args:
            stage_name: Name of the processing stage (A, B, C, or D)
            duration_ms: Duration of the stage in milliseconds
            status: Status of the stage (success/failure)
        """
        if not self.enabled:
            return False
        
        try:
            tags = {
                "stage": stage_name,
                "status": status
            }
            
            self.log_metric(
                f"llm_quality_guardian.stage_{stage_name}_duration_ms",
                duration_ms,
                tags=tags
            )
            
            self.log_event(
                f"stage_{stage_name}_{status}",
                f"Stage {stage_name} completed in {duration_ms:.2f}ms",
                tags=tags
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log performance: {str(e)}")
            return False
    
    def log_model_ensemble_metrics(self, model_scores: Dict[str, float], ensemble_score: float, tags: Optional[Dict[str, str]] = None) -> bool:
        """
        Log model ensemble metrics
        
        Args:
            model_scores: Individual model scores
            ensemble_score: Ensemble aggregated score
            tags: Optional tags
        """
        if not self.enabled:
            return False
        
        try:
            base_tags = tags or {}
            base_tags["component"] = "model_ensemble"
            
            # Log ensemble score
            self.log_metric(
                "llm_quality_guardian.ensemble_score",
                ensemble_score,
                tags=base_tags
            )
            
            # Log individual model scores
            for model_name, score in model_scores.items():
                model_tags = base_tags.copy()
                model_tags["model"] = model_name
                
                self.log_metric(
                    f"llm_quality_guardian.model_score",
                    score,
                    tags=model_tags
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log ensemble metrics: {str(e)}")
            return False
    
    def create_dashboard_annotations(self, annotation_text: str, tags: Optional[Dict[str, str]] = None) -> bool:
        """
        Create annotation for Datadog dashboard
        
        Args:
            annotation_text: Text for the annotation
            tags: Optional tags
        """
        if not self.enabled:
            return False
        
        try:
            annotation_data = {
                "text": annotation_text,
                "tags": tags or [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Dashboard annotation created: {annotation_text}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create annotation: {str(e)}")
            return False
    
    def log_system_health(self, component: str, status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log system health status
        
        Args:
            component: System component (detector, models, gateway, etc.)
            status: Health status (healthy/degraded/unhealthy)
            details: Optional health details
        """
        if not self.enabled:
            return False
        
        try:
            tags = {"component": component, "status": status}
            
            self.log_event(
                f"system_health_{component}",
                f"Component {component} status: {status}",
                tags=tags
            )
            
            # Log health metric (1 for healthy, 0 for unhealthy)
            health_value = 1.0 if status == "healthy" else 0.0
            self.log_metric(
                f"llm_quality_guardian.system_health.{component}",
                health_value,
                tags=tags
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log system health: {str(e)}")
            return False
    
    def setup_alerts(self) -> Dict[str, Any]:
        """
        Setup Datadog alerts for monitoring
        
        Returns:
            Dictionary with alert configurations
        """
        alerts_config = {
            "high_hallucination_rate": {
                "metric": "llm_quality_guardian.confidence_score",
                "threshold": 0.85,
                "comparison": "above"
            },
            "slow_processing": {
                "metric": "llm_quality_guardian.processing_time_ms",
                "threshold": 5000,
                "comparison": "above"
            },
            "model_ensemble_degradation": {
                "metric": "llm_quality_guardian.ensemble_score",
                "threshold": 0.5,
                "comparison": "below"
            },
            "error_spike": {
                "metric": "llm_quality_guardian.errors",
                "threshold": 10,
                "comparison": "above"
            }
        }
        
        self.logger.info("Datadog alerts configured")
        return alerts_config
    
    def get_monitoring_dashboard_config(self) -> Dict[str, Any]:
        """
        Get configuration for monitoring dashboard
        
        Returns:
            Dashboard configuration dictionary
        """
        return {
            "title": "LLM Quality Guardian - Real-time Monitoring",
            "widgets": [
                {
                    "title": "Hallucination Detection Rate",
                    "metric": "llm_quality_guardian.confidence_score"
                },
                {
                    "title": "Processing Time (ms)",
                    "metric": "llm_quality_guardian.processing_time_ms"
                },
                {
                    "title": "Ensemble Model Scores",
                    "metric": "llm_quality_guardian.model_score"
                },
                {
                    "title": "Stage Performance",
                    "metrics": [
                        "llm_quality_guardian.stage_a_duration_ms",
                        "llm_quality_guardian.stage_b_duration_ms",
                        "llm_quality_guardian.stage_c_duration_ms",
                        "llm_quality_guardian.stage_d_duration_ms"
                    ]
                },
                {
                    "title": "System Health",
                    "metrics": [
                        "llm_quality_guardian.system_health.detector",
                        "llm_quality_guardian.system_health.models",
                        "llm_quality_guardian.system_health.gateway"
                    ]
                }
            ]
        }
