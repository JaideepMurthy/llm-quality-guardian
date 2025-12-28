#!/usr/bin/env python3
"""
PHASE 3 - LLM Quality Guardian Main Application
Entry point for the production build with all components integrated
"""

import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try to load from .env.example if .env doesn't exist
    example_path = Path(__file__).parent.parent / ".env.example"
    if example_path.exists():
        load_dotenv(example_path)

# Configure logging
logging.basicConfig(
    level=logging.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import FastAPI components
from phase3_api_gateway import app as fastapi_app
from phase3_ml_models import ModelEnsemble
from phase3_datadog_monitor import DatadogMonitor
from phase3_quality_analyzer import HallucinationDetector


def initialize_application():
    """
    Initialize the complete application with all components
    """
    logger.info("Initializing LLM Quality Guardian v1.0.0")
    
    try:
        # Check required environment variables
        required_vars = ["DATADOG_API_KEY", "DATADOG_APP_KEY", "GOOGLE_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("Using default/mock configurations")
        
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        return False


def get_app():
    """
    Get the FastAPI application instance
    """
    if not initialize_application():
        logger.warning("Application initialized with warnings")
    
    return fastapi_app


def main():
    """
    Main entry point for running the application
    """
    import uvicorn
    
    logger.info("Starting LLM Quality Guardian...")
    
    # Get configuration from environment
    host = os.getenv("FAST_API_HOST", "0.0.0.0")
    port = int(os.getenv("FAST_API_PORT", "8000"))
    reload = os.getenv("FAST_API_RELOAD", "false").lower() == "true"
    workers = int(os.getenv("FAST_API_WORKERS", "4"))
    
    logger.info(f"Server will run on http://{host}:{port}")
    logger.info(f"Reload: {reload}, Workers: {workers}")
    
    try:
        if reload:
            # Development mode with auto-reload
            uvicorn.run(
                "main:get_app",
                host=host,
                port=port,
                reload=True,
                log_level="info"
            )
        else:
            # Production mode with multiple workers
            uvicorn.run(
                "main:get_app",
                host=host,
                port=port,
                workers=workers,
                log_level="info"
            )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
