from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List

class BaseAnomalyDetector(ABC):
    """
    Abstract base class for all anomaly detection models in the ensemble.
    """
    
    def __init__(self, name: str):
        """
        Initialize the detector.
        
        Args:
            name (str): Identifier for the model (e.g., 'Isolation_Forest_v1')
        """
        self.name = name
        self.model = None
        self.features = [
            'hour_sin', 'hour_cos', 'is_off_hours', 'is_weekend',
            'time_since_last_event_ip', 'unique_users_15m',
            'failures_15m', 'successes_15m', 'failure_ratio_15m'
        ]

    @abstractmethod
    def train(self, df: pd.DataFrame):
        """
        Train the model on historical feature data (assumed to be mostly normal).
        
        Args:
            df (pd.DataFrame): Training data containing feature columns.
        """
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Predict anomalies on new data.
        
        Args:
            df (pd.DataFrame): Data to predict on.
            
        Returns:
            List[Dict[str, Any]]: List of predictions where each element corresponds to a row in df.
                Required format:
                {
                    'is_anomaly': bool,
                    'anomaly_score': float, # Higher means more anomalous
                }
        """
        pass
