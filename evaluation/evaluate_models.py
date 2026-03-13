import os
import sys
import pandas as pd
import numpy as np
import logging
from typing import Tuple

# Add project root to sys.path to allow imports when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.database import get_all_logs, init_db
from agent.features.feature_extractor import build_features
from agent.models.ensemble_detector import EnsembleDetector
from agent.alert_manager import AlertManager

logger = logging.getLogger(__name__)

def prepare_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch all logs from database, build features, and split into train/test.
    In a real SIEM, training data would be known good baseline.
    Here we use the first 70% of chronological data as training (mostly normal).
    """
    raw_logs = get_all_logs()
    if not raw_logs:
        logger.error("No logs found in DB. Run collector first.")
        return pd.DataFrame(), pd.DataFrame()
        
    logger.info(f"Loaded {len(raw_logs)} logs from database. Building features...")
    df_features = build_features(raw_logs)
    
    # Sort chronologically just in case
    df_features = df_features.sort_values('timestamp')
    
    # Split 70/30
    split_idx = int(len(df_features) * 0.70)
    df_train = df_features.iloc[:split_idx].copy()
    df_test = df_features.iloc[split_idx:].copy()
    
    logger.info(f"Train samples: {len(df_train)}, Test samples: {len(df_test)}")
    return df_train, df_test

def run_evaluation_pipeline():
    """
    Main evaluation script to train the ensemble, predict on test, 
    and create alerts using the AlertManager.
    """
    df_train, df_test = prepare_data()
    if df_train.empty:
        return
        
    logger.info("Initializing Ensemble Detector...")
    ensemble = EnsembleDetector()
    
    logger.info("Training models on historical baseline...")
    ensemble.train(df_train)
    
    logger.info("Predicting on test data...")
    predictions = ensemble.predict(df_test)
    
    # Calculate basic detection stats
    anomalies = [p for p in predictions if p['is_anomaly']]
    logger.info(f"Detected {len(anomalies)} anomalies out of {len(df_test)} test samples ({(len(anomalies)/len(df_test))*100:.2f}%).")
    
    # Initialize AlertManager using background data (e.g., sample of train data)
    background_data = df_train[ensemble.models[0].features].sample(min(100, len(df_train)), random_state=42)
    alert_mgr = AlertManager(ensemble, background_data)
    
    logger.info("Processing predictions for explainability and alerting...")
    alert_mgr.process_predictions(df_test, predictions)
    
    logger.info("Evaluation Pipeline Complete. Results stored in 'anomalies' table.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Ensure DB is initialized before running
    init_db()
    run_evaluation_pipeline()
