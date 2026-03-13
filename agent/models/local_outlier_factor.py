import pandas as pd
from sklearn.neighbors import LocalOutlierFactor
from typing import Dict, Any, List

try:
    from base_model import BaseAnomalyDetector
except ImportError:
    from agent.models.base_model import BaseAnomalyDetector

class LOFDetector(BaseAnomalyDetector):
    """
    Local Outlier Factor anomaly detector.
    Finds anomalous data points by measuring local deviation of a given data 
    point with respect to its neighbors.
    """
    
    def __init__(self, contamination: float = 0.05, n_neighbors: int = 20):
        super().__init__("Local_Outlier_Factor")
        self.contamination = contamination
        # novelty=True must be set to allow predict() on new data after fit()
        self.model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=self.contamination,
            novelty=True,
            n_jobs=-1
        )
        self.is_fitted = False

    def train(self, df: pd.DataFrame):
        """Train the LOF model on feature data."""
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
        
        # score_samples returns opposite of local outlier factor (lower is more anomalous)
        # We invert so higher means more anomalous.
        scores = -self.model.score_samples(X) 
        
        results = []
        for i in range(len(preds)):
            results.append({
                'is_anomaly': bool(preds[i] == -1),
                'anomaly_score': float(scores[i]),
                'model_name': self.name
            })
            
        return results
