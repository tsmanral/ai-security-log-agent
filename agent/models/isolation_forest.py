import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List

try:
    from base_model import BaseAnomalyDetector
except ImportError:
    from agent.models.base_model import BaseAnomalyDetector

class IFDetector(BaseAnomalyDetector):
    """
    Isolation Forest anomaly detector.
    Well-suited for high-dimensional anomaly detection.
    """
    
    def __init__(self, contamination: float = 0.05):
        super().__init__("Isolation_Forest")
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        self.is_fitted = False

    def train(self, df: pd.DataFrame):
        """Train the Isolation Forest model on feature data."""
        X = df[self.features]
        self.model.fit(X)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Predict anomalies and generate scores for the input DataFrame."""
        if not self.is_fitted:
            raise ValueError(f"Model {self.name} must be trained before calling predict().")
            
        X = df[self.features]
        
        # predict returns 1 for inliers, -1 for outliers
        preds = self.model.predict(X)
        
        # score_samples returns opposite of anomaly score (lower is more anomalous)
        # sklearn scores are negative. We invert so higher means more anomalous.
        scores = -self.model.score_samples(X) 
        
        results = []
        for i in range(len(preds)):
            results.append({
                'is_anomaly': bool(preds[i] == -1),
                'anomaly_score': float(scores[i]),
                'model_name': self.name
            })
            
        return results
