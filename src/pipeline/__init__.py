"""
Unified pipeline orchestrator for the cleaning corpus pipeline.

This package provides a single entry point to run the complete pipeline:
Discovery → Crawl → Process → Enrich → Evaluate
"""

from src.pipeline.orchestrator import PipelineOrchestrator

__all__ = ["PipelineOrchestrator"]

