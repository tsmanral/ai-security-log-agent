import argparse
import logging
import os
import subprocess
import time
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
AGENT_DIR = PROJECT_ROOT / "agent"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_step(script_path: Path, description: str):
    """Utility to run a python script as a subprocess."""
    logger.info(f"==== Starting: {description} ====")
    if not script_path.exists():
        logger.error(f"Cannot find script: {script_path}")
        return False
        
    try:
        subprocess.run(["python", str(script_path)], check=True)
        logger.info(f"==== Completed: {description} ====\n")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step failed with error code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="AI-Sentinel: Open-Source Extract-Detect-Explain SIEM")
    parser.add_argument("--pipeline", action="store_true", help="Run the full pipeline (Generate -> Collect -> Evaluate)")
    parser.add_argument("--dashboard", action="store_true", help="Launch the Streamlit dashboard")
    args = parser.parse_args()
    
    if args.pipeline:
        # 1. Generate local synthetic data
        run_step(DATASETS_DIR / "generate_ssh_logs.py", "Generating Synthetic SSH Logs")
        
        # 2. Database Init is handled by scripts, but we need to ingest historical logs
        # We can run the collector script as a module, or just run evaluation since evaluation will trigger everything if data exists
        logger.info("Initializing DB and generating features dynamically...")
        from agent.database import init_db
        init_db()
        
        # Run log collector ingestion
        logger.info("Ingesting generated logs into the database...")
        from agent.log_collector import collect_historical_logs
        log_file = PROJECT_ROOT / "logs" / "generated_auth.log"
        collect_historical_logs(log_file)
        logger.info("Log Ingestion Complete.\n")
        
        # 3. Predict & Alert
        run_step(EVALUATION_DIR / "evaluate_models.py", "Evaluating Models & Generating Explainable Alerts")
    
    if args.dashboard:
        logger.info("Starting Streamlit Dashboard...")
        dash_path = DASHBOARD_DIR / "dashboard.py"
        try:
            subprocess.run(["streamlit", "run", str(dash_path)])
        except KeyboardInterrupt:
            logger.info("Dashboard stopped.")
            
    if not args.pipeline and not args.dashboard:
        parser.print_help()

if __name__ == "__main__":
    main()
