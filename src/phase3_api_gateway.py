# PHASE 3 - LLM Quality Guardian v1 Production Build
# FastAPI Gateway + Stage A-D Implementation

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import os
from datetime import datetime
import asyncio
import uuid

from phase3_quality_analyzer import HallucinationDetector
from phase3_datadog_monitor import DatadogMonitor
from phase3_ml_models import ModelEnsemble

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Quality Guardian",
    description="Real-time hallucination detection for LLMs with Datadog monitoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class TextInput(BaseModel):
    """Model for text input to analyze"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    model_name: Optional[str] = Field(default="gpt-4", description="Source LLM model")
    context: Optional[str] = Field(default=None, description="Optional context for analysis")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class HallucinationResult(BaseModel):
    """Model for hallucination detection result"""
    request_id: str
    is_hallucination: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    hallucination_type: Optional[str]
    explanation: str
    detected_issues: List[str]
    timestamp: str
    processing_time_ms: float
    model_scores: Dict[str, float]

class BatchRequest(BaseModel):
    """Model for batch processing requests"""
    texts: List[str]
    model_name: Optional[str] = "gpt-4"
    batch_id: Optional[str] = None

class HealthStatus(BaseModel):
    """Model for health check response"""
    status: str
    timestamp: str
    version: str
    components: Dict[str, str]

# ==================== Global Instances ====================

hallucinaton_detector = None
datadog_monitor = None
model_ensemble = None

# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global hallucinaton_detector, datadog_monitor, model_ensemble
    
    try:
        logger.info("Initializing LLM Quality Guardian components...")
        
        # Initialize Datadog monitoring
        datadog_monitor = DatadogMonitor(
            api_key=os.getenv("DATADOG_API_KEY"),
            app_key=os.getenv("DATADOG_APP_KEY")
        )
        
        # Initialize ML model ensemble
        model_ensemble = ModelEnsemble()
        await model_ensemble.load_models()
        
        # Initialize hallucination detector
        hallucinaton_detector = HallucinationDetector(
            model_ensemble=model_ensemble,
            datadog_monitor=datadog_monitor
        )
        
        logger.info("All components initialized successfully")
        datadog_monitor.log_event("app_startup", "LLM Quality Guardian started successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        datadog_monitor.log_error("startup_error", str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down LLM Quality Guardian...")
    if datadog_monitor:
        datadog_monitor.log_event("app_shutdown", "LLM Quality Guardian shutting down")

# ==================== Health & Status Endpoints ====================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        components={
            "detector": "ready" if hallucinaton_detector else "not_ready",
            "datadog": "ready" if datadog_monitor else "not_ready",
            "models": "ready" if model_ensemble else "not_ready"
        }
    )

@app.get("/status")
async def status():
    """Get system status"""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# ==================== Analysis Endpoints ====================

@app.post("/analyze", response_model=HallucinationResult)
async def analyze_text(request: TextInput, background_tasks: BackgroundTasks):
    """
    Analyze text for hallucinations
    
    STAGE A: Input Validation
    STAGE B: Feature Extraction
    STAGE C: Model Ensemble Prediction
    STAGE D: Result Synthesis
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        if not hallucinaton_detector:
            raise HTTPException(status_code=503, detail="Detector not initialized")
        
        logger.info(f"[{request_id}] Analyzing text: {request.model_name}")
        
        # Call detector with full pipeline (Stages A-D)
        result = await hallucinaton_detector.detect_hallucination(
            text=request.text,
            model_name=request.model_name,
            context=request.context,
            request_id=request_id
        )
        
        # Add processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        response = HallucinationResult(
            request_id=request_id,
            is_hallucination=result["is_hallucination"],
            confidence_score=result["confidence_score"],
            hallucination_type=result.get("hallucination_type"),
            explanation=result["explanation"],
            detected_issues=result.get("detected_issues", []),
            timestamp=datetime.utcnow().isoformat(),
            processing_time_ms=processing_time,
            model_scores=result.get("model_scores", {})
        )
        
        # Log to Datadog in background
        background_tasks.add_task(
            datadog_monitor.log_analysis,
            request_id=request_id,
            input_text=request.text,
            result=result,
            processing_time_ms=processing_time
        )
        
        logger.info(f"[{request_id}] Analysis complete: {result['is_hallucination']}")
        return response
        
    except Exception as e:
        logger.error(f"[{request_id}] Analysis error: {str(e)}")
        if datadog_monitor:
            background_tasks.add_task(datadog_monitor.log_error, "analysis_error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-analyze")
async def batch_analyze(request: BatchRequest, background_tasks: BackgroundTasks):
    """
    Batch analyze multiple texts
    """
    batch_id = request.batch_id or str(uuid.uuid4())
    
    try:
        logger.info(f"[{batch_id}] Processing batch with {len(request.texts)} texts")
        
        results = []
        for idx, text in enumerate(request.texts):
            text_input = TextInput(
                text=text,
                model_name=request.model_name
            )
            # Process each text (in production, use concurrent.futures for parallelization)
            result = await analyze_text(text_input, background_tasks)
            results.append(result)
        
        logger.info(f"[{batch_id}] Batch processing complete")
        return {
            "batch_id": batch_id,
            "total_texts": len(request.texts),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"[{batch_id}] Batch processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Configuration Endpoints ====================

@app.get("/config")
async def get_config():
    """
    Get current configuration
    """
    return {
        "max_text_length": 10000,
        "supported_models": ["gpt-4", "gpt-3.5-turbo", "claude-2", "palm-2"],
        "hallucination_types": [
            "factual_error",
            "logical_contradiction",
            "fabricated_citation",
            "out_of_context",
            "temporal_inconsistency"
        ],
        "confidence_threshold": 0.7
    }

# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ==================== Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
