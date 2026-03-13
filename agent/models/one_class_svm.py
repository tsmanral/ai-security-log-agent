import pandas as pd
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List

try:
    from base_model import BaseAnomalyDetector
except ImportError:
    from agent.models.base_model import BaseAnomalyDetector

class OCSVMDetector(BaseAnomalyDetector):
    """
    One-Class Support Vector Machine anomaly detector.
    Constructs a frontier representing the support of the normal dataset.
    Requires feature scaling.
    """
    
    def __init__(self, nu: float = 0.05, kernel: str = 'rbf'):
        super().__init__("One_Class_SVM")
        self.nu = nu # Approximation of contamination
        self.model = OneClassSVM(
            nu=self.nu,
            kernel=kernel,
            gamma='scale'
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

    def train(self, df: pd.DataFrame):
        """Train the OCSVM model on scaled feature data."""
        X = df[self.features]
        # OCSVM is highly sensitive to feature scaling
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Predict anomalies and generate scores for the input DataFrame."""
        if not self.is_fitted:
            raise ValueError(f"Model {self.name} must be trained before calling predict().")
            
        X = df[self.features]
        X_scaled = self.scaler.transform(X)
        
        # predict returns 1 for inliers, -1 for outliers
        preds = self.model.predict(X_scaled)
        
        # score_samples returns raw scoring function (signed distance to separating hyperplane)
        # Positive values are inliers, negative are outliers.
        # We invert so higher means more anomalous.
        scores = -self.model.score_samples(X_scaled) 
        
        results = []
        for i in range(len(preds)):
            results.append({
                'is_anomaly': bool(preds[i] == -1),
                'anomaly_score': float(scores[i]),
                'model_name': self.name
            })
            
        return results
