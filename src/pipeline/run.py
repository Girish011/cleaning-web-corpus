#!/usr/bin/env python3
"""
Entry point for the unified pipeline orchestrator.

Usage:
    python -m src.pipeline.run [--stages STAGE1,STAGE2,...] [--config PATH]

Examples:
    # Run complete pipeline
    python -m src.pipeline.run
    
    # Run only crawl and process
    python -m src.pipeline.run --stages crawl,process
    
    # Run with custom config
    python -m src.pipeline.run --config configs/custom.yaml
"""

import argparse
import pathlib
import sys

# Add project root to path
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.pipeline.orchestrator import PipelineOrchestrator


def main():
    """Main entry point for pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="Unified pipeline orchestrator for cleaning corpus pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python -m src.pipeline.run
  
  # Run only crawl and process stages
  python -m src.pipeline.run --stages crawl,process
  
  # Run with custom config
  python -m src.pipeline.run --config configs/custom.yaml
  
  # Run discovery only
  python -m src.pipeline.run --stages discover
        """,
    )

    parser.add_argument(
        "--stages",
        type=str,
        default=None,
        help="Comma-separated list of stages to run (discover,crawl,process,evaluate). "
             "If not specified, runs all stages.",
    )

    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=None,
        help="Path to config file (default: configs/default.yaml)",
    )

    args = parser.parse_args()

    # Parse stages
    stages = None
    if args.stages:
        stages = [s.strip() for s in args.stages.split(",")]
        valid_stages = {"discover", "crawl", "process", "evaluate"}
        invalid = set(stages) - valid_stages
        if invalid:
            print(f"Error: Invalid stages: {', '.join(invalid)}")
            print(f"Valid stages: {', '.join(sorted(valid_stages))}")
            return 1

    # Initialize orchestrator
    try:
        orchestrator = PipelineOrchestrator(config_path=args.config)
    except Exception as e:
        print(f"Error initializing orchestrator: {e}")
        return 1

    # Run pipeline
    try:
        success = orchestrator.run(stages=stages)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

